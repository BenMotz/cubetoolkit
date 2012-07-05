import os
import os.path

from fabric.api import require, env, run, cd, local, put, sudo
from fabric import utils
from fabric.contrib import console

VIRTUALENV = "venv"
REQUIREMENTS = "requirements.txt"

# This is deleted whenever code is deployed
CODE_DIR = "toolkit"

def testing():
    """Configure to deploy locally"""
    env.target = "testing"
    env.site_root = "/var/www_toolkit/site"
    env.user = "ben"
    env.hosts = ["localhost"]
    env.git_source = "ben@phonog.dyndns.org:data/python/cube"
    env.settings = "testing_settings.py"

def production():
    """Configure to deploy live"""
    env.target = "production"
    env.site_root = "/home/users/cubetoolkit/site"
    env.user = "cubetoolkit"
    env.hosts = ["toolkit.cubecinema.com"]
    env.settings = "live_settings.py"

def deploy_code():
    """Deploy code from git HEAD onto target"""
    # Check that target is defined:
    require('site_root', provided_by = ('testing', 'production'))

    archive = "site_transfer.tgz"
    local("git archive --format=tgz HEAD > {0}".format(archive))
    # local('tar -czf {0} . --exclude=media --exclude=venv --exclude={0} --exclude=".pyc"'.format(archive))
    put(archive, env.site_root)
    with cd(env.site_root):
        target = os.path.join(env.site_root, CODE_DIR)
        run("rm -rf {0}".format(target))
        run("tar -xzf {0}".format(archive))
        run("rm -f toolkit/settings.py")
        run("ln -s {0} toolkit/settings.py".format(env.settings))

def deploy_static():
    """Rsync all static content onto target"""
    # Check that target is defined:
    require('site_root', provided_by = ('testing', 'production'))

    # This isn't so much to put content there, but to delete anything that
    # isn't needed or shouldn't be there.
    local('rsync -av --delete static/ {0}@{1}:{2}/static'.format(env.user, env.hosts[0], env.site_root))

def deploy_media():
    """Rsync all media content onto target"""
    # Check that target is defined:
    require('site_root', provided_by = ('testing', 'production'))

    local('rsync -av --delete media/ {0}@{1}:{2}/media'.format(env.user, env.hosts[0], env.site_root))

def update_requirements():
    """ Update installed packages in remote virtualenv """
    # Update the packages installed in the environment:
    venv_path = os.path.join(env.site_root, VIRTUALENV)
    req_file = os.path.join(env.site_root, REQUIREMENTS)
#    with cd(env.site_root):
#        run("{venv_path}/bin/pip install --requirement {req_file}".format(venv_path=venv_path, req_file=req_file))

def restart_server():
    # ??
    sudo("apache2ctl restart")

## Disabled, for destruction avoidance
def bootstrap():
    """Wipe out what has gone before, build virtual environment, uppload code"""
    if not console.confirm("Flatten remote, including media files?", default=False):
        utils.abort("User aborted")
    # Check that target is defined:
    require('site_root', provided_by = ('testing', 'production'))
    # Scorch the earth
    run("rm -rf %(site_root)s" % env)
    # Recreate the directory
    run("mkdir %(site_root)s" % env)
    deploy_code()
    deploy_static()
    deploy_media()
    # Create the virtualenv:
    venv_path = os.path.join(env.site_root, VIRTUALENV)
    run("virtualenv --system-site-packages {0}".format(venv_path))
    # Update the packages installed in the environment:
    update_requirements()

def deploy():
    """Upload code, install any new requirements"""
    # Check that target is defined:
    require('site_root', provided_by = ('testing', 'production'))
    if env.target == 'production':
        if not console.confirm("Uploading to live site: sure?", default=False):
            utils.abort("User aborted")

    deploy_code()
    deploy_static()
    update_requirements()
#    restart_server()


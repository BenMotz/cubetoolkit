import os
import os.path

from fabric.api import require, env, run, cd, local, put
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

def production():
    """Configure to deploy live"""
    env.target = "production"
    env.site_root = "/home/users/toolkit/site"
    env.user = "cubetoolkit"
    env.hosts = ["toolkit.cubecinema.com"]

def deploy_code():
    # Check that target is defined:
    require('site_root', provided_by = ('testing', 'production'))

    archive = "site_transfer.tgz"
    local("git archive --format=tgz HEAD > {0}".format(archive))
    put(archive, env.site_root)
    with cd(env.site_root):
        target = os.path.join(env.site_root, CODE_DIR)
        run("rm -rf {0}".format(target))
        run("tar -xzf {0}".format(archive))

def update_requirements():
    """ Update installed packages in remote virtualenv """
    # Update the packages installed in the environment:
    venv_path = os.path.join(env.site_root, VIRTUALENV)
    req_file = os.path.join(env.site_root, REQUIREMENTS)
    with cd(env.site_root):
        run("pip install -E {venv_path} --requirement {req_file}".format(venv_path=venv_path, req_file=req_file))

def restart_server():
    # ??
    pass

## Disabled, for destruction avoidance
#def bootstrap():
#    """Wipe out what has gone before, build virtual environment, uppload code"""
#    # Check that target is defined:
#    require('site_root', provided_by = ('testing', 'production'))
#    # Scorch the earth
#    run("rm -rf %(site_root)s" % env)
#    deploy_code()
#    # Create the virtualenv:
#    venv_path = os.path.join(env.site_root, VIRTUALENV)
#    run("virtualenv --system-site-packages {0}".format(venv_path))
#    # Update the packages installed in the environment:
#    update_requirements()

def deploy():
    """Upload code, install any new requirements"""
    # Check that target is defined:
    require('site_root', provided_by = ('testing', 'production'))
    if env.target == 'production':
        if not console.confirm("Uploading to live site: sure?", default=False):
            utils.abort()

    deploy_code()
    update_requirements()


import os
import os.path

from fabric.api import require, env, run, cd, local, put, sudo, lcd
from fabric import utils
from fabric.contrib import console

VIRTUALENV = "venv"
REQUIREMENTS_PYTHON_ONLY = "requirements_python_only.txt"
REQUIREMENTS_C_COMPONENT = "requirements_c_components.txt"

# This is deleted whenever code is deployed
CODE_DIR = "toolkit"


def staging():
    """Configure to deploy to staging server"""
    env.target = "staging"
    env.site_root = "/var/www_toolkit/site"
    env.user = "ben"
    env.hosts = ["localhost"]
    env.settings = "staging_settings.py"


def production():
    """Configure to deploy live"""
    env.target = "production"
    env.site_root = "/home/toolkit/site"
    env.user = "toolkit"
    env.hosts = ["sparror.cubecinema.com"]
    env.settings = "live_settings.py"


def deploy_code():
    """Deploy code from git HEAD onto target"""

    # Check that target is defined:
    require('site_root', provided_by=('staging', 'production'))

    # Create tar of (local) git HEAD:
    archive = "site_transfer.tgz"
    local_root = os.path.dirname(__file__)
    utils.puts("Changing to {0}".format(local_root))
    with lcd(local_root):
        # (we need to be in the site root to create the tgz correctly)
        utils.puts("Creating site tgz")
        local("git archive --format=tgz HEAD > {0}".format(archive))

        # Upload to remote:
        utils.puts("Uploading to remote")
        put(archive, env.site_root)

        # On remote system. (Note that because of odd things about fabric's
        # environment vars the local pwd affects the remote commands. Yes.)
        with cd(env.site_root):
            # Extract:
            target = os.path.join(env.site_root, CODE_DIR)
            utils.puts("Deleting {0}".format(target))
            run("rm -rf {0}".format(target))
            utils.puts("Extracting {0}".format(archive))
            run("tar -xzf {0}".format(archive))

            # Configure the correct settings file.
            run("rm -f toolkit/settings.py?")
            run("ln -s {0} toolkit/settings.py".format(env.settings))


def deploy_static():
    """Run collectstatic command"""
    # Check that target is defined:
    require('site_root', provided_by=('staging', 'production'))

    with cd(env.site_root):
        utils.puts("Running collectstatic (pwd is '{0}')".format(run("pwd")))
        static_path = os.path.join(env.site_root, "static")
        run("rm -rf {0}".format(static_path))
        run("venv/bin/python manage.py collectstatic --noinput --settings=toolkit.import_settings")


def deploy_media():
    """Rsync all media content onto target"""
    # Check that target is defined:
    require('site_root', provided_by=('staging', 'production'))

    local('rsync -av --delete media/ {0}@{1}:{2}/media'.format(env.user, env.hosts[0], env.site_root))


def run_migrations():
    """Run south to make sure database schema is in sync with the application"""
    require('site_root', provided_by=('staging', 'production'))

    with cd(env.site_root):
        utils.puts("Running database migrations")
        run("venv/bin/python manage.py migrate --noinput --settings=toolkit.import_settings")


def install_requirements(upgrade=False):
    """ Install requirements in remote virtualenv """
    # Update the packages installed in the environment:
    venv_path = os.path.join(env.site_root, VIRTUALENV)
    req_file = os.path.join(env.site_root, REQUIREMENTS_PYTHON_ONLY)
    upgrade_flag = "--upgrade" if upgrade else ""
    with cd(env.site_root):
        run("{venv_path}/bin/pip install {upgrade} --requirement {req_file}".format(
            venv_path=venv_path, upgrade=upgrade_flag, req_file=req_file))


def upgrade_requirements():
    """ Upgrade all requirements in remote virtualenv """
    return install_requirements(True)


# Disabled, for destruction avoidance
def bootstrap():
    """Wipe out what has gone before, build virtual environment, uppload code"""
    if not console.confirm("Flatten remote, including media files?", default=False):
        utils.abort("User aborted")
    # Check that target is defined:
    require('site_root', provided_by=('staging', 'production'))
    # Scorch the earth
    run("rm -rf %(site_root)s" % env)
    # Recreate the directory
    run("mkdir %(site_root)s" % env)
    # Create the virtualenv:
    venv_path = os.path.join(env.site_root, VIRTUALENV)
    # Virtualenv changed their interface at v1.7: (idiots)
    virtualenv_version = run("virtualenv --version").split(".")
    if virtualenv_version[0] == "1" and int(virtualenv_version[1]) < 7:
        run("virtualenv {0}".format(venv_path))
    else:
        run("virtualenv --system-site-packages {0}".format(venv_path))

    # Now run deployment, as normal
    deploy()


def deploy():
    """Upload code, install any new requirements"""
    # Check that target is defined:
    require('site_root', provided_by=('staging', 'production'))
    if env.target == 'production':
        if not console.confirm("Uploading to live site: sure?", default=False):
            utils.abort("User aborted")

    deploy_code()
    install_requirements()

    deploy_static()
    run_migrations()

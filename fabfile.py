import os
import os.path

from fabric.api import require, env, run, cd, local, put, lcd, get, prompt
from fabric import utils
from fabric.contrib import console

VIRTUALENV = "venv"
REQUIREMENTS_FILE = "requirements/base.txt"

# This is deleted whenever code is deployed
CODE_DIRS = ["toolkit", "easy_thumbnails"]


def _assert_target_set():
    # utility method to check that target is defined:
    require(
        "site_root",
        provided_by=(
            "cube_staging",
            "cube_production",
            "star_and_shadow_production",
        ),
    )


def cube_staging():
    """Configure to deploy to staging on cubecinema.com"""
    env.target = "staging"
    env.site_root = "/home/staging/site"
    env.media = "/home/staging/site/media/"
    env.user = "staging"
    env.hosts = ["cubecinema.com"]
    env.settings = "staging_settings.py"
    # For running manage.py commands use this settings file; this is mostly
    # so that a different logfile can be set, as the deploy user may not have
    # permission to access the normal log file
    env.deploy_script_settings = "toolkit.deploy_settings"


def cube_production():
    """Configure to deploy live on cubecinema.com"""
    env.target = "production"
    env.site_root = "/home/toolkit/site"
    env.media = "/home/toolkit/site/media/"
    env.user = "toolkit"
    env.hosts = ["cubecinema.com"]
    env.settings = "live_settings.py"
    # See note above:
    env.deploy_script_settings = "toolkit.deploy_settings"


def star_and_shadow_production():
    """Configure to deploy star and shadow live on xtreamlab.net"""
    env.target = "production"
    env.site_root = "/home/users/starandshadow/star_site"
    env.user = "starandshadow"
    env.hosts = ["xtreamlab.net"]
    env.settings = "production_settings.py"
    # See note above:
    env.deploy_script_settings = "toolkit.deploy_settings"


def star_and_shadow_staging():
    """Configure to deploy star and shadow staging on xtreamlab.net"""
    env.target = "staging"
    env.site_root = "/home/users/starandshadow/staging"
    env.media = "/home/users/starandshadow/staging/media"
    env.user = "starandshadow"
    env.hosts = ["xtreamlab.net"]
    env.settings = "staging_settings.py"
    # See note above:
    env.deploy_script_settings = "toolkit.deploy_settings"
    env.dev_db_name = "starshadow_staging"


def deploy_code():
    """Deploy code from git HEAD onto target"""

    _assert_target_set()

    # Create tar of (local) git HEAD using the hash as the filename
    archive = "%s.tgz" % local("git rev-parse HEAD", capture=True)
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
            # Delete old code
            for code_dir in CODE_DIRS:
                target = os.path.join(env.site_root, code_dir)
                utils.puts("Deleting {0}".format(target))
                run("rm -rf {0}".format(target))
            # Extract:
            utils.puts("Extracting {0}".format(archive))
            # Untar with -m to avoid trying to utime /media directories that
            # may be owned by the webserver (which then fails)
            run("tar -m -xzf {0}".format(archive))

            # Configure the correct settings file.
            run("rm -f toolkit/settings.py?")
            run(
                "ln -s {0} toolkit/settings.py".format(
                    os.path.join(env.site_root, env.settings)
                )
            )


def deploy_static():
    """Run collectstatic command"""

    _assert_target_set()

    with cd(env.site_root):
        utils.puts("Running collectstatic (pwd is '{0}')".format(run("pwd")))
        static_path = os.path.join(env.site_root, "static")
        run("rm -rf {0}".format(static_path))
        run(
            "venv/bin/python manage.py collectstatic --noinput --settings={0}".format(
                env.deploy_script_settings
            )
        )


def set_media_permissions():
    """Set media directories to g+w"""
    media_dirs = [
        "media/diary",
        "media/printedprogramme",
        "media/volunteers",
        "media/images",
        "media/original_images",
        "media/documents",
    ]

    with cd(env.site_root):
        for media_dir in media_dirs:
            path = os.path.join(env.site_root, media_dir)
            run("chmod g+w {0}".format(path))


def deploy_media():
    """Rsync all media content onto target"""

    _assert_target_set()

    local(
        "rsync -av --delete media/ {0}@{1}:{2}/media".format(
            env.user, env.hosts[0], env.site_root
        )
    )


def get_media():
    """Rsync media content from a production server to your development environment"""

    _assert_target_set()

    local(
        "rsync -av --delete --exclude=thumbnails {0}@{1}:{2}/ media/".format(
            env.user, env.hosts[0], env.media
        )
    )


def sync_media_from_production_to_staging():
    """Rsync media content from the production server to the staging server. Invoke as fab cube_staging sync_media_from_production_to_staging"""

    # TODO define explicitly
    _assert_target_set()

    with cd(env.site_root):
        run(
            "rsync -av --delete --exclude=thumbnails /home/toolkit/site/media/ {0}".format(
                env.media
            )
        )


def run_migrations():
    """Run migrations to make sure database schema is in sync with the application"""

    _assert_target_set()

    with cd(env.site_root):
        utils.puts("Running database migrations")
        run(
            "venv/bin/python manage.py migrate --noinput --settings={0}".format(
                env.deploy_script_settings
            )
        )


def install_requirements(upgrade=False):
    """Install requirements in remote virtualenv"""
    # Update the packages installed in the environment:
    venv_path = os.path.join(env.site_root, VIRTUALENV)
    req_file = os.path.join(env.site_root, REQUIREMENTS_FILE)
    upgrade_flag = "--upgrade" if upgrade else ""
    with cd(env.site_root):
        run(
            "{venv_path}/bin/pip install {upgrade} --requirement {req_file}".format(
                venv_path=venv_path, upgrade=upgrade_flag, req_file=req_file
            )
        )


def upgrade_requirements():
    """Upgrade all requirements in remote virtualenv"""
    return install_requirements(True)


# Disabled, for destruction avoidance
def bootstrap():
    """Wipe out what has gone before, build virtual environment, upload code"""

    _assert_target_set()

    if not console.confirm(
        "Flatten remote, including media files?", default=False
    ):
        utils.abort("User aborted")

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
        run(
            "virtualenv --system-site-packages --python=python3 {0}".format(
                venv_path
            )
        )

    utils.puts(
        "\nRemote site is prepared. Now copy the settings file to '{0}/{1}'"
        " and run the 'deploy' command from this fabric file.".format(
            env.site_root, env.settings
        )
    )


def _fetch_database_dump(dump_filename):
    if os.path.exists(dump_filename):
        utils.abort("Local file {0} already exists".format(dump_filename))

    utils.puts("Generating remote database dump")
    with cd(env.site_root):
        dump_file_path = os.path.join(env.site_root, dump_filename)

        run(
            "venv/bin/python manage.py mysqldump_database {dump_file_path} "
            "--settings={deploy_script_settings}".format(
                dump_file_path=dump_file_path,
                deploy_script_settings=env.deploy_script_settings,
            )
        )
        run(
            "gzip {dump_file_path} -c > {dump_file_path}.gz".format(
                dump_file_path=dump_file_path
            )
        )
        get(dump_file_path + ".gz", local_path=dump_filename + ".gz")
        run("rm {0} {0}.gz".format(dump_file_path))

        local("gunzip {0}.gz".format(dump_filename))


def _load_database_dump(dump_filename):
    if not os.path.isfile(dump_filename):
        utils.abort("Couldn't find {0}".format(dump_filename))

    db_username = prompt(
        "Please enter local database username "
        "(must have permission to drop and create database!)",
        default="root",
    )

    if not console.confirm(
        "About to do something irreversible to the 'toolkit'"
        "database on your local system. Sure? ",
        default=False,
    ):
        utils.abort("User aborted")
        local("rm {0}".format(dump_filename))

    local(
        "mysql -u{db_username} -p toolkit < {dump_filename}".format(
            db_username=db_username, dump_filename=dump_filename
        )
    )


def sync_to_local_database():
    """Retrieve the remote database and load it into the local database"""

    _assert_target_set()

    dump_filename = "database_dump.sql"
    _fetch_database_dump(dump_filename)
    _load_database_dump(dump_filename)

    local("rm {0}".format(dump_filename))


def deploy():
    """Upload code, install any new requirements"""

    _assert_target_set()

    if env.target == "production":
        if not console.confirm("Uploading to live site: sure?", default=False):
            utils.abort("User aborted")

    deploy_code()
    install_requirements()

    deploy_static()
    set_media_permissions()
    run_migrations()

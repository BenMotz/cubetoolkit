import os
import os.path
import sys

from fabric import task
from invoke.exceptions import Exit

IMAGE_REPOSITORY = "toolkit"
IMAGE_BUILD_DIR = "tmp_toolkit_deploy_{}"

DEFAULT_HOST = "cubecinema.com"


def _assert_target_set(c):
    if not hasattr(c.config, "site_root"):
        raise Exit("Target not specified - e.g. 'fab cube_staging deploy'")


def _assert_docker_available(c):
    # print(f"ADA c type: {type(c)}\n\n")
    result = c.run("docker version", hide=True, warn=True, pty=False)
    if result.failed:
        raise Exit("Docker not available or user does not have permission")


def _confirm(question, default=True):
    prompt = f"{question} [{'Y/n' if default else 'y/N'}]"
    while True:
        response = input(prompt).lower().strip()
        if not response:
            return default
        elif response in ["y", "yes"]:
            return True
        elif response in ["n", "no"]:
            return False
        else:
            print("Enter'(y)es' or '(n)o'", file=sys.stderr)


@task(hosts=[DEFAULT_HOST])
def cube_staging(c):
    """Configure to deploy to staging on cubecinema.com"""
    c.config.target = "staging"
    c.config.site_root = "/home/staging/site"
    c.config.media = "/home/staging/site/media/"
    c.config.docker_image_tag = "staging"
    c.config.docker_compose_file = "docker-compose-staging.yml"
    c.config.docker_compose_project = "toolkit_staging"
    c.config.media_user = "staging"


@task(hosts=[DEFAULT_HOST])
def cube_production(c):
    """Configure to deploy live on cubecinema.com"""
    c.config.target = "production"
    c.config.site_root = "/home/toolkit/site"
    c.config.media = "/home/toolkit/site/media/"
    c.config.docker_image_tag = "production"
    c.config.docker_compose_file = "docker-compose-production.yml"
    c.config.docker_compose_project = "toolkit_production"
    c.config.media_user = "toolkit"


def _image_build_dir(build_root, target):
    return os.path.join(build_root, IMAGE_BUILD_DIR.format(target))


@task(hosts=[DEFAULT_HOST])
def build_remote_image(c):
    """Upload git HEAD snapshot to target and build the image"""

    _assert_target_set(c)
    _assert_docker_available(c)

    build_root = c.run("echo $HOME", hide=True).stdout.strip()

    # Create tar of (local) git HEAD using the hash as the filename
    git_rev = c.local(
        "git rev-parse --short=10 HEAD", hide=True
    ).stdout.strip()
    archive = f"tk-snapshot-{git_rev}.tgz"
    local_root = os.path.dirname(__file__)

    print("Creating site tgz")
    # we need to be in the site root to create the tgz correctly:
    c.local(f"cd {local_root} && git archive --format=tgz HEAD > {archive}")

    # Upload to remote:
    print("Uploading to remote")
    c.put(archive, build_root)

    image_build_dir = _image_build_dir(build_root, target=c.config.target)

    # Delete old build directory
    print(f"Deleting and recreating {format(image_build_dir)}")
    c.run(f"rm -rf {image_build_dir}")
    c.run(f"mkdir {image_build_dir}")

    # Extract:
    print(f"Extracting {archive}")
    # Untar with -m to avoid trying to utime /media directories that
    # may be owned by the webserver (which then fails)
    c.run(f"cd {image_build_dir} && tar -m -xzf ../{archive}")

    print("Building image")
    c.run(
        f"cd {image_build_dir} && docker build --pull --tag {IMAGE_REPOSITORY}:{c.config.docker_image_tag} ."
    )


@task(hosts=[DEFAULT_HOST])
def docker_compose_up(c):
    build_root = c.run("echo $HOME", hide=True).stdout.strip()
    image_build_dir = _image_build_dir(build_root, target=c.config.target)
    compose_file = os.path.join(image_build_dir, c.config.docker_compose_file)

    print("Bringing up docker-compose")
    c.run(
        f"cd {image_build_dir} && "
        f"docker-compose "
        f"--project-name {c.config.docker_compose_project} "
        f"--file {compose_file} "
        f"up "
        f"--detach "
        f"--no-build"
    )


@task(hosts=[DEFAULT_HOST])
def set_media_permissions(c):
    """Set media directories to g+w"""
    media_dirs = [
        "media/diary",
        "media/printedprogramme",
        "media/volunteers",
        "media/images",
        "media/original_images",
        "media/documents",
    ]

    c.close()
    old_user = c.user
    c.user = c.config.media_user
    print("Setting media permissions")
    for media_dir in media_dirs:
        path = os.path.join(c.config.site_root, media_dir)
        c.run(f"chmod g+w {path}")
    c.close()
    c.user = old_user


@task(hosts=[DEFAULT_HOST])
def get_media(c):
    """Rsync media content from a production server to your development environment"""

    _assert_target_set(c)

    c.local(
        f"rsync -av --delete --exclude=thumbnails {c.config.user}@{DEFAULT_HOST}:{c.config.media}/ media/",
        echo=True,
    )


@task(hosts=[DEFAULT_HOST])
def sync_media_from_production_to_staging(c):
    """Rsync media content from the production server to the staging server. Invoke as fab cube_staging sync_media_from_production_to_staging"""

    # TODO define explicitly
    _assert_target_set(c)

    c.run(
        f"cd {c.config.site_root} && "
        f"rsync -av --delete --exclude=thumbnails /home/toolkit/site/media/ {c.config.media}",
        echo=True,
    )


@task(hosts=[DEFAULT_HOST])
def fetch_database_dump(c, dump_filename="database_dump.sql"):
    dump_file_gz = dump_filename + ".gz"
    if os.path.exists(dump_filename) or os.path.exists(dump_file_gz):
        raise Exit(f"Local file {dump_filename} already exists")

    print("Generating remote database dump")

    # Ask manage.py in the toolkit container for the mysqldump command to run
    # (which will include the DB name, user and password)
    dump_command = c.run(
        f"docker exec {c.config.docker_compose_project}_toolkit_1 "
        "/venv/bin/python3 manage.py mysqldump_database --print-command STDOUT",
        hide=True,
    ).stdout.strip()

    c.run(f"{dump_command} | gzip > {dump_file_gz}", hide=True)

    print("Downloading database dump")
    c.get(dump_file_gz, local=dump_file_gz)
    c.run(f"rm {dump_file_gz}")

    c.local(f"gunzip {dump_file_gz}")


@task(hosts=[DEFAULT_HOST])
def deploy(c):
    """Upload code, build image, bring docker-compose up"""

    _assert_target_set(c)

    if c.config.target == "production":
        if not _confirm("Uploading to live site: sure?", default=False):
            raise Exit("User aborted")

    build_remote_image(c)
    set_media_permissions(c)
    docker_compose_up(c)

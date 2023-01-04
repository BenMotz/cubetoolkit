import os
import os.path

from fabric.api import require, env, run, cd, local, put, lcd, get, prompt
from fabric.tasks import Task
from fabric.context_managers import settings
from fabric import utils
from fabric.contrib import console

IMAGE_REPOSITORY = "toolkit"
IMAGE_BUILD_DIR = "tmp_toolkit_deploy_{}"


def _assert_target_set():
    # utility method to check that target is defined:
    require(
        "site_root",
        provided_by=(
            "cube_staging",
            "cube_production",
        ),
    )


def _assert_docker_available():
    result = run("docker version", quiet=True, warn_only=True, pty=False)
    if result.failed:
        utils.abort("Docker not available or user does not have permission")


def cube_staging():
    """Configure to deploy to staging on cubecinema.com"""
    env.target = "staging"
    env.site_root = "/home/staging/site"
    env.media = "/home/staging/site/media/"
    env.hosts = ["cubecinema.com"]
    env.docker_image_tag = "staging"
    env.docker_compose_file = "docker-compose-staging.yml"
    env.docker_compose_project = "toolkit_staging"
    env.media_user = "staging"


def cube_production():
    """Configure to deploy live on cubecinema.com"""
    env.target = "production"
    env.site_root = "/home/toolkit/site"
    env.media = "/home/toolkit/site/media/"
    env.hosts = ["cubecinema.com"]
    env.docker_image_tag = "production"
    env.docker_compose_file = "docker-compose-production.yml"
    env.docker_compose_project = "toolkit_production"
    env.media_user = "toolkit"


def _image_build_dir(build_root):
    return os.path.join(build_root, IMAGE_BUILD_DIR.format(env.target))


def build_remote_image():
    """Upload git HEAD snapshot to target and build the image"""

    _assert_target_set()
    _assert_docker_available()

    build_root = run("echo $HOME", quiet=True)

    # Create tar of (local) git HEAD using the hash as the filename
    archive = "tk-snapshot-%s.tgz" % local(
        "git rev-parse --short=10 HEAD", capture=True
    )
    local_root = os.path.dirname(__file__)
    utils.puts("Changing to {0}".format(local_root))
    with lcd(local_root):
        # (we need to be in the site root to create the tgz correctly)
        utils.puts("Creating site tgz")
        local("git archive --format=tgz HEAD > {0}".format(archive))

        # Upload to remote:
        utils.puts("Uploading to remote")
        put(archive, build_root)

        image_build_dir = _image_build_dir(build_root)

        # Delete old build directory
        utils.puts("Deleting and recreating {0}".format(image_build_dir))
        run("rm -rf {0}".format(image_build_dir))
        run("mkdir {0}".format(image_build_dir))

        with cd(image_build_dir):
            # Extract:
            utils.puts("Extracting {0}".format(archive))
            # Untar with -m to avoid trying to utime /media directories that
            # may be owned by the webserver (which then fails)
            run("tar -m -xzf ../{0}".format(archive))

            utils.puts("Building image")
            run(
                "docker build --pull --tag {0}:{1} .".format(
                    IMAGE_REPOSITORY, env.docker_image_tag
                )
            )


def docker_compose_up():
    build_root = run("echo $HOME", quiet=True)
    image_build_dir = _image_build_dir(build_root)
    compose_file = os.path.join(image_build_dir, env.docker_compose_file)
    with cd(image_build_dir):
        utils.puts("Bringing up docker-compose")
        run(
            "docker-compose --project-name {0} --file {1} up --detach --no-build".format(
                env.docker_compose_project, compose_file
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


def deploy():
    """Upload code, build image, bring docker-compose up"""

    _assert_target_set()

    if env.target == "production":
        if not console.confirm("Uploading to live site: sure?", default=False):
            utils.abort("User aborted")

    build_remote_image()
    with settings(user=env.media_user):
        set_media_permissions()
    docker_compose_up()

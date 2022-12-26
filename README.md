Cube Toolkit
============

Introduction
------------

This is the code that powers parts of the Cube Microplex, a volunteer run
thing in Bristol, UK: http://www.cubecinema.com/

It's a Django (i.e. Python) application that (currently) provides an event
diary, membership database, and CMS (using Wagtail).

It was initially written to closely emulate a set of Perl CGI scripts, which
is why the UI is the way it is.

Deployment for production
-------------------------

At present the application is deployed directly onto a real live server that
you could drop on your foot if you were so minded. On that server it runs
from a container managed by docker-compose. The full process for deployment
is mildly complicated, and there are detailed instructions on the Cube wiki
about how to do it.


Running for development
-----------------------

There are two ways to run locally; under docker, and directly with your local
python.

A docker-compose.yml file is provided that should work to run the toolkit and
required services. Note the configuration it provides is not very secure.

For advice on running under local python see the cube wiki or ask me.

License
-------
The code is copyright Ben Motz and other contributors. It's currently,
slightly arbitrarily, distributed under the GNU Affero license (see LICENSE).
If you want to use this code under some other FLOSS license then do ask, as
it's unlikely to be a problem.

This specifically excludes the following files:

*  /toolkit/members/static/members/cube_microplex_logo.gif
*  /toolkit/members/static/members/default_mugshot.gif
*  /toolkit/diary/static/diary/diary_edit_list_header.gif
*  toolkit/content/static/content/logo.gif

These images are copyright Cube Cinema Ltd, which has not given me permission
to distribute them, and certainly hasn't given you permission.

This repository also includes code from other authors that may be under
other licenses, as indicated. Specifically the contents of the following
directories:

* toolkit/static_common/js/lib/
* toolkit/static_common/css/lib/
* toolkit/diary/static/diary/js/lib/

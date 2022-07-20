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
you could drop on your foot if you were so minded. The process for deployment
is somewhat complicated, and there are detailed instructions on the Cube wiki
about how to deploy to do it.(If anyone ever expresses any interest at all then
I'd be happy to suck that out of the Cube wiki into this repository.)

In the future the plan is to deploy the application in a container; there is
a Dockerfile you can build (`docker build . --tag toolkit:latest`), however
this is not yet in use in production.

There is a `docker-compose.yml` file that may be used with docker-compose to
run the toolkit and associated services: this is currently intended for
development and experimentation, not for production.

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

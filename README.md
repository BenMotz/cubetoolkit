Cube Toolkit
============

Introduction
------------

This is the code that powers parts of the Cube Microplex, a volunteer run
thing in Bristol, UK: http://www.cubecinema.com/

It's a Django (i.e. Python) application that (currently) provides an event
diary and membership database.

It was initially written to closely emulate a set of Perl CGI scripts, which
is why the UI is the way it is.

Installation
------------
This is very much the code for the Cube's purposes, as such no great effort
has been made to make it easy to install elsewhere. There are detailed
instructions on the Cube wiki about how to get the development version up and
running, and how to deploy to the Cube's live and staging servers. If anyone
ever expresses any interest at all then I'd be happy to suck that out of the
Cube wiki into this repository.

License
-------
The code is copyright Ben Motz and other contributors. It's currently,
slightly arbitrarily, distributed under the GNU Affero license (see LICENSE).
If you want to use this code under some other FLOSS license then do ask, as
it's unlikely to be a problem.

This specifically excludes the following files:
/toolkit/members/static/members/cube_microplex_logo.gif
/toolkit/members/static/members/default_mugshot.gif
and all the .gif and .png files in the directory:
/toolkit/diary/static/diary/
These images are copyright Cube Cinema Ltd, which has not given me permission
to distribute them. Make of that what you will.

This repository also includes code from other authors that may be under
other licenses, as indicated. Specifically the contents of the following
directories:
/easy_thumbnails/
toolkit/static_common/js/lib/
toolkit/static_common/css/lib/

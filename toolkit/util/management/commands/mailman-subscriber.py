#!/usr/bin/env python
# vi: set et sw=4 st=4:
#
# 2004-08-27 Jim Tittsler <jwt@starship.python.net>
# 2004-10-03 jwt    change authentication
# 2004-10-04 jwt    remove dependency on ClientCookie
# 2004-10-07 jwt    use getopt to retrieve host, list, password from command
# 2004-10-10 jwt    return to using ClientCookie
# 2004-10-13 jwt    add --fullnames option
# 2005-02-15 jwt    switch on RFC2965 cookie support when newer version
#                     of ClientCookie is detected
# 2005-02-16 jwt    use Python 2.4's cookielib if it is available
# 2005-02-27 jwt    only visit the roster page for letters that exist
# 2005-06-04 mas    add --nomail option (Mark Sapiro <msapiro.value.net>)
# 2005-06-14 jwt    handle chunks of email addresses starting [0-9]*
# 2010-01-29 jwt    add explicit license (GPLv2)
#
# mailman_subscribers.py scripts the Mailman admin web interface
# Copyright 2010 James W. Tittsler
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301, USA.


"""List the email addresses subscribed to a mailing list, fetched from web.

Usage: %(PROGRAM)s [options] hostname listname password

Where:
   --output file
   -o file
       Write output to specified file instead of standard out.

   --fullnames
   -f
       Include the full names in the output.

   --nomail
   -n
       List only no-mail members

   --verbose
   -v
       Include extra progress output.

   --help
   -h
       Print this help message and exit

   hostname is the name used in the URL of the list's web interface
   listname is the name of the mailing list
   password is the list's admin password

   The list of subscribers is fetched from the web administrative
   interface.  Using the bin/list_members program from a shell
   account is preferable, but not always available.

   Tested with the Mailman 2.1.5/2.1.6 member roster layout.

   If Python 2.4's cookielib is available,  use it.  Otherwise require
   ClientCookie  http://wwwsearch.sourceforge.net/ClientCookie/
"""

import sys
import re
import string
import urllib
import getopt
from HTMLParser import HTMLParser

# if we have Python 2.4's cookielib, use it
try:
    import cookielib
    import urllib2

    policy = cookielib.DefaultCookiePolicy(rfc2965=True)
    cookiejar = cookielib.CookieJar(policy)
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookiejar)).open
except ImportError:
    import ClientCookie

    # if this is a new ClientCookie, we need to turn on RFC2965 cookies
    cookiejar = ClientCookie.CookieJar()
    try:
        cookiejar.set_policy(ClientCookie.DefaultCookiePolicy(rfc2965=True))
        # install an opener that uses this policy
        opener = ClientCookie.build_opener(
            ClientCookie.HTTPCookieProcessor(cookiejar)
        )
        ClientCookie.install_opener(opener)
    except AttributeError:
        # must be an old ClientCookie, which already accepts RFC2965 cookies
        pass
    opener = ClientCookie.urlopen

PROGRAM = sys.argv[0]


def usage(code, msg=""):
    if code:
        fd = sys.stderr
    else:
        fd = sys.stdout
    print >> fd, __doc__ % globals()
    if msg:
        print >> fd, msg
    sys.exit(code)


subscribers = {}
nomails = {}
maxchunk = 0
letters = ["0"]
processed_letters = []


class MailmanHTMLParser(HTMLParser):
    """cheap way to find email addresses and pages with multiple
    chunks from Mailman 2.1.5 membership pages"""

    def handle_starttag(self, tag, attrs):
        global maxchunk, letters
        if tag == "input":
            s = False
            for a, v in attrs:
                if a == "name" and v.endswith("_realname"):
                    subemail = v[:-9]
                    s = True
                elif a == "value":
                    subname = v
            if s and not subscribers.has_key(subemail):
                subscribers[subemail] = subname
            t = False
            for a, v in attrs:
                if a == "name" and v.endswith("_nomail"):
                    nmemail = v[:-7]
                    t = True
                elif a == "value":
                    subnomail = v
            if t and not nomails.has_key(nmemail):
                nomails[nmemail] = subnomail
        if tag == "a":
            for a, v in attrs:
                if a == "href" and v.find("/mailman/admin/"):
                    m = re.search(r"chunk=(?P<chunkno>\d+)", v, re.I)
                    if m:
                        if int(m.group("chunkno")) > maxchunk:
                            maxchunk = int(m.group("chunkno"))
                    m = re.search(r"letter=(?P<letter>[0-9a-z])", v, re.I)
                    if m:
                        letter = m.group("letter")
                        if (
                            letter not in letters
                            and letter not in processed_letters
                        ):
                            letters.append(letter)


def main():
    global maxchunk, letters
    try:
        opts, args = getopt.getopt(
            sys.argv[1:],
            "ho:fnv",
            ["help", "output=", "fullnames", "nomail", "verbose"],
        )
    except:
        usage(2)

    fp = sys.stdout
    fullnames = False
    nomail = False
    verbose = False
    for o, a in opts:
        if o in ("-v", "--verbose"):
            verbose = True
        if o in ("-h", "--help"):
            usage(0)
        if o in ("-o", "--output"):
            fp = open(a, "wt")
        if o in ("-f", "--fullnames"):
            fullnames = True
        if o in ("-n", "--nomail"):
            nomail = True
    if len(args) != 3:
        usage(2)
    member_url = "https://%s/mailman/admin/%s/members" % (args[0], args[1])
    p = {"adminpw": args[2]}

    # login, picking up the cookie
    page = opener(member_url, urllib.urlencode(p))
    page.close()
    p = {}

    # loop through the letters, and all chunks of each
    while len(letters) > 0:
        letter = letters[0]
        letters = letters[1:]
        processed_letters.append(letter)
        chunk = 0
        maxchunk = 0
        while chunk <= maxchunk:
            if verbose:
                print >>sys.stdout, "%c(%d)" % (letter, chunk)
            page = opener(member_url + "?letter=%s&chunk=%d" % (letter, chunk))
            lines = page.read()
            page.close()

            parser = MailmanHTMLParser()
            parser.feed(lines)
            parser.close()
            chunk += 1

    subscriberlist = subscribers.items()
    subscriberlist.sort()

    # print the subscribers list
    for (email, name) in subscriberlist:
        if nomail and nomails[email] == "off":
            continue
        if not fullnames or name == "":
            print >> fp, email
        else:
            print >> fp, "%s <%s>" % (name, email)

    fp.close()


if __name__ == "__main__":
    main()

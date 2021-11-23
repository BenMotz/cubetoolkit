"""Process member's mailing list email bounces by logging into the mail server
mailbox which receives the bounces, inspecting the bounced mails,
and unsubcribing the members associated with the bounced mails.
Also deletes over-quota and holiday replies from the mailbox.
invoke with python2 mailoutomatic.py
"""
import os
import sys
import datetime
import imaplib
import email
import string
import random
import StringIO
import rfc822
import re
from urllib import urlopen
import logging

"""
File: imaplib-example-1.py
from http://effbot.org/librarybook/imaplib.htm

See also
http://www.doughellmann.com/PyMOTW/imaplib/index.html

Recipe 52560: Remove duplicates from a sequence
http://code.activestate.com/recipes/52560/
http://python.about.com/od/pythonstandardlibrary/ss/email_whitelist_5.htm

TODO
* Rewrite for python3
* Cope with Re: in subject line
* Unacceptable Mail Content
* spam detected
* "Message contains spam or virus"
* Use MD5 password
"""

mailserver_default = "localhost"
user_default = "admin"
mailbox_default = "Inbox.logs.mailout bounces"
site = "cubecinema.com"

verbose = True
deleteStuff = True  # Delete processed mails from mailbox
unsubscribe = True  # Unsubscribe members from toolkit
expunge = True  # Expunge mailbox on completion
maxMesgNo = (
    10000  # Max number of mails to process. Use a lower number for testing
)


def emailHits(domain, domains):
    if domain in domains:
        domains[domain] = domains[domain] + 1
    else:
        domains[domain] = 1


"""
Examples of gone away strings

Mailbox disabled
mailbox unavailable
This is a permanent error
Unrouteable address  (bris.ac.uk)
recipient rejected
The email account that you tried to reach does not exist (google)
This user doesn't have a yahoo.co.uk account
Rcpt <johnsmith@safe-mail.net> does not exist
unable to validate recipient  (virgin/blueyonder)
Delivery has failed
"""

GoneAway = "Mailbox disabled|mailbox unavailable|Mailbox is inactive|This is a permanent error"
GoneAway += "|Unrouteable address|recipient rejected|unknown or illegal alias"
GoneAway += "|The email account that you tried to reach does not exist"
GoneAway += "|This user doesn't have a .* account|Address rejected"
GoneAway += (
    "|Rcpt .* does not exist|recipient.*known|Recipient address rejected"
)
GoneAway += "|unable to validate recipient|Invalid recipient"
GoneAway += "|account has been disabled or discontinued"
GoneAway += (
    "|User unknown|Unknown user|User is unknown|account has been disabled"
)
GoneAway += "|No such user|Recipient address rejected|User does not exist"
GoneAway += "|No such recipient|no mailbox|No such mailbox"
GoneAway += "|Delivery.*failed|inactive user"
GoneAway += "|email account that you tried to reach is disabled"
GoneAway += "|email account that you tried to reach does not exist"
GoneAway += "|Unknown local part|MAILBOX NOT FOUND"
GoneAway += "|This email address is not known to this system"
GoneAway += "|unknown or illegal alias|disabled mailbox"
GoneAway += "|cannot find address on system|is a deactivated mailbox"
GoneAway += "|Incoming mail not allowed to this address"
GoneAway += "|Account Inactive"
GoneAway += "|dd Requested mail action aborted"
GoneAway += "|This mailbox is disabled"

SpamAlleged = "Your email was detected as spam"
SpamAlleged += "|Message contains spam"
SpamAlleged += "|Message is spam"
SpamAlleged += "|detected as spam"
SpamAlleged += "|looks like spam"
SpamAlleged += "|rejected by recipients spam filter"
SpamAlleged += "|spam detected"
SpamAlleged += "|detected as spam"
SpamAlleged += "|Message rejected as spam"
SpamAlleged += "|this message looked like spam"

"""Examples of over quota strings
full, over quota
mailbox is full
Over quota"""

OverQuota = "over quota|mailbox.*full|overquota|too many messages|quota exceeded|user has exhausted allowed storage space|full mailbox|temporarily deferred"

SPF = "SPF verification failed for host"

# Name server errors
NameServerError = "name service error"

LOG_DIR = "/var/log/cubetoolkit"
LOG_FILENAME = "mailoutomatic-%s.log" % datetime.datetime.now().strftime(
    "%d-%b-%Y-%H:%m:%S"
)

"""logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filename=LOG_FILENAME,
                    filemode='w')
"""
# https://docs.python.org/2/howto/logging.html
# create logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# create formatter
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s", datefmt="%I:%M:%S %p"
)
# add formatter to ch
ch.setFormatter(formatter)
# add ch to logger
logger.addHandler(ch)

handler = logging.FileHandler(os.path.join(LOG_DIR, LOG_FILENAME), mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.INFO)
logger.addHandler(handler)  # add the handlers to the logger


REMOVELIST = [
    "undeliverable",
    "failure",
    "undelivered mail returned to sender",
    "failed",
    "returned mail",
    "delivery status",
    "problems",
]  # removed returned

DELETEON = ["auto", "office", "vacation", "away", "warning", "maternity"]

mailserver = raw_input("Enter name of mail server [%s]: " % mailserver_default)
if not mailserver:
    mailserver = mailserver_default
user = raw_input("Enter mail user name [%s]: " % user_default)
if not user:
    user = user_default
mailbox = raw_input("Enter mailbox name [%s]: " % mailbox_default)
if not mailbox:
    mailbox = mailbox_default
password = raw_input("Enter mail password for user %s: " % user)

removeCount = 0
overQuotaCount = 0
nameErrorCount = 0  # TODO
SPFErrorCount = 0
spamCount = 0
manualUnsubscribeCnt = 0
removedDomains = {}

"""Example removalstring:
http://cubecinema.com/members/19999/unsubscribe/?k=T4EL2xJnHLrR63H4fhm8rRj7IU6WA1Pa
See https://regex101.com/
"""
removeStr = r"https:\/\/%s\/members\/(\d+)\/unsubscribe\/\?k=(.+)" % site

# connect to server
server = imaplib.IMAP4(mailserver)

# login
msg_str = 'Logging in to mail server "%s" as user "%s"...' % (mailserver, user)
logging.info(msg_str)

response = server.login(user, password)
logging.info(response)

# Select a mailbox. Returned data is the count of messages in mailbox
# (EXISTS response). The default mailbox is 'INBOX'. If the readonly flag is
# set, modifications to the mailbox are not allowed.
# Status should be string 'OK'

(status, msg_cnt) = server.select(mailbox)

msg_str = 'Mailbox "%s" contains %d mails' % (mailbox, int(msg_cnt[0]))
logging.info(msg_str)

# list items on server
# resp, items = server.search(None, "ALL")
# resp should be the string 'OK', items is list, the first item of which is a
# string containing the matching messages

# sys.exit(0)

msg_str = "Processing matches from Delete list ..."
logging.info(msg_str)

for keyWord in DELETEON:
    resp, items = server.search(None, "SUBJECT", keyWord)

    # msg_ids is str of matching ids
    # resp, [msg_ids] = server.search(None, 'SUBJECT', SEARCHON)

    items = string.split(items[0])  # doesn't do anything ??

    msg_str = '    %d messages matching "%s" found' % (len(items), keyWord)
    logging.info(msg_str)

    if deleteStuff:
        for id in items:
            # What are the current flags?
            # if verbose:
            #     typ, response = server.fetch(id, '(FLAGS)')
            #     print 'msg id %s: %s' % (id, response)

            # Change the Deleted flag
            typ, response = server.store(id, "+FLAGS", r"(\Deleted)")

            # typ, response = server.fetch(id, '(FLAGS)')
            # print 'msg id %s: %s' % (id, response)

        msg_str = '    deleted %d messages with subject "%s"' % (
            len(items),
            keyWord,
        )
        logging.info(msg_str)

msg_str = "Processing matches from Remove list ..."
logging.info(msg_str)

for keyWord in REMOVELIST:
    # Header checks
    resp, items = server.search(None, "SUBJECT", keyWord)
    items = string.split(items[0])
    msg_str = '    %d messages matching "%s" found' % (len(items), keyWord)
    logging.info(msg_str)

    # TODO Calculate the missing messages

    # Fetch the message for body checks
    for id in items:
        if int(id) < maxMesgNo:
            msg_str = "        Inspecting message %s" % id
            logging.info(msg_str)
            typ, msg_data = server.fetch(id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_string(response_part[1])
                    if False:
                        for header in ["subject", "to", "from"]:
                            print(
                                "    %-8s: %s" % (header.upper(), msg[header])
                            )
                    # if msg.is_multipart():
                    #     # TODO
                    #     out = msg.get_payload()
                    #     for i in out:
                    #         msgText =out[i].as_string()
                    # else:
                    msgText = msg.as_string()

                    m = re.search(OverQuota, msgText, re.I)
                    if bool(m):
                        u = m.group(0)
                        msg_str = '        "%s" found' % u
                        logging.info(msg_str)
                        overQuotaCount += 1
                        # Delete over quota mails
                        if deleteStuff:
                            typ, response = server.store(
                                id, "+FLAGS", r"(\Deleted)"
                            )
                            # TODO use response

                    else:  # Not over quota - continue
                        # Check for SPF error
                        m = re.search(SPF, msgText, re.I)
                        if bool(m):
                            u = m.group(0)
                            msg_str = '        "%s" found' % u
                            SPFErrorCount += 1
                            # Delete over quota mails
                            if deleteStuff:
                                typ, response = server.store(
                                    id, "+FLAGS", r"(\Deleted)"
                                )
                                # TODO use response

                        # Check for name server error
                        m = re.search(NameServerError, msgText, re.I)
                        if bool(m):
                            u = m.group(0)
                            msg_str = '        "%s" found' % u
                            nameErrorCount += 1
                            # TODO break from here?

                        # Check fo message flagged as spam
                        m = re.search(SpamAlleged, msgText, re.I)
                        if bool(m):
                            u = m.group(0)
                            msg_str = '        "%s" found' % u
                            spamCount += 1
                            # TODO break from here?

                        # Check if the email has bounced
                        m = re.search(GoneAway, msgText, re.I)
                        if bool(m):
                            u = m.group(0)
                            msg_str = '            "%s" found' % u
                            logging.info(msg_str)

                            # Now see if we can find the unsubscribe string
                            # ignoring case
                            m = re.search(removeStr, msgText, re.I)
                            if bool(m):
                                u = m.group(0).strip()
                                msg_str = "            %s found" % u
                                logging.info(msg_str)
                                removeCount = removeCount + 1

                                # u1 = re.sub('unsubscribe', 'unsubscribe-now', u)
                                # print u1; logging.info(u1)

                                if unsubscribe:

                                    # Get the email address of who we are unsubscribing
                                    u_info = re.sub("unsubscribe", "edit", u)
                                    reply = urlopen(u_info).read()
                                    m = re.search(
                                        r"name=\"email\" value=\"(.*)\" id=\"id_email",
                                        reply,
                                    )
                                    if bool(m):
                                        punter = m.group(1)
                                    else:
                                        punter = "unknown"

                                    u_now = re.sub(
                                        "unsubscribe", "unsubscribe-now", u
                                    )
                                    reply = urlopen(u_now).read()
                                    # TODO check for class="success"
                                    logging.debug(reply)
                                    msg_str = (
                                        "            unsubscribed %s" % punter
                                    )
                                    logging.info(msg_str)

                                    # strip the user to get the email domain
                                    # removedMails.append(removedMail)
                                    if True:
                                        m = re.search(r"\@.*", punter)
                                        if bool(m):
                                            domain = m.group(0)[
                                                1:
                                            ]  # discard the leading @
                                            emailHits(
                                                domain, removedDomains
                                            )  # store the domain

                                    # Now delete the email
                                    typ, response = server.store(
                                        id, "+FLAGS", r"(\Deleted)"
                                    )
                                    # TODO check response
                                    # msg_str = response
                                    # logging.info(msg_str)

                            else:
                                msg_str = "    unsubscribe string not found"
                                logging.info(msg_str)
                                manualUnsubscribeCnt += 1
                                # TODO print the email address

                        else:
                            msg_str = "            bounce string not found"
                            logging.info(msg_str)

# Really delete the messages
if expunge:
    typ, response = server.expunge()
    msg_str = "Expunged %d mails" % len(response)
    logging.info(msg_str)

(status, msg_cnt) = server.select(mailbox)
msg_str = 'Mailbox "%s" now contains %d mails' % (mailbox, int(msg_cnt[0]))
logging.info(msg_str)

# server.close()   # TODO
msg_str = server.logout()
logging.info(msg_str)

msg_str = "%d over quota reports" % overQuotaCount
logging.info(msg_str)

msg_str = "%d message flagged as spam" % spamCount
logging.info(msg_str)

msg_str = "%d name server errors" % nameErrorCount
logging.info(msg_str)

if unsubscribe:
    msg_str = "%d subscribers removed" % removeCount
else:
    msg_str = "%d subscribers would have been removed" % removeCount
logging.info(msg_str)

msg_str = "%d subscribers will need removing manually" % manualUnsubscribeCnt
logging.info(msg_str)

if unsubscribe:
    msg_str = "Removed these domains: "
    logging.info(msg_str)

    for key in removedDomains:
        msg_str = "%s -> %s" % (key, removedDomains[key])
        logging.info(msg_str)

sys.exit(0)

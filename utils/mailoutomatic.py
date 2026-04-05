"""Process member's mailing list email bounces by logging into the mail server
mailbox which receives the bounces, inspecting the bounced mails,
and unsubscribing the members associated with the bounced mails.
Also deletes over-quota and holiday replies from the mailbox.
invoke with python3 mailoutomatic.py
"""

import os
import sys
import datetime
import imaplib
import email
import re
import logging
from urllib.request import urlopen

"""
File: imaplib-example-1.py
from http://effbot.org/librarybook/imaplib.htm

See also
http://www.doughellmann.com/PyMOTW/imaplib/index.html

Recipe 52560: Remove duplicates from a sequence
http://code.activestate.com/recipes/52560/
http://python.about.com/od/pythonstandardlibrary/ss/email_whitelist_5.htm

TODO
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
maxMesgNo = 10000  # Max number of mails to process. Use a lower number for testing


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

GoneAway = (
    "Mailbox disabled|mailbox unavailable|Mailbox is inactive|This is a permanent error"
)
GoneAway += "|Unrouteable address|recipient rejected|unknown or illegal alias"
GoneAway += "|The email account that you tried to reach does not exist"
GoneAway += "|This user doesn't have a .* account|Address rejected"
GoneAway += "|Rcpt .* does not exist|recipient.*known|Recipient address rejected"
GoneAway += "|unable to validate recipient|Invalid recipient"
GoneAway += "|account has been disabled or discontinued"
GoneAway += "|User unknown|Unknown user|User is unknown|account has been disabled"
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
OverQuota += "|Access denied"

SPF = "SPF verification failed for host"

# Name server errors
NameServerError = "name service error"

LOG_DIR = "/var/log/cubetoolkit"
LOG_FILENAME = (
    f"mailoutomatic-{datetime.datetime.now().strftime('%d-%b-%Y-%H:%M:%S')}.log"
)

# https://docs.python.org/3/howto/logging.html
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Console handler
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s", datefmt="%I:%M:%S %p"
)
ch.setFormatter(formatter)
logger.addHandler(ch)

handler = logging.FileHandler(os.path.join(LOG_DIR, LOG_FILENAME), mode="w")
handler.setFormatter(formatter)
handler.setLevel(logging.INFO)
logger.addHandler(handler)


REMOVELIST = [
    "undeliverable",
    "failure",
    "undelivered mail returned to sender",
    "failed",
    "returned mail",
    "delivery status",
    "problems",
]

DELETEON = ["auto", "office", "vacation", "away", "warning", "maternity"]

mailserver = input(f"Enter name of mail server [{mailserver_default}]: ")
if not mailserver:
    mailserver = mailserver_default
user = input(f"Enter mail user name [{user_default}]: ")
if not user:
    user = user_default
mailbox = input(f"Enter mailbox name [{mailbox_default}]: ")
if not mailbox:
    mailbox = mailbox_default
password = input(f"Enter mail password for user {user}: ")

removeCount = 0
overQuotaCount = 0
nameErrorCount = 0
SPFErrorCount = 0
spamCount = 0
manualUnsubscribeCnt = 0
removedDomains = {}

"""Example removalstring:
http://cubecinema.com/members/19999/unsubscribe/?k=T4EL2xJnHLrR63H4fhm8rRj7IU6WA1Pa
See https://regex101.com/
"""
removeStr = rf"https:\/\/{site}\/members\/(\d+)\/unsubscribe\/\?k=(.+)"

# connect to server securely on port 993
server = imaplib.IMAP4_SSL(mailserver, 993)

# login
logging.info(f'Logging in to mail server "{mailserver}" as user "{user}"...')
response = server.login(user, password)
logging.info(response)

# Select a mailbox. Returned data is the count of messages in mailbox
# (EXISTS response). The default mailbox is 'INBOX'. If the readonly flag is
# set, modifications to the mailbox are not allowed.
(status, msg_cnt) = server.select(f'"{mailbox}"')
logging.info(f'Mailbox "{mailbox}" contains {int(msg_cnt[0])} mails')

logging.info("Processing matches from Delete list ...")

for keyWord in DELETEON:
    resp, items = server.search(None, "SUBJECT", f'"{keyWord}"')

    # In Python 3, items[0] is bytes
    item_list = items[0].split()

    logging.info(f'    {len(item_list)} messages matching "{keyWord}" found')

    if deleteStuff:
        for msg_id in item_list:
            server.store(msg_id, "+FLAGS", r"(\Deleted)")

        logging.info(f'    deleted {len(item_list)} messages with subject "{keyWord}"')

logging.info("Processing matches from Remove list ...")

for keyWord in REMOVELIST:
    resp, items = server.search(None, "SUBJECT", f'"{keyWord}"')
    item_list = items[0].split()
    logging.info(f'    {len(item_list)} messages matching "{keyWord}" found')

    for msg_id in item_list:
        if int(msg_id) < maxMesgNo:
            logging.info(f"        Inspecting message {msg_id.decode()}")
            typ, msg_data = server.fetch(msg_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    # In Python 3, response_part[1] is bytes
                    msg = email.message_from_bytes(response_part[1])
                    msgText = msg.as_string()

                    m = re.search(OverQuota, msgText, re.I)
                    if m:
                        logging.info(f'        "{m.group(0)}" found')
                        overQuotaCount += 1
                        if deleteStuff:
                            server.store(msg_id, "+FLAGS", r"(\Deleted)")

                    else:  # Not over quota - continue
                        # Check for SPF error
                        m = re.search(SPF, msgText, re.I)
                        if m:
                            logging.info(f'        "{m.group(0)}" found')
                            SPFErrorCount += 1
                            if deleteStuff:
                                server.store(msg_id, "+FLAGS", r"(\Deleted)")

                        # Check for name server error
                        m = re.search(NameServerError, msgText, re.I)
                        if m:
                            logging.info(f'        "{m.group(0)}" found')
                            nameErrorCount += 1

                        # Check for message flagged as spam
                        m = re.search(SpamAlleged, msgText, re.I)
                        if m:
                            logging.info(f'        "{m.group(0)}" found')
                            spamCount += 1

                        # Check if the email has bounced
                        m = re.search(GoneAway, msgText, re.I)
                        if m:
                            logging.info(f'            "{m.group(0)}" found')

                            # Now see if we can find the unsubscribe string
                            m = re.search(removeStr, msgText, re.I)
                            if m:
                                u = m.group(0).strip()
                                logging.info(f"            {u} found")
                                removeCount += 1

                                if unsubscribe:
                                    # Get the email address of who we are unsubscribing
                                    u_info = re.sub("unsubscribe", "edit", u)
                                    reply = urlopen(u_info).read().decode("utf-8")
                                    m2 = re.search(
                                        r'name="email" value="(.*)" id="id_email',
                                        reply,
                                    )
                                    punter = m2.group(1) if m2 else "unknown"

                                    u_now = re.sub("unsubscribe", "unsubscribe-now", u)
                                    reply = urlopen(u_now).read().decode("utf-8")
                                    logging.debug(reply)
                                    logging.info(f"            unsubscribed {punter}")

                                    # Strip the user to get the email domain
                                    m2 = re.search(r"\@.*", punter)
                                    if m2:
                                        domain = m2.group(0)[
                                            1:
                                        ]  # discard the leading @
                                        emailHits(domain, removedDomains)

                                    # Now delete the email
                                    server.store(msg_id, "+FLAGS", r"(\Deleted)")

                            else:
                                logging.info("    unsubscribe string not found")
                                manualUnsubscribeCnt += 1

                        else:
                            logging.info("            bounce string not found")

# Really delete the messages
if expunge:
    typ, response = server.expunge()
    logging.info(f"Expunged {len(response)} mails")

(status, msg_cnt) = server.select(f'"{mailbox}"')
logging.info(f'Mailbox "{mailbox}" now contains {int(msg_cnt[0])} mails')

server.logout()

logging.info(f"{overQuotaCount} over quota reports")
logging.info(f"{spamCount} message flagged as spam")
logging.info(f"{nameErrorCount} name server errors")

if unsubscribe:
    logging.info(f"{removeCount} subscribers removed")
else:
    logging.info(f"{removeCount} subscribers would have been removed")

logging.info(f"{manualUnsubscribeCnt} subscribers will need removing manually")

if unsubscribe:
    logging.info("Removed these domains:")
    for key, val in removedDomains.items():
        logging.info(f"{key} -> {val}")

sys.exit(0)

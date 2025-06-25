"""Not strictly part of this django suite but appearing in this repo for
completeness.
Suck documents from the psimonkey era Star and Shadow django database
and use wp-cli to load documents as posts in wordpress.
Run initially with --inspect to get a list of document types and authors.
Create the document types as categories and create the wordpress users with
matching names.

"""

import subprocess

from django.core.management.base import BaseCommand
from django.utils.html import strip_tags

import MySQLdb

# Adjust to taste
dbuser = "starandshadow_archive"
dbpass = "kq9LaMpgf4czGQ9v"
dbdb = "starandshadow_archive"
wordpress_server = "localhost"
wordpress_path = "/home/adelayde/websites/xislblogs.xtreamlab.net/wordpress/"
shell_user = "marcus"
url = "dialogue.starandshadow.org.uk"


class Command(BaseCommand):
    help = (
        "Migrate documents from legacy Star and Shadow web site into wordpress"
    )

    def _conn_to_archive_database(self):
        try:
            self.stdout.write(f"Connecting to database {dbdb}...")
            db = MySQLdb.connect(
                "localhost", dbuser, dbpass, dbdb, charset="utf8"
            )
            return db
        except MySQLdb.Error as e:
            self.stdout.write(
                self.style.ERROR(f"Failed to connect to database {dbdb}")
            )

    def _read_archive_db(self, cursor, table):

        # ORDER BY `startDate` DESC"
        sql = f"SELECT * FROM `{table}`"
        # sql = "SELECT * FROM `%s` WHERE `id` = 164" % table
        # sql = "SELECT * FROM `%s`"#  LIMIT 10" % table
        # sql = "SELECT * FROM `%s` ORDER BY `created` DESC LIMIT 10 OFFSET 10" % table
        rows = cursor.execute(sql)  # returns number of rows
        self.stdout.write("%s: %d rows found" % (table, rows))
        documents = cursor.fetchall()
        return documents

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            "--inspect",
            action="store_true",
            dest="inspect",
            default=False,
            help="Enumerate authors and document types and create in wordpress",
        )

        parser.add_argument(
            "--verbose",
            action="store_true",
            dest="verbose",
            default=False,
            help="Spew out more detail",
        )

    def handle(self, *args, **options):

        db = self._conn_to_archive_database()
        cursor = db.cursor()
        doc_types = []
        authors = []

        documents = self._read_archive_db(cursor, "content_document")
        fail_count = 0
        failed_docs = list()

        for document in documents:
            legacy_id = document[0]
            title = document[1]
            title = " ".join(title.split())
            source = document[2]
            source = " ".join(source.split())
            summary = document[3]
            author = document[4].title()
            author = " ".join(author.split())
            created = document[5]
            doc_type = document[6]
            body = document[7]

            # Fix authors
            if author in [
                "",
                "Adrin Neatrour",
                "A Neatrour",
                "Adriin Neatrour",
                "Adrin Neatrour",
                "Adrin Netarour",
                "Adrinneatrour",
            ]:
                author = "adrinneatrour"
            if author in ["Yaron Golan For Kino Bambino"]:
                author = "yarongolan"
            if author in ["Phil Eastine"]:
                author = "phileastein"
            if author in ["I.M., M.F With John Smith (Adt)"]:
                author = "ilanamitchell"

            author = author.lower()
            author = author.replace(" ", "")

            doc_str = '%s "%s" "%s" "%s" %s "%s"' % (
                legacy_id,
                title,
                source,
                author,
                created,
                doc_type,
            )
            if not options["inspect"]:
                self.stdout.write(doc_str)

            body = body.replace("\u2019", "'")
            body = body.replace("<br />", "\n")
            body = body.replace("</p>", "\n")
            body = strip_tags(body)
            summary = strip_tags(summary)
            title = strip_tags(title)

            newbody = ""
            paras = body.split("&nbsp;\n\n")
            for idx, para in enumerate(paras):
                para = para.strip()
                para = para.replace("&nbsp;", " ")
                if idx != 0:
                    para = " ".join(para.splitlines())
                if para:
                    # print('Paragraph %d\n\n%s\n' % (idx, para))
                    newbody = f"{newbody}\n\n{para}"
            # print(newbody)

            shebang = (
                "sudo -u %s wp post create \
                --post_content=\"%s\" \
                --post_date='%s 18:00:00' \
                --post_title=\"%s\" \
                --post_status=Publish \
                --post_excerpt=\"%s\" \
                --user='%s' \
                --post_category=['%s'] \
                --post_mime_type='text/html' \
                --path='%s' \
                --url='%s'"
                % (
                    shell_user,
                    newbody,
                    created,
                    title,
                    summary,
                    author,
                    doc_type,
                    wordpress_path,
                    url,
                )
            )

            if not options["inspect"]:
                try:
                    out = subprocess.check_output(
                        shebang, shell=True, stderr=subprocess.STDOUT
                    )
                    # out is bytes
                    out = str(out, "utf-8")
                    for line in out.splitlines():
                        print(line)
                except subprocess.CalledProcessError as e:
                    print(f"{shebang}: {str(e.output, 'utf-8')}")
                    fail_count = fail_count + 1
                    failed_docs.append(doc_str)
                    continue

            if doc_type not in doc_types:
                doc_types.append(doc_type)
            if author not in authors:
                authors.append(author)

        if options["inspect"]:

            body = body.replace("\u2019", "'")
            body = strip_tags(body)
            newbody = ""
            paras = body.split("&nbsp;\n\n")
            for idx, para in enumerate(paras):
                para = para.strip()
                para = para.replace("&nbsp;", " ")
                if idx != 0:
                    para = " ".join(para.splitlines())
                if para:
                    if options["verbose"]:
                        self.stdout.write(
                            "\nParagraph %d\n\n%s\n" % (idx, para)
                        )
                    newbody = f"{newbody}\n\n{para}"

            self.stdout.write(f"doc types: {doc_types}")
            self.stdout.write(f"Authors: {sorted(authors)}")

            for author in authors:
                first_name = author.split(" ")[0].lower()
                made_up_email = f"{first_name}@bogus-domain.org"
                # print(made_up_email)
                # wp user create bob bob@example.com --role=author
                shebang = (
                    'sudo -u adelayde wp user create "%s" "%s" \
                    --role=editor \
                    --porcelain \
                    --path=%s --url=%s'
                    % (author, made_up_email, wordpress_path, url)
                )
                self.stdout.write(f"Creating user {author}")
                try:
                    out = subprocess.check_output(
                        shebang, shell=True, stderr=subprocess.STDOUT
                    )
                    # out is bytes
                    out = str(out, "utf-8")
                    for line in out.splitlines():
                        print(line)
                except subprocess.CalledProcessError as e:
                    print(f"{shebang}: {str(e.output, 'utf-8')}")
                    continue

            for doc_type in doc_types:
                # wp term create category Apple
                shebang = (
                    'sudo -u adelayde wp term create category "%s" \
                    --path=%s --url=%s'
                    % (doc_type, wordpress_path, url)
                )
                self.stdout.write(f"Creating category {doc_type}")
                try:
                    out = subprocess.check_output(
                        shebang, shell=True, stderr=subprocess.STDOUT
                    )
                    # out is bytes
                    out = str(out, "utf-8")
                    for line in out.splitlines():
                        print(line)
                except subprocess.CalledProcessError as e:
                    print(f"{shebang}: {str(e.output, 'utf-8')}")
                    continue

        else:
            self.stdout.write(
                self.style.SUCCESS(f"{len(documents)} documents considered")
            )
            if fail_count:
                self.stdout.write(
                    self.style.WARNING(
                        "%d documents imports failed" % fail_count
                    )
                )
                for failed_doc in failed_docs:
                    self.stdout.write(self.style.WARNING(failed_doc))

        db.close()

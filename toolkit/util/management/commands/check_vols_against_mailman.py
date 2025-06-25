import os.path
import subprocess
import urllib
from django.core.management.base import BaseCommand

from toolkit.members.models import Volunteer

server_default = "cubecinema.com"
list_default = "volunteers"
mailman_api = "mailman-subscriber.py"


class Command(BaseCommand):
    help = "Match active volunteers against mailman volunteers list"

    def _get_mailman_vols(self):
        vols = []
        path, filename = os.path.split(__file__)

        server = input(
            f"Enter name of server that mailman is running on [{server_default}]: "
        )
        if not server:
            server = server_default
        vol_list = input(f"Enter name of mailman list [{list_default}]: ")
        if not vol_list:
            vol_list = list_default
        list_pass = input("Enter mailing list password: ")
        if not list_pass:
            self.stdout.write(
                self.style.WARNING("Mailing list password cannot be blank")
            )
            return vols

        args = f"{server} {vol_list} {list_pass}"
        shebang = f"python2 {os.path.join(path, mailman_api)} {args}"

        try:
            out = subprocess.check_output(
                shebang, shell=True, stderr=subprocess.STDOUT
            )
            # out is bytes
            out = str(out, "utf-8")
            for line in out.splitlines():
                # vols = (Volunteer.objects.filter(active=True)
                # self.stdout.write(self.style.SUCCESS(line))
                vols.append(urllib.parse.unquote_plus(line.rstrip()))
            self.stdout.write(
                self.style.SUCCESS(f"\n{len(vols)} vols found in mailman")
            )
            return vols
        except subprocess.CalledProcessError as e:
            self.stdout.write(
                self.style.ERROR(f"{shebang}\n{str(e.output, 'utf-8')}")
            )

    def _readfile(self, filename):
        """Unused - read vols from a file"""

        vols = []

        with open(filename) as fp:
            vols = [urllib.parse.unquote_plus(line.rstrip()) for line in fp]

        return vols

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            "--verbose",
            action="store_true",
            dest="verbose",
            help="Show more detail",
        )

    def handle(self, *args, **options):

        mmvols = self._get_mailman_vols()
        # mmvols = self._readfile(vols_file)
        if not mmvols:
            self.stdout.write(
                self.style.WARNING("No volunteers returned by mailman")
            )
            return

        vols = Volunteer.objects.filter(active=True).order_by("member__name")

        self.stdout.write(
            self.style.SUCCESS(f"{len(vols)} active volunteers to check\n")
        )

        self.stdout.write(
            "Checking volunteers for a matching email in mailman\n\n"
        )

        for vol in vols:
            if vol.member.email.lower() in mmvols:
                if options["verbose"]:
                    self.stdout.write(
                        self.style.SUCCESS(f"{vol.member} found in mailman")
                    )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"{vol.member} <{vol.member.email}> not found in mailman"
                    )
                )

        self.stdout.write(
            "\nChecking mailman for a matching email in volunteers\n\n"
        )

        for mmvol in mmvols:
            matched = Volunteer.objects.filter(member__email=mmvol).filter(
                active=True
            )
            if matched:
                if len(matched) > 1:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Duplicate entry in vols database found for {mmvol}"
                        )
                    )
                    for match in matched:
                        self.stdout.write(
                            f"{match.member.name} <{match.member.email}>"
                        )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"{mmvol} not found in volunteers database"
                    )
                )
                # Try again, to see if retired
                matched = Volunteer.objects.filter(member__email=mmvol)
                if matched:
                    self.stdout.write("Found retired volunteer")
                    for match in matched:
                        self.stdout.write(
                            f"{match.member.name} <{match.member.email}>"
                        )

        self.stdout.write(self.style.SUCCESS("\nChecks complete\n"))

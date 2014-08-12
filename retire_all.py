from toolkit.members.models import Volunteer

active_vols = Volunteer.objects.all().filter(active=True)
print "Retiring {0} volunteers".format(len(active_vols))
for volunteer in active_vols:
    print volunteer.member.name
    volunteer.active = False
    volunteer.save()


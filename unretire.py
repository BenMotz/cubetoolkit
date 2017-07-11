import csv
from toolkit.members.models import Volunteer

FILENAME = "volunteerlist.csv"


def load_data(filename):
    data = []
    with open(filename, "rt") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) == 3:
                data.append(row)
    return data


def try_get_volunteer_by_name(name):
    try:
        return Volunteer.objects.get(member__name__iexact=name)
    except Volunteer.DoesNotExist:
        return None


def try_get_volunteer_by_email(email):
    try:
        return Volunteer.objects.get(member__email__iexact=email)
    except Volunteer.MultipleObjectsReturned:
        print "Multiple volunteers with the same email address: {0}".format(email)
    except Volunteer.DoesNotExist:
        pass

    return None


def get_volunteer_objects(volunteers):
    results = []
    errors = []

    for vol_rec in volunteers:
        src_name = vol_rec[0] + " " + vol_rec[1]
        src_email = vol_rec[2]

        vol = try_get_volunteer_by_name(src_name)

        if not vol and src_email:
            vol = try_get_volunteer_by_email(src_email)

        if vol:
            results.append(vol)
        else:
            errors.append(vol_rec)

    return results, errors


def unretire(volunteers):
    for v in volunteers:
        v.active = True
        v.save()


def main():
    print "Trying to read {0}".format(FILENAME)
    volunteer_list = load_data(FILENAME)

    print "Attempting to unretire {0} volunteers".format(len(volunteer_list))
    volunteers, errors = get_volunteer_objects(volunteer_list)

    if errors:
        print "\nAborting: couldn't match the following entries in the source file to volunteer records:"
        print "\n".join([str(e) for e in errors])
        exit(1)

    unretire(volunteers)


if __name__ == "__main__":
    main()

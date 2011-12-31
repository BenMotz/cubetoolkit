#!/usr/bin/python
import os
import logging

import diary.models

FORMATS_PATH="./formats"


def create_event_types(event_types):
    for e_type, roles in event_types.iteritems():
        e_type_o, created = diary.models.EventType.objects.get_or_create(name=e_type)
        if created:
            logging.info("Created event type: %s", e_type)
            e_type_o.shortname = e_type
            e_type_o.save()
        assigned_roles_keys = set([r['pk'] for r in e_type_o.roles.values('pk')])
        for role in roles:
            role = diary.models.Role.objects.get(name=role)
            if role.pk not in assigned_roles_keys:
                logging.info("Adding role %s to %s", role, e_type)
                e_type_o.roles.add(role)

def load_event_templates(path_to_formats):
    def clean(string):
        return string.strip().replace("_", " ")

    type_index = {}
    for root, dirs, files in os.walk(path_to_formats):
        for event_type in files:
            role_list = []
            with open(os.path.join(root, event_type), "r") as role_list_file:
                for line in role_list_file:
                    role_list.append(clean(line))
            type_index[clean(event_type)] = role_list
    logging.info("Loaded %d event types: %s", len(type_index), ",".join(type_index.keys()))
    return type_index


def main():
    type_index = load_event_templates(FORMATS_PATH)
    create_event_types(type_index)

if __name__ == "__main__":
    main()

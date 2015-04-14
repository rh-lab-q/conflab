from django.db.models.signals import post_syncdb
from django.contrib.auth.models import Permission, Group
from django.db.utils import IntegrityError

import confla.models

def add_groups(sender, verbosity, **kwargs):
    try:
        volunteers = Group(name='Volunteers')
        volunteers.save()
        if verbosity > 2:
            print("Confla: " + volunteers.name + " added")
    except IntegrityError:

        if verbosity > 1:
            print("Confla: Group " + volunteers.name + " already exists.")
    try:
        speakers = Group(name='Speakers')
        speakers.save()
        if verbosity > 2:
            print("Confla: " + speakers.name + " added")
    except IntegrityError:

        if verbosity > 1:
            print("Confla: Group " + speakers.name + " already exists.")
    try:
        reviewers = Group(name='Reviewers')
        reviewers.save()
        if verbosity > 2:
            print("Confla: " + reviewers.name + " added")
    except IntegrityError:
        if verbosity > 1:
            print("Confla: Group " + reviewers.name + " already exists.")

    try:
        organizers = Group(name='Organizers')
        organizers.save()
        if verbosity > 2:
            print("Confla: " + organizers.name + " added")
    except IntegrityError:
        if verbosity > 1:
            print("Confla: Group " + organizers.name + " already exists.")

    if verbosity > 1:
        print("Confla: Adding permissions for groups.")
    volunteers = Group.objects.get(name="Volunteers")
    volunteers.permissions.add(Permission.objects.get(codename="can_volunteer"))
    organizers = Group.objects.get(name="Organizers")
    organizers.permissions.add(Permission.objects.get(codename="can_organize"))

# check for all our view permissions after a syncdb
post_syncdb.connect(add_groups, sender=confla.models)

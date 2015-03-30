from django.db.models.signals import post_syncdb
from django.contrib.auth.models import Permission, Group
from django.db.utils import IntegrityError

import confla.models

def add_groups(sender, verbosity, **kwargs):
    try:
        volunteers = Group(name='Volunteers')
        volunteers.save()
        if verbosity > 2:
            print("Confla: Volunteers added")
    except IntegrityError:

        if verbosity > 1:
            print("Confla: Group Reviewers already exists.")
    try:
        speakers = Group(name='Speakers')
        speakers.save()
        if verbosity > 2:
            print("Confla: Speakers added")
    except IntegrityError:

        if verbosity > 1:
            print("Confla: Group Reviewers already exists.")
    try:
        reviewers = Group(name='Reviewers')
        reviewers.save()
        if verbosity > 2:
            print("Confla: Reviewers added")
    except IntegrityError:
        if verbosity > 1:
            print("Confla: Group Reviewers already exists.")

    if verbosity > 1:
        print("Confla: Adding permissions for groups.")
    volunteers = Group.objects.get(name="Volunteers")
    volunteers.permissions.add(Permission.objects.get(codename="can_volunteer"))

# check for all our view permissions after a syncdb
post_syncdb.connect(add_groups, sender=confla.models)

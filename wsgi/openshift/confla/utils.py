import os

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _

#TODO: security++, more file types?
def validate_papers(value):
    extensions = ['.pdf']
    ext = os.path.splitext(value.name)[1]
    if not ext in extensions:
        raise ValidationError(_("Unsupported file type. File must be a pdf or ... file."))


# a helper function for renaming uploaded files
def conf_rename_and_return_path(path):
    def wrapper(instance, filename):
        ext = filename.split('.')[-1]
        filename = '{}.{}'.format(instance.url_id, ext)
        return os.path.join(path, filename)
    return wrapper

# a helper function for renaming uploaded avatars
def user_rename_and_return_path(path):
    def wrapper(instance, filename):
        ext = filename.split('.')[-1]
        filename = '{}.{}'.format(instance.username, ext)
        return os.path.join(path, filename)
    return wrapper

# a helper function for renaming uploaded papers
def paper_rename_and_return_path(path):
    def wrapper(instance, filename):
        ext = filename.split('.')[-1]
        filename = '{}.{}'.format(instance.user.username, ext)
        return os.path.join(path, filename)
    return wrapper

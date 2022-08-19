import os

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.utils.deconstruct import deconstructible

@deconstructible
class ConfRenamePath(object):

    def __init__(self, path):
        self.path = path

    def __call__(self, instance, filename):
        ext = filename.split('.')[-1]
        filename = '{}.{}'.format(instance.url_id, ext)
        return os.path.join(self.path, filename)

@deconstructible
class UserRenamePath(object):

    def __init__(self, path):
        self.path = path

    def __call__(self, instance, filename):
        ext = filename.split('.')[-1]
        filename = '{}.{}'.format(instance.username, ext)
        return os.path.join(self.path, filename)

@deconstructible
class PaperRenamePath(object):

    def __init__(self, path):
        self.path = path

    def __call__(self, instance, filename):
        ext = filename.split('.')[-1]
        filename = '{}.{}'.format(instance.user.username, ext)
        return os.path.join(path, filename)

splash_rename_and_return_path = ConfRenamePath('splash/')
icon_rename_and_return_path = ConfRenamePath('icon/')
user_rename_and_return_path = UserRenamePath('avatars/')
paper_rename_and_return_path = PaperRenamePath('papers/')

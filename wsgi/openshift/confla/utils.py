import os

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

from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404

from confla.models import Conference

def get_conf_or_404(url_id):
    try:
        conf = Conference.objects.get(url_id=url_id)
    except ObjectDoesNotExist:
        raise Http404
    return conf

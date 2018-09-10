from django.conf.urls import include, url

from django.contrib import admin

from django.conf import settings
from django.contrib.auth import views as auth_views

admin.autodiscover()

urlpatterns = [
    url(r'^', include('confla.urls', namespace='confla')),
#    url(r'^$', core_views.home, name='home'),
    url(r'^login/$', auth_views.login, name='login'),
    url(r'^logout/$', auth_views.logout, name='logout'),
    url(r'^oauth/', include('social_django.urls', namespace='social')),  # <--
    url(r'^admin/', admin.site.urls),
]

urlpatterns += [
    url(r'^captcha/', include('captcha.urls')),
]

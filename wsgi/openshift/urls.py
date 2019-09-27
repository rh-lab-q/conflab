from django.conf.urls import include, url

from django.contrib import admin

from django.conf import settings
from django.contrib.auth import views as auth_views

admin.autodiscover()

urlpatterns = [
    url(r'^', include('confla.urls')),
#    url(r'^', include('confla.urls', namespace='confla')),


#    url(r'^$', core_views.home, name='home'),
    url(r'^login/$', auth_views.LoginView, name='login'),
    url(r'^logout/$', auth_views.LogoutView, name='logout'),
#    url(r'^oauth/', include('social_django.urls', namespace='social')),  # <--
#    url(r'^admin/', include('admin.site.urls')),
]

urlpatterns += [
    url(r'^captcha/', include('captcha.urls')),
]

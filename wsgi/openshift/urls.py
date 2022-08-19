from django.conf.urls import include
from django.urls import path, re_path

from django.contrib import admin

from django.conf import settings
from django.contrib.auth import views as auth_views

admin.autodiscover()

urlpatterns = [
    re_path(r'^', include('confla.urls')),


#    re_path(r'^$', core_views.home, name='home'),
    re_path(r'^login/$', auth_views.LoginView.as_view(), name='login'),
    re_path(r'^logout/$', auth_views.LogoutView.as_view(), name='logout'),
#    re_path(r'^oauth/', include('social_django.urls', namespace='social')),  # <--
#    re_path(r'^admin/', include('admin.site.urls')),
    re_path('admin/', admin.site.urls),
]

urlpatterns += [
    re_path(r'^captcha/', include('captcha.urls')),
]

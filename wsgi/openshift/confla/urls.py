from django.conf.urls import patterns, url
from django.conf.urls.static import static
from django.conf import settings

from confla import views

urlpatterns = patterns('',
        url(r'^$', views.AboutView.as_view(), name='index'),
        url(r'^about/$', views.AboutView.as_view(), name='about'),
        url(r'^sched/$', views.ScheduleView.as_view(), name='schedule'),
        url(r'^login/$', views.LoginView.as_view(), name='login'),
        url(r'^logout/$', views.LoginView.logout, name='logout'),
        url(r'^process/$', views.LoginView.check_login, name='loginx'),
        url(r'^users/$', views.UserView.as_view(), name='users'),
)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

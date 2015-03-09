from django.conf.urls import patterns, url

from confla import views

urlpatterns = patterns('',
        url(r'^$', views.AboutView.as_view(), name='index'),
        url(r'^about/$', views.AboutView.as_view(), name='about'),
        url(r'^sched/$', views.ScheduleView.as_view(), name='schedule'),
        url(r'^login/$', views.LoginView.as_view(), name='login'),
        url(r'^users/$', views.UserView.as_view(), name='users'), # warning - placeholder!
        #url(r'^(?P<username>\w+)/(?P<password>\w+)/$', views.check_psswd, name='loginx'),
)

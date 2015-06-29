from django.conf.urls import patterns, url, include
from django.conf.urls.static import static
from django.conf import settings

from confla import views

urlpatterns = patterns('',
        url(r'^$', views.AboutView.as_view(), name='index'),
        url(r'^about/$', views.AboutView.as_view(), name='about'),
        url(r'^sched/$', views.ScheduleView.my_view, name='schedule'),
        url(r'^sched/list$', views.ScheduleView.list_view, name='listsched'),
        url(r'add_rooms/$', views.AddRoomsView.view_form, name='add_rooms'),
        url(r'^admin/sched/$', views.TimetableView.view_timetable, name='adminsched'),
        url(r'^admin/sched/saveTable/$', views.TimetableView.save_timetable, name='saveTable'),
        url(r'^admin/sched/saveEvent/$', views.TimetableView.save_event, name='saveEvent'),
        url(r'^login/$', views.LoginView.my_view, name='login'),
        url(r'^logout/$', views.LoginView.logout, name='logout'),
        url(r'^process/$', views.LoginView.auth_and_login, name='process_login'),
        url(r'^users/$', views.UserView.my_view, name='users'),
        url(r'^users/reg_talk/$', views.UserView.send_paper, name='user_reg_talk'),
        url(r'^users/add_email/$', views.UserView.add_email, name='user_add_email'),
        url(r'^users/delete_email/$', views.UserView.delete_email, name='user_delete_email'),
        url(r'users/profile/$', views.UserView.view_profile, name='profile'),
        url(r'users/volunteer/$', views.VolunteerView.my_view, name='volunteer'),
        url(r'^register/$', views.RegisterView.user_register, name='register'),
        url(r'^thanks/$', views.RegisterView.as_view(), name='thanks'),
        url(r'^reg_talk/$', views.RegisterView.send_paper, name='reg_talk'),
       # url(r'^notlogged/$', views.UserView.not_logged, name='notlogged'),

        url(r'^i18n/', include('django.conf.urls.i18n'), name='set_language'),
)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

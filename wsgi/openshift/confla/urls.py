from django.conf.urls import patterns, url, include
from django.conf.urls.static import static
from django.conf import settings

from confla import views

urlpatterns = patterns('',
        url(r'^$', views.IndexView.my_view, name='index'),
        url(r'^(?P<url_id>\w+)/$', views.AboutView.my_view, name='splash'),
        url(r'^(?P<url_id>\w+)/about/$', views.AboutView.my_view, name='about'),
        url(r'^(?P<url_id>\w+)/sched/$', views.ScheduleView.my_view, name='schedule'),
        url(r'^(?P<url_id>\w+)/sched/list/$', views.ScheduleView.list_view, name='listsched'),
        url(r'^(?P<url_id>\w+)/config/$', views.RoomConfView.slot_view, name='conf_rooms'),
        url(r'^(?P<url_id>\w+)/config/save/$', views.RoomConfView.save_config, name='rooms_conf_save'),
        url(r'^(?P<url_id>\w+)/sched/edit/$', views.TimetableView.view_timetable, name='adminsched'),
        url(r'^(?P<url_id>\w+)/sched/edit/saveTable/$', views.TimetableView.save_timetable, name='saveTable'),
        url(r'^(?P<url_id>\w+)/sched/edit/saveEvent/$', views.TimetableView.save_event, name='saveEvent'),
        url(r'^(?P<url_id>\w+)/sched/edit/popover/$', views.EventView.get_admin_popover, name='eventPop_admin'),
        url(r'add_rooms/$', views.AddRoomsView.view_form, name='add_rooms'),
        url(r'^admin/eventlist/$', views.EventEditView.event_view, name='editEvent'),
        url(r'^admin/eventlist/(?P<id>\d+)/$', views.EventEditView.event_view, name='editEvent'),
        url(r'^admin/eventlist/editEvent/(?P<id>\d+)/$', views.EventEditView.event_save, name='editEvent2'),
        url(r'^events/popover/$', views.EventView.get_popover, name='eventPop'),
        url(r'^events/modal/$', views.EventEditView.event_modal, name='eventMod'),
        url(r'^login/$', views.LoginView.my_view, name='login'),
        url(r'^logout/$', views.LoginView.logout, name='logout'),
        url(r'^process/$', views.LoginView.auth_and_login, name='process_login'),
        url(r'^users/$', views.UserView.my_view, name='users'),
        url(r'^(?P<url_id>\w+)/cfp/$', views.CfpView.save_form_and_register, name='cfp'),
        url(r'^users/add_email/$', views.UserView.add_email, name='user_add_email'),
        url(r'^users/delete_email/$', views.UserView.delete_email, name='user_delete_email'),
        url(r'users/profile/$', views.UserView.view_profile, name='profile'),
        url(r'users/volunteer/$', views.VolunteerView.my_view, name='volunteer'),
        url(r'^register/$', views.RegisterView.user_register, name='register'),
        url(r'^thanks/$', views.RegisterView.as_view(), name='thanks'),
        #url(r'^reg_talk/$', views.RegisterView.save_form_and_register, name='reg_talk'),
        url(r'^export/m_app$', views.ExportView.m_app, name='export_mapp'),
        #url(r'^notlogged/$', views.UserView.not_logged, name='notlogged'),
        url(r'^test/$', views.TestingView.event_view, name='test'),

        url(r'^i18n/', include('django.conf.urls.i18n'), name='set_language'),
)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

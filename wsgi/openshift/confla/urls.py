from django.conf.urls import url, include
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from django.urls import path

from confla import views

app_name = "confla"

urlpatterns = [
        path('admin/', admin.site.urls),

        url(r'^$', views.IndexView.my_view, name='index'),
        url(r'add_rooms/$', views.AddRoomsView.view_form, name='add_rooms'),
        url(r'^events/popover/$', views.EventView.get_popover, name='eventPop'),
        url(r'^events/modal/$', views.EventEditView.event_modal, name='eventMod'),
        url(r'^login/$', views.LoginView.my_view, name='login'),
        url(r'^logout/$', views.LoginView.logout, name='logout'),
        url(r'^process/$', views.LoginView.auth_and_login, name='process_login'),
        url(r'^users/$', views.UserView.my_view, name='users'),
        url(r'^user/(?P<url_username>\w+)/profile/$', views.UserView.view_profile, name='profile'),
        url(r'^user/(?P<url_username>\w+)/delete_mail/(?P<id>\d+)/', views.UserView.delete_email, name='delete_email'),
        url(r'^user/(?P<url_username>\w+)/set_primary_mail/(?P<id>\d+)/', views.UserView.set_email_primary, name='set_primary_email'),
        url(r'^user/volunteer/$', views.VolunteerView.my_view, name='volunteer'),
        url(r'^register/$', views.RegisterView.user_register, name='register'),
        url(r'^reset_password/$', views.RegisterView.reset_password, name='reset_password'),
        url(r'^reset_password2/(?P<email_address>[^/]+)/(?P<token>[^/]+)$', views.RegisterView.reset_password2, name='reset_password2'),
        #url(r'^reg_talk/$', views.RegisterView.save_form_and_register, name='reg_talk'),
        #url(r'^notlogged/$', views.UserView.not_logged, name='notlogged'),
        url(r'^i18n/', include('django.conf.urls.i18n'), name='set_language'),
        url(r'^(?P<url_id>\w+)/$', views.AboutView.splash_view, name='splash'),
        url(r'^(?P<url_id>\w+)/cfp/$', views.CfpView.save_form_and_register, name='cfp'),
        url(r'^(?P<url_id>\w+)/about/$', views.AboutView.splash_view, name='about'),
        url(r'^(?P<url_id>\w+)/events/$', views.EventView.event_list, name='event_list'),
        url(r'^(?P<url_id>\w+)/places/$', views.PlacesView.osm, name='places'),
        url(r'^(?P<url_id>\w+)/about/(?P<page>\w+)$', views.PagesView.content, name='pages'),
        url(r'^(?P<url_id>\w+)/speakers/grid/$', views.UserView.speaker_grid, name='speaker_grid'),
        url(r'^(?P<url_id>\w+)/speakers/list/$', views.UserView.speaker_list, name='speaker_list'),
        url(r'^(?P<url_id>\w+)/sched/$', views.ScheduleView.my_view, name='schedule'),
        url(r'^(?P<url_id>\w+)/sched/list/$', views.ScheduleView.list_view, name='listsched'),
        url(r'^(?P<url_id>\w+)/sched/list/(?P<id>\d+)/$', views.ScheduleView.list_view, name='listschedTag'),
        url(r'^(?P<url_id>\w+)/config/$', views.RoomConfView.slot_view, name='conf_rooms'),
        url(r'^(?P<url_id>\w+)/config/save/$', views.RoomConfView.save_config, name='rooms_conf_save'),
        url(r'^(?P<url_id>\w+)/export/m_app/$', views.ExportView.m_app, name='export_mapp'),
        url(r'^(?P<url_id>\w+)/export/csv/$', views.ExportView.csv, name='export_csv'),
        url(r'^org/admin/geo_icons/$', views.IconsView.table, name='geo_icons'),
        url(r'^org/admin/geo_points/$', views.PlacesView.table, name='geo_points'),
        url(r'^org/admin/stats/$', views.AdminView.dashboard, name='org_dashboard'),
        url(r'^org/admin/newconf/$', views.ConferenceView.create_conf, name='create_conf'),
        url(r'^org/admin/createroom/$', views.ConferenceView.create_room, name='create_room'),
        url(r'^org/admin/createtag/$', views.EventEditView.create_event_tag, name='create_event_tag'),
        url(r'^org/admin/saveconf/$', views.ConferenceView.save_conf, name='save_conf'),
        url(r'^org/admin/users/$', views.AdminView.users, name='org_users'),
        url(r'^org/admin/$', views.AdminView.conf_list, name='org_conf_list'),
        url(r'^export/conference_list/$', views.ExportView.conf_list, name='conf_list_export'),
        url(r'^(?P<url_id>\w+)/admin/$', views.AdminView.dashboard, name='dashboard'),
        url(r'^(?P<url_id>\w+)/admin/conf/edit/$', views.ConferenceView.edit_conf, name='edit_conf'),
        url(r'^(?P<url_id>\w+)/admin/saveconf/$', views.ConferenceView.save_conf, name='save_conf_urlid'),
        url(r'^(?P<url_id>\w+)/admin/pages/$', views.PagesView.pages_list, name='admin_pages'),
        url(r'^(?P<url_id>\w+)/admin/page/(?P<page>\d+)/edit/$', views.PagesView.edit_page, name='edit_page'),
        url(r'^(?P<url_id>\w+)/admin/page/(?P<page>\d+)/save/$', views.PagesView.save_page, name='save_page'),
        url(r'^(?P<url_id>\w+)/admin/users/$', views.AdminView.users, name='speakers'),
        url(r'^(?P<url_id>\w+)/admin/sched/edit/$', views.TimetableView.view_timetable, name='adminsched'),
        url(r'^(?P<url_id>\w+)/admin/sched/edit/saveTable/$', views.TimetableView.save_timetable, name='saveTable'),
        url(r'^(?P<url_id>\w+)/admin/sched/edit/saveEvent/$', views.TimetableView.save_event, name='saveEvent'),
        url(r'^(?P<url_id>\w+)/admin/sched/edit/popover/$', views.EventView.get_admin_popover, name='eventPop_admin'),
        url(r'^(?P<url_id>\w+)/admin/eventlist/$', views.EventEditView.event_view, name='editEvent'),
        url(r'^(?P<url_id>\w+)/admin/eventlist/(?P<id>\d+)/$', views.EventEditView.event_view, name='editEvent'),
        url(r'^(?P<url_id>\w+)/admin/eventlist/editEvent/(?P<id>\d+)/$', views.EventEditView.event_save, name='editEvent2'),
        url(r'^(?P<url_id>\w+)/admin/import/$', views.ImportView.import_view, name='import'),
        url(r'^(?P<url_id>\w+)/admin/import/json/$', views.ImportView.json_upload, name='json_import'),
        url(r'^(?P<url_id>\w+)/admin/export/$', views.ExportView.export_view, name='export'),
        url(r'^activate/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',views.RegisterView.activate_email , name='activate_email'),

    ]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

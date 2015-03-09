from django.shortcuts import render
from django.views import generic

class AboutView(generic.TemplateView):
    template_name = 'confla/about.html'

class ScheduleView(generic.TemplateView):
    template_name = 'confla/schedule.html'

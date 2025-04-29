from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
# Create your views here.

class HomeView(TemplateView):
    template_name = 'home/index.html'
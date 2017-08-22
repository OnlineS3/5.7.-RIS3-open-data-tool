"""Open Data Tool URL Configuration
The `urlpatterns` list routes URLs to views.
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.auth import views as auth_views

from OpenDataTool.views import *

urlpatterns = [
    # Development
    url(r'^admin/', admin.site.urls),
    url(r'^signup/$', signup, name='signup'),
    url(r'^login/$', auth_views.login, name='login'),
    url(r'^logout/$', auth_views.logout, {'next_page': '/about'}, name='logout'),

    url(r'^select2/', include('django_select2.urls')),

    # Application
    url(r'^about/$', about, name='about'),
    url(r'^guide/$', guidepage, name='guide'),
    url(r'^pdf/$', guide, name='pdf'),
    url(r'^related/$', related, name='related'),

    url(r'^search/$', search, name='search'),
    url(r'^results/$', results, name='results'),
    url(r'^projects/$', projects, name='projects'),
    url(r'^explorer/$', explorer, name='explorer'),

    url(r'^query/$', query, name='query'),
    url(r'^bookmarked/$', bookmarked, name='bookmarked'),

    # url(r'^init/$', init, name="init"),
    # url(r'^annotate/$', annotate, name="annotate"),

    # Base URL
    url(r'^$', about),
]

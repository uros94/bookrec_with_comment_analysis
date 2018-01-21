from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    url(r'^$', auth_views.login, name='login'),
    url(r'^signup/$', views.signup, name='signup'),
    url(r'^logout/$', auth_views.logout, {'next_page': '/'}, name='logout'),
    url(r'^home/$', views.home, name='home'),
    url(r'^home/(?P<idb>\d+)/book_like/$', views.book_like, name='book_like'),
    url(r'^home/(?P<idb>\d+)/book_dislike/$', views.book_dislike, name='book_dislike'),
    url(r'^home/(?P<idb>\d+)/$', views.book_detail, name='book_detail'),
]

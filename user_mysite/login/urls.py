from django.urls import path
from django.conf.urls import url, include
from login import views
import django.contrib.staticfiles.urls

urlpatterns = [
    url(r'^index/', views.index),
    url(r'^login/', views.login),
    url(r'^register/', views.register),
    url(r'^logout/', views.logout),
    url('^ajax_val/', views.ajax_val, name='ajax_val'),
    url(r'^confirm/$', views.user_confirm),
    # url(r'^',include(django.contrib.staticfiles.urls)),
]

# print('测试')
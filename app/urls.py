from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^home$', views.home, name='home'),
    url(r'^file/upload$', views.upload_file, name='upload_file'),
    url(r'^data/get$', views.get_data, name='get_data'),
    url(r'^outliers/detect$', views.detect_outliers, name='detect_outliers')
]
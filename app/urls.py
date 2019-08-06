from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^home$', views.home, name='home'),
    url(r'^file/upload$', views.upload_file, name='upload_file'),
    url(r'^data/get$', views.get_data, name='get_data'),
    url(r'^outliers/detect$', views.detect_outliers, name='detect_outliers'),
    url(r'^outliers/get$', views.get_outliers, name='get_outliers'),
    url(r'^outliers/treat$', views.treat_outliers, name='treat_outliers'),
    url(r'^status/update$', views.update_experiment_status, name='update_process_status'),
    url(r'^status/get$', views.get_experiment_status, name='get_experiment_status'),
    url(r'^file/download$', views.download_treated_file, name='download_treated_file')
]
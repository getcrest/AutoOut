from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^home$', views.home, name='home'),
    url(r'^file/upload$', views.upload_file, name='upload_file'),

    # Data related endpoints
    url(r'^data/get$', views.get_data, name='get_data'),
    url(r'^data/properties$', views.get_dataset_properties, name='get_dataset_properties'),
    url(r'^data/feature/delete$', views.add_feature, name='delete_feature'),
    url(r'^data/feature/add$', views.add_feature, name='add_feature'),

    # Detection and treatment related endpoints
    url(r'^outliers/detect$', views.detect_outliers, name='detect_outliers'),
    url(r'^outliers/get$', views.get_outliers, name='get_outliers'),
    url(r'^outliers/treat$', views.treat_outliers, name='treat_outliers'),
    url(r'^outliers/number$', views.get_no_outliers, name='get_no_outliers'),

    # Detection and treatment status endpoints
    url(r'^status/update$', views.update_experiment_status, name='update_process_status'),
    url(r'^status/get$', views.get_experiment_status, name='get_experiment_status'),

    # Download the treated file
    url(r'^file/download$', views.download_treated_file, name='download_treated_file')
]
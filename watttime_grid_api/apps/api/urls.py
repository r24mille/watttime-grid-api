from django.conf.urls import patterns, url, include
from rest_framework import routers
from apps.api import views

router = routers.DefaultRouter()

# Wire up our API using automatic URL routing.
urlpatterns = patterns('',
    url(r'^', include(router.urls)),
    url(r'^docs/', include('rest_framework_swagger.urls')),
    url(r'^balancing_authorities/$', views.BalancingAuthorityList.as_view(),
        name='balancingauthority-list'),
    url(r'^balancing_authorities/(?P<abbrev>[A-Z]+)/$', views.BalancingAuthorityDetail.as_view(),
        name='balancingauthority-detail'),
    url(r'^fuels/$', views.FuelTypeList.as_view(),
        name='fueltype-list'),
    url(r'^fuels/(?P<name>[a-z]+)/$', views.FuelTypeDetail.as_view(),
        name='fueltype-detail'),
    url(r'^datapoints/$', views.DataPointList.as_view(),
        name='datapoint-list'),
    url(r'^datapoints/(?P<pk>[0-9]+)/$', views.DataPointDetail.as_view(),
        name='datapoint-detail'),
    url(r'^fuel_carbon_intensities/$', views.FuelToCarbonList.as_view(),
        name='fueltocarbon-list'),
    url(r'^fuel_carbon_intensities/(?P<pk>[0-9]+)/$', views.FuelToCarbonList.as_view(),
        name='fueltocarbon-detail'),
)

from django.urls import path, include
from . import views

from .views import ClientCreateView, DetailedView
from rest_framework import routers

router = routers.DefaultRouter()
router.register('count', views.CountView)


urlpatterns = [
    #path('', include('count.urls'))
    path('api/', include(router.urls)),
    path('create/', ClientCreateView, name='create'),
    path('details/<str:name>/', DetailedView, name='detailedview')
]

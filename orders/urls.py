from django.urls import path
from . import views


urlpatterns = [
    path('place_order/',views.place_order,name='place_order'),
    path('create_charge/', views.create_charge, name='create_charge'),
    path ('order_completed/', views.order_completed, name='order_completed'),
]

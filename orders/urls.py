from django.urls import path
from . import views


urlpatterns = [
    path('place_order/',views.place_order,name='place_order'),
    path('payments/<int:order_id>/', views.payments, name='payments'),   
    path('complete-payment/<int:order_id>/', views.complete_payment, name='complete_payment'),
    path('order-complete/<int:order_id>/', views.order_complete, name='order_complete'),

] 
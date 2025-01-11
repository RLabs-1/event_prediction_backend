from django.urls import path
from .views.views import user_view
from .views import views

urlpatterns = [
    path('api/user/', user_view, name='user_view'),  # defining the route /api/user/ and mapping it to the user_view
    path('register/', views.user_register, name='user_register'),
]

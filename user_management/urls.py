from django.urls import path
from .views.views import user_view

urlpatterns = [
    path('api/user/', user_view, name='user_view'),  # defining the route /api/user/ and mapping it to the user_view
]

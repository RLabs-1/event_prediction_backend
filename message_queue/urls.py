from django.urls import path
from .views.views import (
    FcmSubscribeView,
    FcmUnsubscribeView
)


urlpatterns = [
    path("fcm/subscribe", FcmSubscribeView.as_view(), name="fcm-subscribe"),
    path("fcm/unsubscribe", FcmUnsubscribeView.as_view(), name="fcm-unsubscribe"),
]

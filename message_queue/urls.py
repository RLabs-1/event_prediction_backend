from django.urls import path
from .views.views import (
    FcmSubscribeView,
    FcmUnsubscribeView
)

from .views.fcm_views import RegisterFcmTokenView

app_name = 'message_queue'


urlpatterns = [
    path('fcm/register-token', RegisterFcmTokenView.as_view(), name='register-fcm-token'),
    path("fcm/subscribe", FcmSubscribeView.as_view(), name="fcm-subscribe"),
    path("fcm/unsubscribe", FcmUnsubscribeView.as_view(), name="fcm-unsubscribe"),
]

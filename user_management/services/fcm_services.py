# user_management/services/fcm_services.py

from core.models import UserFcmToken

def register_fcm_token(user, fcm_token, session_id):
    """
    Registers or updates the FCM token for a user-session pair.
    """
    obj, _ = UserFcmToken.objects.update_or_create(  #Check if the same user and session_id already exist, if yes it updates, if not it creates
        user=user,
        session_id=session_id,
        defaults={'fcm_token': fcm_token}
    )
    return obj

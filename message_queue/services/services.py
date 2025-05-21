import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
from loguru import logger

class FCMService:
    """Service to handle Firebase Cloud Messaging notifications"""
    
    @classmethod
    def initialize_firebase(cls):
        """Initialize Firebase admin SDK if not already initialized"""
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
                firebase_admin.initialize_app(cred)
                logger.info("Firebase app initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase app: {str(e)}")
            raise Exception(f"Failed to initialize Firebase app: {str(e)}")
    
    @classmethod
    def send(cls, topic_name, notification):
        """
        Send a notification to a specific Firebase topic
        
        Args:
            topic_name (str): The name of the Firebase topic to send to
            notification (dict): Dictionary containing notification data with
                                'title' and 'body' keys and optional 'data' key
                                
        Returns:
            str: The message ID from FCM server if successful
        """
        try:
            # Make sure Firebase is initialized
            cls.initialize_firebase()
            
            # Validate inputs
            if not isinstance(topic_name, str) or not topic_name:
                raise ValueError("Topic name must be a non-empty string")
            
            if not isinstance(notification, dict):
                raise ValueError("Notification must be a dictionary")
            
            if 'title' not in notification or 'body' not in notification:
                raise ValueError("Notification must contain 'title' and 'body' keys")
            
            # Create a message
            message = messaging.Message(
                notification=messaging.Notification(
                    title=notification['title'],
                    body=notification['body'],
                ),
                topic=topic_name,
                # Include additional data if provided
                data=notification.get('data', {})
            )
            
            # Send the message
            response = messaging.send(message)
            logger.info(f"Notification sent successfully to topic '{topic_name}', message_id: {response}")
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to send notification to topic '{topic_name}': {str(e)}")
            raise Exception(f"Failed to send notification: {str(e)}")
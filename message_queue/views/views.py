from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from firebase_admin import messaging
from core.models import UserFcmToken
from rest_framework.exceptions import NotFound
from firebase_admin.exceptions import FirebaseError
from django.conf import settings
from drf_spectacular.utils import extend_schema

class FcmSubscribeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["message_queue"],
        description="Subscribe the authenticated user's FCM token(s) to a given topic.",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "topicName": {
                        "type": "string",
                        "description": "Name of the topic to subscribe to."
                    }
                },
                "required": ["topicName"]
            }
        },
        responses={
            200: {
                "description": "Successfully subscribed to the topic.",
                "content": {
                    "application/json": {
                        "example": {
                            "message": "Subscribed to myTopic",
                            "successCount": 1,
                            "failureCount": 0
                        }
                    }
                }
            },
            400: {"description": "Missing topicName or invalid input."},
            401: {"description": "Authentication credentials were not provided or are invalid."},
            403: {"description": "Permission denied."},
            404: {"description": "No FCM token found for user."},
            500: {"description": "Firebase error or unexpected server error."}
        }
    )
    def post(self, request):
        try:
            topic_name = request.data.get("topicName")
            if not topic_name:
                raise ValueError("Missing topicName")

            user = request.user
            tokens = UserFcmToken.objects.filter(user=user).values_list("fcm_token", flat=True)

            if not tokens:
                raise NotFound("No FCM token found for user")

            response = messaging.subscribe_to_topic(list(tokens), topic_name)

            return Response({
                "message": f"Subscribed to {topic_name}",
                "successCount": response.success_count,
                "failureCount": response.failure_count,
            }, status=status.HTTP_200_OK)



        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except NotFound as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except FirebaseError as e:
            return Response({"error": f"Firebase error: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except PermissionError as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)

        except Exception as e:
            return Response({"error": f"Unexpected error: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class FcmUnsubscribeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["message_queue"],
        description="Unsubscribe the authenticated user's FCM token(s) from a given topic.",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "topicName": {
                        "type": "string",
                        "description": "Name of the topic to unsubscribe from."
                    }
                },
                "required": ["topicName"]
            }
        },
        responses={
            200: {
                "description": "Successfully unsubscribed from the topic.",
                "content": {
                    "application/json": {
                        "example": {
                            "message": "Unsubscribed from myTopic",
                            "successCount": 1,
                            "failureCount": 0
                        }
                    }
                }
            },
            400: {"description": "Missing topicName or invalid input."},
            401: {"description": "Authentication credentials were not provided or are invalid."},
            403: {"description": "Permission denied."},
            404: {"description": "No FCM token found for user."},
            500: {"description": "Firebase error or unexpected server error."}
        }
    )
    def post(self, request):
        try:
            topic_name = request.data.get("topicName")
            if not topic_name:
                raise ValueError("Missing topicName")

            user = request.user
            tokens = UserFcmToken.objects.filter(user=user).values_list("fcm_token", flat=True)

            if not tokens:
                raise NotFound("No FCM token found for user")

            response = messaging.unsubscribe_from_topic(list(tokens), topic_name)

            return Response({
                "message": f"Unsubscribed from {topic_name}",
                "successCount": response.success_count,
                "failureCount": response.failure_count,
            }, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except NotFound as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except FirebaseError as e:
            return Response({"error": f"Firebase error: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except PermissionError as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)

        except Exception as e:
            return Response({"error": f"Unexpected error: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


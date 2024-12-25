#defining the view for the api user
from django.shortcuts import render
from django.http import JsonResponse

def user_view(request):
    #A function that handles requests to /api/user
    #I still don't know what specific data we need, so meanwhile I used these, but I can replace it later with actual database queries

    user_data = {
        'username': 'example_user',
        'email': 'user@example.com'
    }
    return JsonResponse(user_data)


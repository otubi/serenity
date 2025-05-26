from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import logout
from .models import APIKey
import secrets
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth import authenticate, login
import requests
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json


def home(request):
    """
    Public homepage for unauthenticated users.
    """
    return render(request, 'home.html')


@login_required
def dashboard(request):
    """
    Dashboard for authenticated users to view or generate their API key.
    """
    try:
        api_key = APIKey.objects.get(user=request.user)
    except ObjectDoesNotExist:
        api_key = None

    return render(request, 'dashboard.html', {'api_key': api_key})


@login_required
def generate_api_key(request):
    """
    Generate a new API key for the user if it doesn't exist,
    or regenerate it if already created.
    """
    api_key, created = APIKey.objects.get_or_create(user=request.user)

    # Always regenerate the key
    api_key.key = secrets.token_urlsafe(32)
    api_key.save()

    return redirect('dashboard')


@login_required
def user_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')  # Redirect to dashboard URL name
        else:
            messages.error(request, "Invalid username or password")
    return render(request, 'login.html')

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully! You can now log in.")
            return redirect('login')  # redirect to your login page
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})


@csrf_exempt
def proxy_ask_api(request):
    if request.method == "POST":
        try:
            body_unicode = request.body.decode('utf-8')
            body_data = json.loads(body_unicode)
            question = body_data.get('question')
            session_id = body_data.get('session_id', None)

            if not question:
                return JsonResponse({"error": "Missing question field"}, status=400)

            fastapi_response = requests.post(
                "http://127.0.0.1:8001/ask",  # Your FastAPI API URL
                json={"question": question, "session_id": session_id}
            )
            fastapi_response.raise_for_status()
            data = fastapi_response.json()

            return JsonResponse(data)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Only POST method allowed"}, status=405)
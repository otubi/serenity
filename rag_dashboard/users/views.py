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
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotAllowed
import json
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str  # for Django 4.x+
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import User



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
            # Decode and parse the JSON request body
            try:
                body_data = json.loads(request.body.decode('utf-8'))
            except json.JSONDecodeError:
                return HttpResponseBadRequest("Invalid JSON body")

            # Extract fields from the parsed data
            question = body_data.get('question')
            session_id = body_data.get('session_id', None)

            if not question:
                return JsonResponse({"error": "Missing 'question' field"}, status=400)

            # Send request to FastAPI backend
            response = requests.post(
                "http://127.0.0.1:8001/ask",  # FastAPI endpoint
                json={"question": question, "session_id": session_id}
            )

            # Raise error if not 2xx
            response.raise_for_status()

            # Parse FastAPI's JSON response
            data = response.json()

            # Rename 'answer' key to 'response' for frontend compatibility
            if "answer" in data:
                data["response"] = data.pop("answer")

            # Return modified JSON response
            return JsonResponse(data)

        except requests.exceptions.RequestException as e:
            return JsonResponse({"error": f"FastAPI server error: {str(e)}"}, status=502)
        except Exception as e:
            return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)

    # If not POST method
    return HttpResponseNotAllowed(["POST"])


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Your email has been confirmed. You can now login.")
        return redirect('login')
    else:
        return render(request, 'users/activation_invalid.html')
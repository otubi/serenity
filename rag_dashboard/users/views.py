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
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import APIKey, Project
from .forms import ProjectForm
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from .forms import CustomUserCreationForm


@login_required
def generate_api_key(request, project_id):
    # Ensure the selected project belongs to the current user
    selected_project = get_object_or_404(Project, project_id=project_id, user=request.user)

    if request.method == "POST":
        # Get or create the API key for this user and project
        api_key_obj, created = APIKey.objects.get_or_create(
            project=selected_project,
            user=request.user,
            defaults={'key': secrets.token_urlsafe(32)}
        )
        # Redirect to dashboard or a confirmation page to avoid duplicate POST
        return redirect('dashboard')

    # If GET request, just show the page with project info
    return render(request, 'generate_api_key.html', {
        'selected_project': selected_project,
    })


@login_required
def create_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.user = request.user
            project.save()
            return redirect('generate_api_key')  # Pass project ID if needed
    else:
        form = ProjectForm()
    return render(request, 'create_project.html', {'form': form})


def home(request):
    """
    Public homepage for unauthenticated users.
    """
    return render(request, 'home.html')

""""
@login_required
def dashboard(request):
    
   Dashboard for authenticated users to view or generate their API key.
    
    try:
        api_key = APIKey.objects.get(user=request.user)
    except ObjectDoesNotExist:
        api_key = None

    return render(request, 'dashboard.html', {'api_key': api_key})

 """


@login_required
def dashboard(request):
    """
    Dashboard for authenticated users to view or generate their API keys (multiple allowed per user).
    """
    # Fetch projects owned by the user
    projects = Project.objects.filter(user=request.user).order_by('project_name')
    
    # Optionally, get selected project ID from GET or default to None
    project_id = request.GET.get('project_id')
    project = None
    if project_id:
        try:
            project = projects.get(project_id=project_id)
        except Project.DoesNotExist:
            project = None

    # Fetch API keys for the user, optionally filtered by selected project if any
    if project:
        api_keys = APIKey.objects.filter(user=request.user, project=project).order_by('-created_at')
    else:
        api_keys = APIKey.objects.filter(user=request.user).order_by('-created_at')

    # Pass projects, selected project, and api keys to template
    context = {
        'projects': projects,
        'project': project,  # Renamed for consistency
        'api_keys': api_keys,
    }
    return render(request, 'dashboard.html', context)

""""
@login_required
def generate_api_key(request):
    
    # Generate or regenerate a secure API key for the authenticated user.
    
    api_key_obj, created = APIKey.objects.get_or_create(user=request.user)

    # Always regenerate the key
    new_key = secrets.token_urlsafe(32)
    api_key_obj.key = new_key
    api_key_obj.save()

    return redirect('dashboard')

"""
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
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Account created successfully! You can now log in.")
            return redirect('login')
    else:
        form = CustomUserCreationForm()
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
    

def generate_api_key_default(request):
    if request.method == "POST":
        project_id = request.POST.get("project_id")
        if project_id:
            project = Project.objects.get(project_id=project_id, user=request.user)
            new_key = APIKey.objects.create(
                user=request.user,
                project=project,
                apikey=str(uuid.uuid4())
            )
        return redirect('dashboard')


@login_required
def create_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.user = request.user
            project.save()
            return redirect('generate_api_key', project_id=project.project_id)
    else:
        form = ProjectForm()
    return render(request, 'create_project.html', {'form': form})

""""
@login_required
def generate_api_key(request, project_id):
    project = get_object_or_404(Project, project_id=project_id, user=request.user)

    # Create or update the API key
    api_key, created = APIKey.objects.get_or_create(project=project, user=request.user)
    api_key.key = secrets.token_urlsafe(32)
    api_key.save()

    return redirect('view_api_key', project_id=project.project_id)
"""

@login_required
def view_api_key(request, project_id):
    project = get_object_or_404(Project, project_id=project_id, user=request.user)
    api_key = get_object_or_404(APIKey, project=project, user=request.user)
    return render(request, 'view_api_key.html', {
        'api_key': api_key,
        'masked_key': api_key.masked_key(),
        'project': project
    })


class CustomLoginView(LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('dashboard')  # Make sure this URL name exists

from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from users import views  # Assuming all views are in `users/views.py`

urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),

    # Authentication
    path('', views.home, name='home'),  # Home page
    path('login/', views.CustomLoginView.as_view(), name='login'),  # Custom login view
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),  # Logout
    path('register/', views.register, name='register'),  # Registration
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),  # Email activation

    # Dashboard & Projects
    path('dashboard/', views.dashboard, name='dashboard'),  # User dashboard
    path('create-project/', views.create_project, name='create_project'),  # Create a project

    # API Key Management
   # path('generate-api-key/', views.generate_api_key, name='generate_api_key_default'),  # Generate without project_id
    path('generate-api-key/<uuid:project_id>/', views.generate_api_key, name='generate_api_key'),  # With project_id
    path('view-api-key/', views.view_api_key, name='view_api_key'),  # View API keys

    # RAG API Proxy (External Integration)
    path('rag_api/ask', views.proxy_ask_api, name='proxy_ask_api'),
]

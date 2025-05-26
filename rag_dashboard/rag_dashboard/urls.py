from django.contrib import admin
from django.urls import path
from users.views import home, generate_api_key, register, dashboard, proxy_ask_api
from django.contrib.auth import views as auth_views
from users import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('login/', auth_views.LoginView.as_view(
        template_name='login.html',
        redirect_authenticated_user=True,
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('generate-api-key/', generate_api_key, name='generate_api_key'),
    path('register/', register, name='register'),
    path('dashboard/', dashboard, name='dashboard'),  # Added dashboard route
    path("rag_api/ask", proxy_ask_api, name="proxy_ask_api"), 
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
]

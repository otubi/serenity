import os
import sys
import django
from django.core.asgi import get_asgi_application
from starlette.applications import Starlette
from starlette.routing import Mount

# Add the root project directory (C:\Users\USER\Desktop\rag_api) to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rag_dashboard.settings')

# Setup Django
django.setup()

# Import FastAPI app after sys.path has been updated
from rag_api import app as fastapi_app  # Ensure rag_api.py is in the base directory

# Get the Django ASGI app
django_app = get_asgi_application()

# Mount FastAPI at /api and Django at /
application = Starlette(
    routes=[
        Mount("/api", app=fastapi_app),
        Mount("/", app=django_app),
    ]
)

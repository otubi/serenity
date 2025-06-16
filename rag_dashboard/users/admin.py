from django.contrib import admin
from .models import Project, APIKey

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('project_name', 'user', 'project_id', 'created_at')
    list_filter = ('created_at', 'user')
    ordering = ('-created_at',)
    search_fields = ('project_name', 'user__username', 'project_id')

@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ('key', 'user', 'project', 'created_at')
    list_filter = ('created_at', 'user', 'project')
    ordering = ('-created_at',)
    search_fields = ('key', 'user__username', 'project__project_name')

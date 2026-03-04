from django.contrib import admin
from .models import Project, ProjectAction


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['emoji', 'title', 'owner', 'status', 'priority', 'domain', 'deadline']
    list_filter = ['status', 'priority', 'domain']
    search_fields = ['title', 'owner__username']
    ordering = ['owner', 'status', 'order']


@admin.register(ProjectAction)
class ProjectActionAdmin(admin.ModelAdmin):
    list_display = ['text', 'project', 'is_done', 'due_date']
    list_filter = ['is_done']

from django.urls import path
from . import views
from .ai_views import AIProjectPlanView, OllamaModelsView

urlpatterns = [
    # Projects CRUD
    path('', views.ProjectListCreateView.as_view(), name='project-list'),
    path('<int:pk>/', views.ProjectDetailView.as_view(), name='project-detail'),
    path('<int:pk>/status/', views.ProjectStatusUpdateView.as_view(), name='project-status'),

    # Actions
    path('<int:pk>/actions/', views.ActionListCreateView.as_view(), name='action-list'),
    path('actions/<int:pk>/', views.ActionUpdateView.as_view(), name='action-detail'),
    path('actions/<int:pk>/status/', views.ActionStatusUpdateView.as_view(), name='action-status'),

    # Roles
    path('<int:pk>/roles/', views.RoleListCreateView.as_view(), name='role-list'),
    path('roles/<int:pk>/', views.RoleDetailView.as_view(), name='role-detail'),

    # Members
    path('<int:pk>/members/', views.MemberListCreateView.as_view(), name='member-list'),
    path('members/<int:pk>/', views.MemberDetailView.as_view(), name='member-detail'),

    # AI
    path('ai/plan/', AIProjectPlanView.as_view(), name='ai-plan'),
    path('ai/models/', OllamaModelsView.as_view(), name='ai-models'),

    # Public
    path('public/<int:user_id>/', views.PublicProjectsView.as_view(), name='public-projects'),
]

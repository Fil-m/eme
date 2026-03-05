from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Project, ProjectAction, ProjectRole, ProjectMember
from .serializers import (
    ProjectSerializer, ProjectActionSerializer,
    ProjectRoleSerializer, ProjectMemberSerializer
)


# ── Projects ──────────────────────────────────────────────────────────────────

class ProjectListCreateView(generics.ListCreateAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        owner_id = self.request.query_params.get('owner')
        if owner_id:
            if str(owner_id) == str(self.request.user.id):
                return Project.objects.filter(owner=self.request.user)
            return Project.objects.filter(owner_id=owner_id, is_public=True)
        return Project.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ProjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Project.objects.filter(owner=self.request.user)


class ProjectStatusUpdateView(APIView):
    """PATCH /api/projects/<pk>/status/ — drag-and-drop status change"""
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        project = get_object_or_404(Project, pk=pk, owner=request.user)
        new_status = request.data.get('status')
        valid = [s[0] for s in Project.STATUS_CHOICES]
        if new_status not in valid:
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        project.status = new_status
        project.save(update_fields=['status', 'updated_at'])
        return Response(ProjectSerializer(project).data)


# ── Actions ───────────────────────────────────────────────────────────────────

class ActionListCreateView(generics.ListCreateAPIView):
    serializer_class = ProjectActionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_project(self):
        return get_object_or_404(Project, pk=self.kwargs['pk'], owner=self.request.user)

    def get_queryset(self):
        return self.get_project().actions.select_related('depends_on', 'assignee__user', 'assignee__role').all()

    def perform_create(self, serializer):
        serializer.save(project=self.get_project())


class ActionUpdateView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProjectActionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ProjectAction.objects.filter(project__owner=self.request.user)


class ActionStatusUpdateView(APIView):
    """PATCH /api/projects/actions/<pk>/status/ — drag-and-drop between action columns"""
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        action = get_object_or_404(ProjectAction, pk=pk, project__owner=request.user)
        new_status = request.data.get('status')
        valid = [s[0] for s in ProjectAction.ACTION_STATUS]
        if new_status not in valid:
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)

        # Block if dependency not done
        if new_status != 'todo' and action.is_blocked:
            return Response(
                {'error': f'Blocked by: "{action.depends_on.text}"'},
                status=status.HTTP_400_BAD_REQUEST
            )

        action.status = new_status
        action.save()  # save() syncs is_done
        return Response(ProjectActionSerializer(action).data)


# ── Roles ─────────────────────────────────────────────────────────────────────

class RoleListCreateView(generics.ListCreateAPIView):
    """GET/POST /api/projects/<pk>/roles/"""
    serializer_class = ProjectRoleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_project(self):
        return get_object_or_404(Project, pk=self.kwargs['pk'], owner=self.request.user)

    def get_queryset(self):
        return self.get_project().roles.all()

    def perform_create(self, serializer):
        serializer.save(project=self.get_project())


class RoleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/projects/roles/<pk>/"""
    serializer_class = ProjectRoleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ProjectRole.objects.filter(project__owner=self.request.user)


# ── Members ───────────────────────────────────────────────────────────────────

class MemberListCreateView(generics.ListCreateAPIView):
    """GET/POST /api/projects/<pk>/members/"""
    serializer_class = ProjectMemberSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_project(self):
        return get_object_or_404(Project, pk=self.kwargs['pk'], owner=self.request.user)

    def get_queryset(self):
        return self.get_project().members.select_related('user', 'role').all()

    def perform_create(self, serializer):
        serializer.save(project=self.get_project())


class MemberDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/projects/members/<pk>/"""
    serializer_class = ProjectMemberSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ProjectMember.objects.filter(project__owner=self.request.user)

    def perform_update(self, serializer):
        old_role_id = self.get_object().role_id
        member = serializer.save()
        new_role_id = member.role_id

        # Auto-assign: if a new role is set, assign this member to all actions
        # that are linked to that role and not yet assigned to anyone.
        if new_role_id and new_role_id != old_role_id:
            unassigned_role_actions = ProjectAction.objects.filter(
                project=member.project,
                assignee_role_id=new_role_id,
                assignee__isnull=True,
            )
            unassigned_role_actions.update(assignee=member)


# ── Public ────────────────────────────────────────────────────────────────────

class PublicProjectsView(generics.ListAPIView):
    """Public project wall — profile vizitka integration"""
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        return Project.objects.filter(owner_id=user_id, is_public=True)


class ProjectPageView(APIView):
    """GET /p/<pk>/ — simple HTML page showing project detail"""
    permission_classes = []  # Auth handled by JWT in JS

    def get(self, request, pk):
        from django.shortcuts import render
        return render(request, 'project_detail.html', {'project_id': pk})

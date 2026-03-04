from rest_framework import serializers
from .models import Project, ProjectAction, ProjectRole, ProjectMember


class ProjectRoleSerializer(serializers.ModelSerializer):
    members_count = serializers.SerializerMethodField()

    class Meta:
        model = ProjectRole
        fields = ['id', 'name', 'emoji', 'description', 'members_count', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_members_count(self, obj):
        return obj.members.count()


class ProjectMemberSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    display_name = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    role_name = serializers.CharField(source='role.name', read_only=True, allow_null=True)
    role_emoji = serializers.CharField(source='role.emoji', read_only=True, allow_null=True)

    class Meta:
        model = ProjectMember
        fields = ['id', 'user', 'username', 'display_name', 'avatar_url',
                  'role', 'role_name', 'role_emoji', 'joined_at']
        read_only_fields = ['id', 'joined_at', 'username', 'display_name', 'avatar_url',
                            'role_name', 'role_emoji']

    def get_display_name(self, obj):
        u = obj.user
        return getattr(u, 'display_name', None) or u.username

    def get_avatar_url(self, obj):
        u = obj.user
        if hasattr(u, 'avatar') and u.avatar:
            return u.avatar.url
        return None


class ProjectActionSerializer(serializers.ModelSerializer):
    assignee_name = serializers.SerializerMethodField()
    assignee_role_name = serializers.SerializerMethodField()
    depends_on_text = serializers.SerializerMethodField()
    is_blocked = serializers.BooleanField(read_only=True)

    class Meta:
        model = ProjectAction
        fields = [
            'id', 'text', 'status', 'is_done', 'priority',
            'deadline', 'due_date',
            'depends_on', 'depends_on_text',
            'assignee', 'assignee_name',
            'assignee_role', 'assignee_role_name',
            'is_blocked', 'created_at'
        ]
        read_only_fields = ['id', 'is_done', 'created_at', 'is_blocked',
                            'assignee_name', 'assignee_role_name', 'depends_on_text']

    def get_assignee_name(self, obj):
        if obj.assignee:
            return obj.assignee.user.username
        return None

    def get_assignee_role_name(self, obj):
        if obj.assignee_role:
            return f"{obj.assignee_role.emoji} {obj.assignee_role.name}"
        return None

    def get_depends_on_text(self, obj):
        if obj.depends_on:
            return obj.depends_on.text
        return None


class ProjectSerializer(serializers.ModelSerializer):
    actions = ProjectActionSerializer(many=True, read_only=True)
    roles = ProjectRoleSerializer(many=True, read_only=True)
    members = ProjectMemberSerializer(many=True, read_only=True)
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    actions_summary = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id', 'title', 'description', 'emoji', 'domain', 'status',
            'priority', 'deadline', 'next_action', 'is_public',
            'order', 'created_at', 'updated_at',
            'actions', 'actions_summary',
            'roles', 'members',
            'owner_username'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'owner_username']

    def get_actions_summary(self, obj):
        actions = obj.actions.all()
        total = actions.count()
        done = actions.filter(is_done=True).count()
        return {'total': total, 'done': done}

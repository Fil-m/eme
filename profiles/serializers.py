from rest_framework import serializers
from .models import EMEUser, SocialLink, FollowRelation
from django.utils import timezone
import datetime


class SocialLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialLink
        fields = ['id', 'network_name', 'link']


class EMEUserSerializer(serializers.ModelSerializer):
    social_links = SocialLinkSerializer(many=True, read_only=True)
    is_online = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = EMEUser
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email',
            'bio', 'address', 'birth_date', 'avatar', 'points', 'level',
            'telegram_id', 'language_code', 'is_node_admin',
            'social_links', 'last_seen', 'is_online',
            'followers_count', 'following_count', 'is_following', 'public_key',
        ]
        read_only_fields = ['points', 'level', 'is_node_admin', 'last_seen']

    def get_is_online(self, obj):
        if obj.last_seen:
            return obj.last_seen > timezone.now() - datetime.timedelta(minutes=5)
        return False

    def get_followers_count(self, obj):
        return obj.followers.count()

    def get_following_count(self, obj):
        return obj.following.count()

    def get_is_following(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user != obj:
            return FollowRelation.objects.filter(
                follower=request.user, following=obj
            ).exists()
        return False


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = EMEUser
        fields = ['username', 'password', 'first_name']

    def create(self, validated_data):
        return EMEUser.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', '')
        )


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Неправильний поточний пароль.')
        return value

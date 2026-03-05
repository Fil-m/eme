from rest_framework import serializers
from django.conf import settings
from .models import MediaFile, Collection, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']


class CollectionSerializer(serializers.ModelSerializer):
    files_count = serializers.IntegerField(source='files.count', read_only=True)
    children = serializers.SerializerMethodField()

    class Meta:
        model = Collection
        fields = ['id', 'name', 'description', 'parent', 'created_at', 'files_count', 'children']
        read_only_fields = ['id', 'created_at']

    def get_children(self, obj):
        children = obj.children.all()
        return CollectionSerializer(children, many=True).data


class MediaFileSerializer(serializers.ModelSerializer):
    collection_name = serializers.CharField(source='collection.name', read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    tag_names = serializers.ListField(
        child=serializers.CharField(max_length=100),
        write_only=True, required=False
    )

    preview_url = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = MediaFile
        fields = [
            'id', 'file', 'file_url', 'collection', 'collection_name', 'file_name',
            'file_path', 'preview_path', 'preview_url', 'file_size', 'mime_type',
            'visibility', 'share_token', 'tags', 'tag_names',
            'created_at', 'is_image', 'is_video',
        ]
        read_only_fields = [
            'id', 'created_at', 'preview_path', 'file_name',
            'file_size', 'mime_type', 'share_token',
        ]

    def get_preview_url(self, obj):
        if not obj.preview_path:
            return None
        request = self.context.get('request')
        # Ensure path uses forward slashes for URL
        web_path = obj.preview_path.replace('\\', '/')
        url = settings.MEDIA_URL + web_path
        if request:
            return request.build_absolute_uri(url)
        return url

    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        # For local paths, we don't have a direct URL unless streamed
        return None

    def create(self, validated_data):
        tag_names = validated_data.pop('tag_names', [])
        media_file = super().create(validated_data)
        self._set_tags(media_file, tag_names)
        return media_file

    def update(self, instance, validated_data):
        tag_names = validated_data.pop('tag_names', None)
        instance = super().update(instance, validated_data)
        if tag_names is not None:
            self._set_tags(instance, tag_names)
        return instance

    @staticmethod
    def _set_tags(media_file, tag_names):
        tags = []
        for name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=name.strip().lower())
            tags.append(tag)
        media_file.tags.set(tags)

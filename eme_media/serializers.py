from rest_framework import serializers
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

    class Meta:
        model = MediaFile
        fields = [
            'id', 'file', 'collection', 'collection_name', 'file_name',
            'file_path', 'preview_path', 'file_size', 'mime_type',
            'visibility', 'share_token', 'tags', 'tag_names',
            'created_at', 'is_image', 'is_video',
        ]
        read_only_fields = [
            'id', 'created_at', 'preview_path', 'file_name',
            'file_size', 'mime_type', 'share_token',
        ]

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

from rest_framework import serializers
from .models import Bookmark, PastebinSnippet, Memo

class BookmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bookmark
        fields = '__all__'
        read_only_fields = ('user_id', 'created_at', 'updated_at')

class PastebinSnippetSerializer(serializers.ModelSerializer):
    class Meta:
        model = PastebinSnippet
        fields = '__all__'
        read_only_fields = ('user_id', 'created_at')

class MemoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Memo
        fields = '__all__'
        read_only_fields = ('user_id', 'created_at', 'updated_at')

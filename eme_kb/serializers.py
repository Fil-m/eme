from rest_framework import serializers
from .models import KBCategory, KBArticle

class KBArticleSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_emoji = serializers.CharField(source='category.emoji', read_only=True)

    class Meta:
        model = KBArticle
        fields = ['id', 'title', 'content', 'category', 'category_name', 'category_emoji', 'tags', 'is_published', 'created_at', 'updated_at', 'order']
        read_only_fields = ['id', 'created_at', 'updated_at', 'category_name', 'category_emoji']

class KBCategorySerializer(serializers.ModelSerializer):
    articles_count = serializers.SerializerMethodField()

    class Meta:
        model = KBCategory
        fields = ['id', 'name', 'emoji', 'order', 'articles_count']
        read_only_fields = ['id', 'articles_count']

    def get_articles_count(self, obj):
        return obj.articles.count()

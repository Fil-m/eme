from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import KBCategory, KBArticle
from .serializers import KBCategorySerializer, KBArticleSerializer

class KBCategoryViewSet(viewsets.ModelViewSet):
    queryset = KBCategory.objects.all()
    serializer_class = KBCategorySerializer
    permission_classes = [IsAuthenticated]

class KBArticleViewSet(viewsets.ModelViewSet):
    queryset = KBArticle.objects.all()
    serializer_class = KBArticleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = KBArticle.objects.all()
        # Filter by category if provided
        category_id = self.request.query_params.get('category_id')
        if category_id:
            qs = qs.filter(category_id=category_id)
        return qs

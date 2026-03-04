from rest_framework import generics, permissions
from .models import CoreSettings
from .serializers import CoreSettingsSerializer

class CoreSettingsView(generics.RetrieveUpdateAPIView):
    serializer_class = CoreSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        obj, created = CoreSettings.objects.get_or_create(user=self.request.user)
        return obj

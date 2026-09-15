from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from django.conf import settings
from django.conf.urls.static import static

from users.views import CustomTokenObtainPairView


urlpatterns = [
    path('admin/', admin.site.urls),

    # Autenticación JWT
    path('api/auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Apps
    path('api/users/', include('users.urls')),
    path('api/pacientes/', include('pacientes.urls')),
    path('api/profesionales/', include('profesionales.urls')),
    path('api/turnos/', include('turnos.urls')),
    path('api/clinicos/', include('clinicos.urls')),
    path('api/notificaciones/', include('notificaciones.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
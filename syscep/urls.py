from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.contrib import messages

# Personalizar títulos del admin
admin.site.site_header = "CEP - Sistema Administrativo"
admin.site.site_title = "CEP Admin"
admin.site.index_title = "Panel de Administración"

def admin_access_check(view):
    def wrapper(request, *args, **kwargs):
        if request.path.startswith('/admin/') and request.user.is_authenticated:
            if not request.user.is_superuser:
                messages.error(request, "Acceso denegado al panel de administración.")
                return redirect('dashboard')
        return view(request, *args, **kwargs)
    return wrapper

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('sysapp.urls')),
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
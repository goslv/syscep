from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.contrib import messages


def admin_required(view_func):
    """
    Decorador que requiere que el usuario sea staff (administrador)
    """

    def check_admin(user):
        if user.is_authenticated:
            return user.is_staff
        return False

    decorated_view = user_passes_test(
        check_admin,
        login_url='dashboard',
        redirect_field_name=None
    )(view_func)

    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'No tienes permisos para acceder a esta sección.')
            return redirect('dashboard')
        return decorated_view(request, *args, **kwargs)

    return wrapper


def staff_or_superuser_required(view_func):
    """
    Decorador que requiere que el usuario sea staff o superuser
    """

    def check_permission(user):
        if user.is_authenticated:
            return user.is_staff or user.is_superuser
        return False

    decorated_view = user_passes_test(
        check_permission,
        login_url='dashboard',
        redirect_field_name=None
    )(view_func)

    def wrapper(request, *args, **kwargs):
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, 'No tienes permisos para acceder a esta sección.')
            return redirect('dashboard')
        return decorated_view(request, *args, **kwargs)

    return wrapper
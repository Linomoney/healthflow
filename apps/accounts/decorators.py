from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def admin_required(view_func):
    """Decorator: hanya user dengan role='admin' yang bisa mengakses."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Silakan login terlebih dahulu.')
            return redirect('admin_login')
        if request.user.role != 'admin':
            messages.error(request, 'Anda tidak memiliki akses ke halaman ini.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


def pasien_required(view_func):
    """Decorator: hanya user dengan role='pasien' yang bisa mengakses."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Silakan login terlebih dahulu.')
            return redirect('login')
        if request.user.role != 'pasien':
            messages.error(request, 'Halaman ini hanya untuk pasien.')
            return redirect('admin_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from .forms import LoginForm, RegisterForm, ProfilForm, ChangePasswordForm, AdminUserForm
from .decorators import admin_required

User = get_user_model()


# ──────────────────────────────────────────────
# PASIEN AUTH
# ──────────────────────────────────────────────

def login_view(request):
    """Login pasien — email + password."""
    if request.user.is_authenticated:
        if request.user.role == 'admin':
            return redirect('admin_dashboard')
        return redirect('home')

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        user = authenticate(request, username=email, password=password)
        if user is not None:
            if user.role == 'admin':
                messages.info(request, 'Silakan login melalui halaman admin.')
                return redirect('admin_login')
            login(request, user)
            messages.success(request, f'Selamat datang, {user.nama}!')
            return redirect('home')
        else:
            messages.error(request, 'Email atau password salah.')
    return render(request, 'accounts/login.html', {'form': form})


def register_view(request):
    """Registrasi pasien baru."""
    if request.user.is_authenticated:
        return redirect('home')

    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Registrasi berhasil! Selamat datang di HealthFlow.')
        return redirect('home')
    return render(request, 'accounts/daftar.html', {'form': form})


def logout_view(request):
    """Logout pasien."""
    logout(request)
    messages.info(request, 'Anda telah keluar.')
    return redirect('login')


@login_required
def profil_view(request):
    """Update profil & ganti password pasien."""
    profil_form = ProfilForm(instance=request.user)
    password_form = ChangePasswordForm(user=request.user)

    if request.method == 'POST':
        if 'update_profil' in request.POST:
            profil_form = ProfilForm(request.POST, request.FILES, instance=request.user)
            if profil_form.is_valid():
                profil_form.save()
                messages.success(request, 'Profil berhasil diperbarui.')
                return redirect('profil')
        elif 'ganti_password' in request.POST:
            password_form = ChangePasswordForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                request.user.set_password(password_form.cleaned_data['password_baru'])
                request.user.save()
                login(request, request.user)  # re-login after password change
                messages.success(request, 'Password berhasil diubah.')
                return redirect('profil')

    return render(request, 'accounts/profil.html', {
        'profil_form': profil_form,
        'password_form': password_form,
    })


# ──────────────────────────────────────────────
# ADMIN AUTH
# ──────────────────────────────────────────────

def admin_login_view(request):
    """Login admin — validasi role == admin."""
    if request.user.is_authenticated and request.user.role == 'admin':
        return redirect('admin_dashboard')

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        user = authenticate(request, username=email, password=password)
        if user is not None and user.role == 'admin':
            login(request, user)
            messages.success(request, f'Selamat datang, {user.nama}!')
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Email/password salah atau Anda bukan admin.')
    return render(request, 'accounts/admin_login.html', {'form': form})


def admin_logout_view(request):
    """Logout admin."""
    logout(request)
    messages.info(request, 'Anda telah keluar dari panel admin.')
    return redirect('admin_login')


# ──────────────────────────────────────────────
# ADMIN — KELOLA USER
# ──────────────────────────────────────────────

@admin_required
def admin_user_list(request):
    """Daftar semua pengguna (pasien + admin)."""
    query = request.GET.get('q', '')
    users = User.objects.all().order_by('-created_at')
    if query:
        users = users.filter(Q(nama__icontains=query) | Q(email__icontains=query))
    return render(request, 'accounts/admin_user_list.html', {'users': users, 'query': query})


@admin_required
def admin_user_create(request):
    """Tambah pengguna baru (admin)."""
    form = AdminUserForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        password = form.cleaned_data.get('password')
        if password:
            user.set_password(password)
        else:
            user.set_password('healthflow123')  # default password
        if not user.username:
            user.username = user.email
        user.save()
        messages.success(request, f'Pengguna {user.nama} berhasil ditambahkan.')
        return redirect('admin_user_list')
    return render(request, 'accounts/admin_user_form.html', {'form': form, 'title': 'Tambah Pengguna'})


@admin_required
def admin_user_edit(request, pk):
    """Edit pengguna (admin)."""
    user = get_object_or_404(User, pk=pk)
    form = AdminUserForm(request.POST or None, request.FILES or None, instance=user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Pengguna {user.nama} berhasil diperbarui.')
        return redirect('admin_user_list')
    return render(request, 'accounts/admin_user_form.html', {'form': form, 'title': 'Edit Pengguna'})


@admin_required
def admin_user_delete(request, pk):
    """Hapus pengguna (admin)."""
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        nama = user.nama
        user.delete()
        messages.success(request, f'Pengguna {nama} berhasil dihapus.')
        return redirect('admin_user_list')
    return render(request, 'accounts/admin_user_confirm_delete.html', {'user_obj': user})

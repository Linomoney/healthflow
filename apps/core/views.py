from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Banner, Klinik
from .forms import BannerForm, KlinikForm
# pyrefly: ignore [missing-import]
from apps.accounts.decorators import admin_required

User = get_user_model()


def home_view(request):
    """Halaman home pasien."""
    if request.user.is_authenticated and request.user.role == 'admin':
        return redirect('admin_dashboard')

    banners = Banner.objects.filter(aktif=True)
    klinik_list = Klinik.objects.filter(aktif=True)

    # Ambil data dokter dan jadwal praktik untuk peta interaktif
    # pyrefly: ignore [missing-import]
    from apps.doctors.models import Dokter
    import json

    dokter_qs = Dokter.objects.filter(aktif=True).select_related('jenis_layanan', 'klinik')
    dokter_data = []
    for doc in dokter_qs:
        schedules = []
        for sched in doc.jadwal.filter(aktif=True):
            schedules.append({
                'id': sched.id,
                'hari': sched.hari,
                'jam_mulai': sched.jam_mulai.strftime('%H:%M'),
                'jam_selesai': sched.jam_selesai.strftime('%H:%M'),
                'kuota': sched.kuota_harian,
            })
        dokter_data.append({
            'id': doc.id,
            'nama': doc.nama,
            'layanan': doc.jenis_layanan.nama_layanan,
            'klinik_id': doc.klinik.id,
            'foto_url': doc.foto.url if doc.foto else None,
            'schedules': schedules,
        })

    # Ambil data klinik untuk peta
    klinik_data = []
    for k in klinik_list:
        klinik_data.append({
            'id': k.id,
            'nama': k.nama,
            'alamat': k.alamat,
            'jam_operasional': k.jam_operasional,
            'telepon': k.telepon,
            'lat': k.latitude,
            'lng': k.longitude,
            'type': k.tipe,
        })

    is_authenticated_pasien = request.user.is_authenticated and request.user.role == 'pasien'

    context = {
        'banners': banners,
        'klinik_list': klinik_list,
        'doctors_json': json.dumps(dokter_data),
        'clinics_json': json.dumps(klinik_data),
        'is_authenticated_pasien': is_authenticated_pasien,
    }
    return render(request, 'core/home.html', context)


@admin_required
def admin_dashboard_view(request):
    """Dashboard ringkasan admin."""
    # pyrefly: ignore [missing-import]
    from apps.reservations.models import Reservasi, Antrian
    # pyrefly: ignore [missing-import]
    from apps.doctors.models import Dokter

    today = timezone.localdate()
    context = {
        'jumlah_antrean_aktif': Antrian.objects.filter(
            status='MENUNGGU',
            reservasi__tanggal_reservasi=today
        ).count(),
        'jumlah_dokter_aktif': Dokter.objects.filter(aktif=True).count(),
        'jumlah_pasien': User.objects.filter(role='pasien').count(),
        'jumlah_reservasi_hari_ini': Reservasi.objects.filter(
            tanggal_reservasi=today
        ).count(),
    }
    return render(request, 'core/admin_dashboard.html', context)


# ──────────────────────────────────────────────
# ADMIN — KELOLA BANNER
# ──────────────────────────────────────────────

@admin_required
def admin_banner_list(request):
    banners = Banner.objects.all()
    return render(request, 'core/admin_banner_list.html', {'banners': banners})


@admin_required
def admin_banner_create(request):
    form = BannerForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Banner berhasil ditambahkan.')
        return redirect('admin_banner_list')
    return render(request, 'core/admin_banner_form.html', {'form': form, 'title': 'Tambah Banner'})


@admin_required
def admin_banner_edit(request, pk):
    banner = get_object_or_404(Banner, pk=pk)
    form = BannerForm(request.POST or None, request.FILES or None, instance=banner)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Banner berhasil diperbarui.')
        return redirect('admin_banner_list')
    return render(request, 'core/admin_banner_form.html', {'form': form, 'title': 'Edit Banner'})


@admin_required
def admin_banner_delete(request, pk):
    banner = get_object_or_404(Banner, pk=pk)
    if request.method == 'POST':
        banner.delete()
        messages.success(request, 'Banner berhasil dihapus.')
        return redirect('admin_banner_list')
    return render(request, 'core/admin_banner_confirm_delete.html', {'banner': banner})


@admin_required
def admin_klinik_list(request):
    klinik_list = Klinik.objects.all()
    return render(request, 'core/admin_klinik_list.html', {'klinik_list': klinik_list})


@admin_required
def admin_klinik_create(request):
    form = KlinikForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Tempat praktik berhasil ditambahkan.')
        return redirect('admin_klinik_list')
    return render(request, 'core/admin_klinik_form.html', {'form': form, 'title': 'Tambah Tempat Praktik'})


@admin_required
def admin_klinik_edit(request, pk):
    klinik = get_object_or_404(Klinik, pk=pk)
    form = KlinikForm(request.POST or None, instance=klinik)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Tempat praktik berhasil diperbarui.')
        return redirect('admin_klinik_list')
    return render(request, 'core/admin_klinik_form.html', {'form': form, 'title': 'Edit Tempat Praktik'})


@admin_required
def admin_klinik_delete(request, pk):
    klinik = get_object_or_404(Klinik, pk=pk)
    if request.method == 'POST':
        klinik.delete()
        messages.success(request, 'Tempat praktik berhasil dihapus.')
        return redirect('admin_klinik_list')
    return render(request, 'core/admin_klinik_confirm_delete.html', {'klinik': klinik})

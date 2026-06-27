from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
import datetime

from .models import JenisLayanan, Dokter, JadwalDokter
from .forms import JenisLayananForm, DokterForm, JadwalDokterForm
# pyrefly: ignore [missing-import]
from apps.accounts.decorators import admin_required


# ──────────────────────────────────────────────
# PASIEN — LISTING & SEARCH DOKTER
# ──────────────────────────────────────────────

def dokter_list_view(request):
    """Daftar dokter untuk pasien, dengan pencarian dan filter klinik."""
    # pyrefly: ignore [missing-import]
    from apps.core.models import Klinik
    query = request.GET.get('q', '')
    klinik_id = request.GET.get('klinik', '')
    
    dokter_qs = Dokter.objects.filter(aktif=True).select_related('jenis_layanan', 'klinik')
    
    if query:
        dokter_qs = dokter_qs.filter(
            Q(nama__icontains=query) | 
            Q(jenis_layanan__nama_layanan__icontains=query) | 
            Q(klinik__nama__icontains=query)
        )
    
    selected_klinik = None
    if klinik_id and klinik_id.isdigit():
        try:
            selected_klinik = Klinik.objects.get(pk=int(klinik_id))
        except Klinik.DoesNotExist:
            selected_klinik = None

        if selected_klinik and selected_klinik.tipe == 'Apotek':
            # Apotek tidak punya dokter sendiri yang ter-FK,
            # tampilkan semua dokter aktif (sama seperti logika peta)
            pass
        elif selected_klinik:
            # Klinik biasa, filter berdasarkan FK
            dokter_qs = dokter_qs.filter(klinik_id=selected_klinik.id)
        
    klinik_list = Klinik.objects.filter(aktif=True)
    
    context = {
        'dokter_list': dokter_qs,
        'query': query,
        'klinik_list': klinik_list,
        'selected_klinik_id': selected_klinik.id if selected_klinik else None,
        'selected_klinik': selected_klinik,
    }
    return render(request, 'doctors/dokter_list.html', context)


def dokter_detail_view(request, pk):
    """Detail dokter beserta jadwal dan sisa kuota per hari."""
    dokter = get_object_or_404(Dokter, pk=pk, aktif=True)
    jadwal_qs = dokter.jadwal.filter(aktif=True)

    # Bangun info kuota 7 hari ke depan
    today = timezone.localdate()
    HARI_MAP = {
        0: 'Senin', 1: 'Selasa', 2: 'Rabu', 3: 'Kamis',
        4: 'Jumat', 5: 'Sabtu', 6: 'Minggu'
    }
    jadwal_info = []
    for i in range(7):
        tanggal = today + datetime.timedelta(days=i)
        nama_hari = HARI_MAP[tanggal.weekday()]
        jadwal_hari = jadwal_qs.filter(hari=nama_hari)
        for j in jadwal_hari:
            jadwal_info.append({
                'jadwal': j,
                'tanggal': tanggal,
                'nama_hari': nama_hari,
                'sisa_kuota': j.sisa_kuota(tanggal),
            })

    return render(request, 'doctors/dokter_detail.html', {
        'dokter': dokter,
        'jadwal_info': jadwal_info,
    })


# ──────────────────────────────────────────────
# ADMIN — JENIS LAYANAN CRUD
# ──────────────────────────────────────────────

@admin_required
def admin_layanan_list(request):
    layanan = JenisLayanan.objects.all()
    return render(request, 'doctors/admin_layanan_list.html', {'layanan_list': layanan})


@admin_required
def admin_layanan_create(request):
    form = JenisLayananForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Jenis layanan berhasil ditambahkan.')
        return redirect('admin_layanan_list')
    return render(request, 'doctors/admin_layanan_form.html', {'form': form, 'title': 'Tambah Jenis Layanan'})


@admin_required
def admin_layanan_edit(request, pk):
    layanan = get_object_or_404(JenisLayanan, pk=pk)
    form = JenisLayananForm(request.POST or None, instance=layanan)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Jenis layanan berhasil diperbarui.')
        return redirect('admin_layanan_list')
    return render(request, 'doctors/admin_layanan_form.html', {'form': form, 'title': 'Edit Jenis Layanan'})


@admin_required
def admin_layanan_delete(request, pk):
    layanan = get_object_or_404(JenisLayanan, pk=pk)
    if request.method == 'POST':
        layanan.delete()
        messages.success(request, 'Jenis layanan berhasil dihapus.')
        return redirect('admin_layanan_list')
    return render(request, 'doctors/admin_layanan_confirm_delete.html', {'layanan': layanan})


# ──────────────────────────────────────────────
# ADMIN — DOKTER CRUD
# ──────────────────────────────────────────────

@admin_required
def admin_dokter_list(request):
    dokter = Dokter.objects.select_related('jenis_layanan').all()
    return render(request, 'doctors/admin_dokter_list.html', {'dokter_list': dokter})


@admin_required
def admin_dokter_create(request):
    form = DokterForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Dokter berhasil ditambahkan.')
        return redirect('admin_dokter_list')
    return render(request, 'doctors/admin_dokter_form.html', {'form': form, 'title': 'Tambah Dokter'})


@admin_required
def admin_dokter_edit(request, pk):
    dokter = get_object_or_404(Dokter, pk=pk)
    form = DokterForm(request.POST or None, request.FILES or None, instance=dokter)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Dokter berhasil diperbarui.')
        return redirect('admin_dokter_list')
    return render(request, 'doctors/admin_dokter_form.html', {'form': form, 'title': 'Edit Dokter'})


@admin_required
def admin_dokter_delete(request, pk):
    dokter = get_object_or_404(Dokter, pk=pk)
    if request.method == 'POST':
        dokter.delete()
        messages.success(request, 'Dokter berhasil dihapus.')
        return redirect('admin_dokter_list')
    return render(request, 'doctors/admin_dokter_confirm_delete.html', {'dokter': dokter})


# ──────────────────────────────────────────────
# ADMIN — JADWAL DOKTER CRUD
# ──────────────────────────────────────────────

@admin_required
def admin_jadwal_list(request, dokter_id):
    dokter = get_object_or_404(Dokter, pk=dokter_id)
    jadwal = dokter.jadwal.all()
    return render(request, 'doctors/admin_jadwal_list.html', {'dokter': dokter, 'jadwal_list': jadwal})


@admin_required
def admin_jadwal_create(request, dokter_id):
    dokter = get_object_or_404(Dokter, pk=dokter_id)
    form = JadwalDokterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        jadwal = form.save(commit=False)
        jadwal.dokter = dokter
        jadwal.save()
        messages.success(request, 'Jadwal berhasil ditambahkan.')
        return redirect('admin_jadwal_list', dokter_id=dokter.pk)
    return render(request, 'doctors/admin_jadwal_form.html', {
        'form': form, 'dokter': dokter, 'title': 'Tambah Jadwal'
    })


@admin_required
def admin_jadwal_edit(request, dokter_id, pk):
    dokter = get_object_or_404(Dokter, pk=dokter_id)
    jadwal = get_object_or_404(JadwalDokter, pk=pk, dokter=dokter)
    form = JadwalDokterForm(request.POST or None, instance=jadwal)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Jadwal berhasil diperbarui.')
        return redirect('admin_jadwal_list', dokter_id=dokter.pk)
    return render(request, 'doctors/admin_jadwal_form.html', {
        'form': form, 'dokter': dokter, 'title': 'Edit Jadwal'
    })


@admin_required
def admin_jadwal_delete(request, dokter_id, pk):
    dokter = get_object_or_404(Dokter, pk=dokter_id)
    jadwal = get_object_or_404(JadwalDokter, pk=pk, dokter=dokter)
    if request.method == 'POST':
        jadwal.delete()
        messages.success(request, 'Jadwal berhasil dihapus.')
        return redirect('admin_jadwal_list', dokter_id=dokter.pk)
    return render(request, 'doctors/admin_jadwal_confirm_delete.html', {
        'jadwal': jadwal, 'dokter': dokter
    })

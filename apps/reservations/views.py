from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.conf import settings
import datetime

from .models import Reservasi, Antrian
from .forms import ReservasiForm
# pyrefly: ignore [missing-import]
from apps.doctors.models import JadwalDokter, Dokter
# pyrefly: ignore [missing-import]
from apps.visits.models import RiwayatKunjungan
# pyrefly: ignore [missing-import]
from apps.accounts.decorators import admin_required, pasien_required

DURASI_RATA_RATA = getattr(settings, 'DURASI_RATA_RATA_MENIT', 10)

HARI_MAP = {
    0: 'Senin', 1: 'Selasa', 2: 'Rabu', 3: 'Kamis',
    4: 'Jumat', 5: 'Sabtu', 6: 'Minggu'
}


# ──────────────────────────────────────────────
# PASIEN — BOOKING FLOW
# ──────────────────────────────────────────────

@pasien_required
def reservasi_create_view(request, jadwal_id):
    """Buat reservasi baru untuk jadwal dokter tertentu."""
    jadwal = get_object_or_404(JadwalDokter, pk=jadwal_id, aktif=True)
    form = ReservasiForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        tanggal = form.cleaned_data['tanggal']
        keluhan = form.cleaned_data['keluhan']

        # Validasi: tanggal tidak boleh di masa lalu
        if tanggal < timezone.localdate():
            messages.error(request, 'Tanggal tidak boleh di masa lalu.')
            return render(request, 'reservations/reservasi_form.html', {
                'form': form, 'jadwal': jadwal
            })

        # Validasi: hari harus sesuai jadwal
        nama_hari = HARI_MAP[tanggal.weekday()]
        if nama_hari != jadwal.hari:
            messages.error(request, f'Jadwal ini hanya tersedia pada hari {jadwal.hari}.')
            return render(request, 'reservations/reservasi_form.html', {
                'form': form, 'jadwal': jadwal
            })

        # Validasi: cek apakah pasien sudah punya reservasi aktif di jadwal+tanggal yang sama
        existing = Reservasi.objects.filter(
            user=request.user,
            jadwal=jadwal,
            tanggal_reservasi=tanggal,
            status_reservasi='AKTIF'
        ).exists()
        if existing:
            messages.error(request, 'Anda sudah memiliki reservasi aktif untuk jadwal dan tanggal ini.')
            return render(request, 'reservations/reservasi_form.html', {
                'form': form, 'jadwal': jadwal
            })

        # Atomic transaction: cek kuota + buat reservasi + buat antrean
        with transaction.atomic():
            # Cek kuota
            jumlah_aktif = Reservasi.objects.filter(
                jadwal=jadwal,
                tanggal_reservasi=tanggal,
                status_reservasi='AKTIF'
            ).count()

            if jumlah_aktif >= jadwal.kuota_harian:
                messages.error(
                    request,
                    f'Maaf, kuota untuk {jadwal.dokter.nama} pada tanggal {tanggal.strftime("%d/%m/%Y")} sudah penuh '
                    f'({jadwal.kuota_harian} pasien).'
                )
                return render(request, 'reservations/reservasi_form.html', {
                    'form': form, 'jadwal': jadwal
                })

            # Buat reservasi
            reservasi = Reservasi.objects.create(
                user=request.user,
                jadwal=jadwal,
                tanggal_reservasi=tanggal,
                keluhan=keluhan,
                status_reservasi='AKTIF',
            )

            # Hitung nomor antrean (dengan locking)
            last = (
                Antrian.objects
                .select_for_update()
                .filter(
                    reservasi__jadwal__dokter=jadwal.dokter,
                    reservasi__tanggal_reservasi=tanggal
                )
                .order_by('-nomor_antrian')
                .first()
            )
            nomor_berikutnya = (last.nomor_antrian + 1) if last else 1

            # Hitung estimasi
            selesai_count = Antrian.objects.filter(
                reservasi__jadwal__dokter=jadwal.dokter,
                reservasi__tanggal_reservasi=tanggal,
                status__in=['SELESAI', 'DIPANGGIL']
            ).count()
            estimasi = (nomor_berikutnya - selesai_count - 1) * DURASI_RATA_RATA

            Antrian.objects.create(
                reservasi=reservasi,
                nomor_antrian=nomor_berikutnya,
                estimasi_menit=max(0, estimasi),
            )

        messages.success(
            request,
            f'Reservasi berhasil! Nomor antrean Anda: {nomor_berikutnya}.'
        )
        return redirect('antrean_saya')

    return render(request, 'reservations/reservasi_form.html', {
        'form': form, 'jadwal': jadwal
    })


# ──────────────────────────────────────────────
# HELPER — BATALKAN ANTREAN KADALUARSA
# ──────────────────────────────────────────────

def auto_cancel_past_queues():
    """Batalkan otomatis antrean hari-hari sebelumnya yang belum selesai diproses."""
    today = timezone.localdate()
    past_antrian = Antrian.objects.filter(
        reservasi__tanggal_reservasi__lt=today,
        status__in=['MENUNGGU', 'DIPANGGIL']
    )
    if past_antrian.exists():
        with transaction.atomic():
            for ant in past_antrian:
                ant.status = 'DIBATALKAN'
                ant.save()
                ant.reservasi.status_reservasi = 'DIBATALKAN'
                ant.reservasi.save()


# ──────────────────────────────────────────────
# PASIEN — PEMANTAUAN ANTREAN
# ──────────────────────────────────────────────

@pasien_required
def antrean_saya_view(request):
    """Halaman pemantauan antrean pasien."""
    auto_cancel_past_queues()
    today = timezone.localdate()
    antrean_list = Antrian.objects.filter(
        reservasi__user=request.user,
        reservasi__tanggal_reservasi__gte=today,
        status__in=['MENUNGGU', 'DIPANGGIL']
    ).select_related(
        'reservasi', 'reservasi__jadwal', 'reservasi__jadwal__dokter'
    ).order_by('reservasi__tanggal_reservasi', 'nomor_antrian')

    # Hitung info tambahan per antrean
    antrean_info = []
    for ant in antrean_list:
        dokter = ant.reservasi.jadwal.dokter
        tanggal = ant.reservasi.tanggal_reservasi

        # Nomor yang sedang dipanggil
        sedang_dipanggil = Antrian.objects.filter(
            reservasi__jadwal__dokter=dokter,
            reservasi__tanggal_reservasi=tanggal,
            status='DIPANGGIL'
        ).first()
        nomor_dipanggil = sedang_dipanggil.nomor_antrian if sedang_dipanggil else 0

        # Sisa di depan
        sisa_depan = Antrian.objects.filter(
            reservasi__jadwal__dokter=dokter,
            reservasi__tanggal_reservasi=tanggal,
            status='MENUNGGU',
            nomor_antrian__lt=ant.nomor_antrian
        ).count()

        # Estimasi
        estimasi = sisa_depan * DURASI_RATA_RATA

        # Alert jika ≤ 2 di depan
        segera = sisa_depan <= 2 and ant.status == 'MENUNGGU'

        antrean_info.append({
            'antrian': ant,
            'nomor_dipanggil': nomor_dipanggil,
            'sisa_depan': sisa_depan,
            'estimasi': estimasi,
            'segera': segera,
        })

    return render(request, 'reservations/antrean_saya.html', {
        'antrean_info': antrean_info,
    })


@pasien_required
def antrean_saya_partial(request):
    """Partial view untuk HTMX polling."""
    return antrean_saya_view(request)


@pasien_required
def batalkan_antrean_view(request, pk):
    """Batalkan antrean pasien."""
    antrian = get_object_or_404(
        Antrian, pk=pk,
        reservasi__user=request.user,
        status='MENUNGGU'
    )
    if request.method == 'POST':
        antrian.status = 'DIBATALKAN'
        antrian.save()
        antrian.reservasi.status_reservasi = 'DIBATALKAN'
        antrian.reservasi.save()
        messages.success(request, 'Antrean Anda berhasil dibatalkan.')
        return redirect('antrean_saya')
    return render(request, 'reservations/batalkan_antrean.html', {'antrian': antrian})


# ──────────────────────────────────────────────
# ADMIN — MONITOR & KELOLA ANTREAN
# ──────────────────────────────────────────────

@admin_required
def admin_antrean_view(request):
    """Monitor antrean aktif dengan filter status dan summary counts."""
    auto_cancel_past_queues()
    import datetime
    dokter_filter = request.GET.get('dokter', '')
    tanggal_filter = request.GET.get('tanggal', '')
    status_filter = request.GET.get('status', '')

    parsed_date = None
    if tanggal_filter:
        try:
            parsed_date = datetime.date.fromisoformat(tanggal_filter)
        except ValueError:
            pass

    # Base queryset with all related data
    antrean_qs = Antrian.objects.select_related(
        'reservasi', 'reservasi__user', 'reservasi__jadwal',
        'reservasi__jadwal__dokter', 'reservasi__jadwal__dokter__jenis_layanan',
        'reservasi__jadwal__dokter__klinik'
    ).order_by('reservasi__tanggal_reservasi', 'reservasi__jadwal__dokter__nama', 'nomor_antrian')

    # Apply date filter
    if parsed_date:
        antrean_qs = antrean_qs.filter(reservasi__tanggal_reservasi=parsed_date)
    else:
        # Default: today and future
        today = timezone.localdate()
        antrean_qs = antrean_qs.filter(reservasi__tanggal_reservasi__gte=today)

    # Apply doctor filter
    if dokter_filter:
        antrean_qs = antrean_qs.filter(reservasi__jadwal__dokter__id=dokter_filter)

    # Summary counts BEFORE status filter (so counts show all statuses)
    summary_menunggu = antrean_qs.filter(status='MENUNGGU').count()
    summary_dipanggil = antrean_qs.filter(status='DIPANGGIL').count()
    summary_selesai = antrean_qs.filter(status='SELESAI').count()
    summary_dibatalkan = antrean_qs.filter(status='DIBATALKAN').count()
    summary_total = antrean_qs.count()

    # Apply status filter AFTER counting summaries
    if status_filter:
        antrean_qs = antrean_qs.filter(status=status_filter)

    # Build query params string for HTMX
    params = []
    if dokter_filter:
        params.append(f"dokter={dokter_filter}")
    if tanggal_filter:
        params.append(f"tanggal={tanggal_filter}")
    if status_filter:
        params.append(f"status={status_filter}")
    query_params = "?" + "&".join(params) if params else ""

    dokter_list = Dokter.objects.filter(aktif=True)

    return render(request, 'reservations/admin_antrean.html', {
        'antrean_list': antrean_qs,
        'dokter_list': dokter_list,
        'dokter_filter': dokter_filter,
        'tanggal_filter': tanggal_filter,
        'status_filter': status_filter,
        'today': timezone.localdate(),
        'query_params': query_params,
        'parsed_date': parsed_date,
        'summary_menunggu': summary_menunggu,
        'summary_dipanggil': summary_dipanggil,
        'summary_selesai': summary_selesai,
        'summary_dibatalkan': summary_dibatalkan,
        'summary_total': summary_total,
    })


@admin_required
def admin_antrean_partial(request):
    """Partial view HTMX untuk admin antrean."""
    return admin_antrean_view(request)


@admin_required
def admin_panggil_antrean(request, dokter_id):
    """Panggil antrean berikutnya untuk dokter tertentu."""
    if request.method == 'POST':
        today = timezone.localdate()
        dokter = get_object_or_404(Dokter, pk=dokter_id)

        # Cari antrean MENUNGGU terkecil untuk dokter ini hari ini
        next_antrian = Antrian.objects.filter(
            reservasi__jadwal__dokter=dokter,
            reservasi__tanggal_reservasi=today,
            status='MENUNGGU'
        ).order_by('nomor_antrian').first()

        if next_antrian:
            next_antrian.status = 'DIPANGGIL'
            next_antrian.waktu_dipanggil = timezone.now()
            next_antrian.save()
            messages.success(request, f'Antrean No. {next_antrian.nomor_antrian} ({next_antrian.reservasi.user.nama}) dipanggil.')
        else:
            messages.info(request, f'Tidak ada antrean menunggu untuk dr. {dokter.nama}.')

    return redirect('admin_antrean')


@admin_required
def admin_panggil_antrean_individu(request, pk):
    """Panggil antrean spesifik berdasarkan ID."""
    if request.method == 'POST':
        antrian = get_object_or_404(Antrian, pk=pk, status='MENUNGGU')
        antrian.status = 'DIPANGGIL'
        antrian.waktu_dipanggil = timezone.now()
        antrian.save()
        messages.success(request, f'Antrean No. {antrian.nomor_antrian} ({antrian.reservasi.user.nama}) dipanggil.')
    return redirect('admin_antrean')


@admin_required
def admin_selesai_antrean(request, pk):
    """Tandai antrean sebagai selesai + buat RiwayatKunjungan."""
    antrian = get_object_or_404(Antrian, pk=pk, status='DIPANGGIL')
    if request.method == 'POST':
        with transaction.atomic():
            antrian.status = 'SELESAI'
            antrian.save()

            antrian.reservasi.status_reservasi = 'SELESAI'
            antrian.reservasi.save()

            # Buat RiwayatKunjungan otomatis
            RiwayatKunjungan.objects.create(
                user=antrian.reservasi.user,
                dokter=antrian.reservasi.jadwal.dokter,
                reservasi=antrian.reservasi,
                tanggal_kunjungan=antrian.reservasi.tanggal_reservasi,
                catatan=antrian.reservasi.keluhan or '',
            )

        messages.success(request, f'Antrean No. {antrian.nomor_antrian} selesai. Riwayat kunjungan telah dicatat.')
    return redirect('admin_antrean')


@admin_required
def admin_reset_antrean(request, pk):
    """Reset antrean kembali ke MENUNGGU."""
    antrian = get_object_or_404(Antrian, pk=pk)
    if request.method == 'POST' and antrian.status in ('DIPANGGIL', 'SELESAI'):
        antrian.status = 'MENUNGGU'
        antrian.waktu_dipanggil = None
        antrian.save()

        # Jika sebelumnya SELESAI, kembalikan reservasi ke AKTIF dan hapus RiwayatKunjungan terkait
        if antrian.reservasi.status_reservasi == 'SELESAI':
            antrian.reservasi.status_reservasi = 'AKTIF'
            antrian.reservasi.save()
            RiwayatKunjungan.objects.filter(reservasi=antrian.reservasi).delete()

        messages.success(request, f'Antrean No. {antrian.nomor_antrian} direset ke Menunggu.')
    return redirect('admin_antrean')


@admin_required
def admin_batalkan_antrean(request, pk):
    """Admin membatalkan antrean MENUNGGU."""
    antrian = get_object_or_404(Antrian, pk=pk, status='MENUNGGU')
    if request.method == 'POST':
        with transaction.atomic():
            antrian.status = 'DIBATALKAN'
            antrian.save()
            antrian.reservasi.status_reservasi = 'DIBATALKAN'
            antrian.reservasi.save()
        messages.success(request, f'Antrean No. {antrian.nomor_antrian} ({antrian.reservasi.user.nama}) telah dibatalkan.')
    return redirect('admin_antrean')

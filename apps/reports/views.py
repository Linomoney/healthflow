from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.db.models import Count, Q
import datetime
import io

# pyrefly: ignore [missing-import]
from apps.reservations.models import Reservasi, Antrian
# pyrefly: ignore [missing-import]
from apps.doctors.models import Dokter
# pyrefly: ignore [missing-import]
from apps.core.models import Klinik
# pyrefly: ignore [missing-import]
from apps.accounts.decorators import admin_required

try:
    import openpyxl
except ImportError:
    openpyxl = None

try:
    # pyrefly: ignore [missing-import]
    from xhtml2pdf import pisa
except ImportError:
    pisa = None


def _parse_dates(request):
    """Parse filter tanggal dari request GET."""
    periode = request.GET.get('periode', 'harian')
    today = timezone.localdate()

    if periode == 'harian':
        start = today
        end = today
    elif periode == 'mingguan':
        start = today - datetime.timedelta(days=today.weekday())
        end = start + datetime.timedelta(days=6)
    elif periode == 'bulanan':
        start = today.replace(day=1)
        next_month = (today.replace(day=28) + datetime.timedelta(days=4))
        end = next_month.replace(day=1) - datetime.timedelta(days=1)
    else:
        # custom
        try:
            start = datetime.date.fromisoformat(request.GET.get('start', str(today)))
            end = datetime.date.fromisoformat(request.GET.get('end', str(today)))
        except (ValueError, TypeError):
            start = today
            end = today

    return start, end, periode


def _get_report_data(start, end, klinik_id=None, dokter_id=None):
    """Ambil data rekap per dokter untuk periode tertentu."""
    dokter_list = Dokter.objects.filter(aktif=True).select_related('jenis_layanan', 'klinik')

    if klinik_id:
        dokter_list = dokter_list.filter(klinik_id=klinik_id)
    if dokter_id:
        dokter_list = dokter_list.filter(id=dokter_id)

    data = []
    total_reservasi = 0
    total_selesai = 0
    total_dibatalkan = 0

    for dokter in dokter_list:
        qs = Reservasi.objects.filter(
            jadwal__dokter=dokter,
            tanggal_reservasi__gte=start,
            tanggal_reservasi__lte=end,
        )
        jumlah = qs.count()
        selesai = qs.filter(status_reservasi='SELESAI').count()
        dibatalkan = qs.filter(status_reservasi='DIBATALKAN').count()
        aktif = qs.filter(status_reservasi='AKTIF').count()

        total_reservasi += jumlah
        total_selesai += selesai
        total_dibatalkan += dibatalkan

        if jumlah > 0:
            data.append({
                'dokter': dokter,
                'jumlah': jumlah,
                'selesai': selesai,
                'dibatalkan': dibatalkan,
                'aktif': aktif,
            })

    return data, total_reservasi, total_selesai, total_dibatalkan


def _get_detail_data(start, end, klinik_id=None, dokter_id=None):
    """Ambil data detail per pasien untuk periode tertentu."""
    qs = Reservasi.objects.filter(
        tanggal_reservasi__gte=start,
        tanggal_reservasi__lte=end,
    ).select_related(
        'user', 'jadwal', 'jadwal__dokter',
        'jadwal__dokter__jenis_layanan', 'jadwal__dokter__klinik'
    ).order_by('tanggal_reservasi', 'created_at')

    if klinik_id:
        qs = qs.filter(jadwal__dokter__klinik_id=klinik_id)
    if dokter_id:
        qs = qs.filter(jadwal__dokter_id=dokter_id)

    return qs


@admin_required
def laporan_view(request):
    """Halaman laporan rekapitulasi."""
    start, end, periode = _parse_dates(request)
    klinik_filter = request.GET.get('klinik', '')
    dokter_filter = request.GET.get('dokter', '')

    klinik_id = int(klinik_filter) if klinik_filter.isdigit() else None
    dokter_id_val = int(dokter_filter) if dokter_filter.isdigit() else None

    data, total_reservasi, total_selesai, total_dibatalkan = _get_report_data(
        start, end, klinik_id=klinik_id, dokter_id=dokter_id_val
    )
    detail_list = _get_detail_data(start, end, klinik_id=klinik_id, dokter_id=dokter_id_val)

    # Statistik tambahan
    total_aktif = total_reservasi - total_selesai - total_dibatalkan
    rasio_keberhasilan = round((total_selesai / total_reservasi * 100), 1) if total_reservasi > 0 else 0
    jumlah_hari = max((end - start).days + 1, 1)
    rata_rata_per_hari = round(total_reservasi / jumlah_hari, 1) if total_reservasi > 0 else 0

    # Data untuk dropdown filter
    klinik_list = Klinik.objects.filter(aktif=True)
    dokter_list = Dokter.objects.filter(aktif=True).select_related('klinik')

    return render(request, 'reports/laporan.html', {
        'data': data,
        'detail_list': detail_list,
        'start': start,
        'end': end,
        'periode': periode,
        'total_reservasi': total_reservasi,
        'total_selesai': total_selesai,
        'total_dibatalkan': total_dibatalkan,
        'total_aktif': total_aktif,
        'rasio_keberhasilan': rasio_keberhasilan,
        'rata_rata_per_hari': rata_rata_per_hari,
        'klinik_list': klinik_list,
        'dokter_list': dokter_list,
        'klinik_filter': klinik_filter,
        'dokter_filter': dokter_filter,
    })


@admin_required
def export_excel(request):
    """Export laporan ke Excel."""
    start, end, periode = _parse_dates(request)
    klinik_filter = request.GET.get('klinik', '')
    dokter_filter = request.GET.get('dokter', '')
    klinik_id = int(klinik_filter) if klinik_filter.isdigit() else None
    dokter_id_val = int(dokter_filter) if dokter_filter.isdigit() else None

    data, total_reservasi, total_selesai, total_dibatalkan = _get_report_data(
        start, end, klinik_id=klinik_id, dokter_id=dokter_id_val
    )
    detail_list = _get_detail_data(start, end, klinik_id=klinik_id, dokter_id=dokter_id_val)

    if not openpyxl:
        return HttpResponse('openpyxl tidak tersedia.', status=500)

    wb = openpyxl.Workbook()

    # ── Sheet 1: Rekapitulasi per Dokter ──
    ws = wb.active
    ws.title = 'Rekapitulasi Dokter'

    ws.append([f'Laporan Rekapitulasi HealthFlow'])
    ws.append([f'Periode: {start.strftime("%d/%m/%Y")} - {end.strftime("%d/%m/%Y")}'])
    ws.append([])
    ws.append(['No', 'Dokter', 'Klinik/Apotek', 'Jenis Layanan', 'Total Reservasi', 'Selesai', 'Dibatalkan', 'Aktif'])

    for i, row in enumerate(data, 1):
        ws.append([
            i,
            f'dr. {row["dokter"].nama}',
            row['dokter'].klinik.nama,
            row['dokter'].jenis_layanan.nama_layanan,
            row['jumlah'],
            row['selesai'],
            row['dibatalkan'],
            row['aktif'],
        ])

    ws.append([])
    ws.append(['', 'TOTAL', '', '', total_reservasi, total_selesai, total_dibatalkan, ''])

    for col_letter in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
        ws.column_dimensions[col_letter].width = 18

    # ── Sheet 2: Detail Per Pasien ──
    ws2 = wb.create_sheet('Detail Per Pasien')
    ws2.append(['No', 'Tanggal', 'Nama Pasien', 'Dokter', 'Klinik/Apotek', 'Jenis Layanan', 'Keluhan', 'Status'])

    for i, r in enumerate(detail_list, 1):
        ws2.append([
            i,
            r.tanggal_reservasi.strftime('%d/%m/%Y'),
            r.user.nama,
            f'dr. {r.jadwal.dokter.nama}',
            r.jadwal.dokter.klinik.nama,
            r.jadwal.dokter.jenis_layanan.nama_layanan,
            r.keluhan or '-',
            r.get_status_reservasi_display(),
        ])

    for col_letter in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
        ws2.column_dimensions[col_letter].width = 20

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f'laporan_healthflow_{start}_{end}.xlsx'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response


@admin_required
def export_pdf(request):
    """Export laporan ke PDF."""
    start, end, periode = _parse_dates(request)
    klinik_filter = request.GET.get('klinik', '')
    dokter_filter = request.GET.get('dokter', '')
    klinik_id = int(klinik_filter) if klinik_filter.isdigit() else None
    dokter_id_val = int(dokter_filter) if dokter_filter.isdigit() else None

    data, total_reservasi, total_selesai, total_dibatalkan = _get_report_data(
        start, end, klinik_id=klinik_id, dokter_id=dokter_id_val
    )
    detail_list = _get_detail_data(start, end, klinik_id=klinik_id, dokter_id=dokter_id_val)

    if not pisa:
        return HttpResponse('xhtml2pdf tidak tersedia.', status=500)

    html = render_to_string('reports/laporan_pdf.html', {
        'data': data,
        'detail_list': detail_list,
        'start': start,
        'end': end,
        'total_reservasi': total_reservasi,
        'total_selesai': total_selesai,
        'total_dibatalkan': total_dibatalkan,
    })

    response = HttpResponse(content_type='application/pdf')
    filename = f'laporan_healthflow_{start}_{end}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    pisa.CreatePDF(io.BytesIO(html.encode('utf-8')), dest=response, encoding='utf-8')
    return response

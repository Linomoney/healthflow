from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .models import RiwayatKunjungan
from apps.accounts.decorators import pasien_required


@pasien_required
def riwayat_list_view(request):
    """Daftar riwayat kunjungan pasien."""
    riwayat = RiwayatKunjungan.objects.filter(
        user=request.user
    ).select_related('dokter', 'reservasi')
    return render(request, 'visits/riwayat_list.html', {'riwayat_list': riwayat})

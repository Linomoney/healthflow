from django.db import models
from django.conf import settings


class RiwayatKunjungan(models.Model):
    """Riwayat kunjungan pasien — otomatis dibuat saat antrean selesai."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Pasien',
        related_name='riwayat_kunjungan'
    )
    dokter = models.ForeignKey(
        'doctors.Dokter',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Dokter',
        related_name='riwayat_kunjungan'
    )
    reservasi = models.ForeignKey(
        'reservations.Reservasi',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Reservasi',
        related_name='riwayat'
    )
    catatan = models.TextField('Catatan', blank=True)
    tanggal_kunjungan = models.DateField('Tanggal Kunjungan')
    created_at = models.DateTimeField('Dibuat pada', auto_now_add=True)

    class Meta:
        verbose_name = 'Riwayat Kunjungan'
        verbose_name_plural = 'Riwayat Kunjungan'
        ordering = ['-tanggal_kunjungan']

    def __str__(self):
        return f'{self.user.nama} — {self.dokter.nama} ({self.tanggal_kunjungan})'

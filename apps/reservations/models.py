from django.db import models
from django.conf import settings


class Reservasi(models.Model):
    """Reservasi yang dibuat pasien untuk jadwal dokter tertentu."""
    STATUS_CHOICES = [
        ('AKTIF', 'Aktif'),
        ('SELESAI', 'Selesai'),
        ('DIBATALKAN', 'Dibatalkan'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Pasien',
        related_name='reservasi'
    )
    jadwal = models.ForeignKey(
        'doctors.JadwalDokter',
        on_delete=models.PROTECT,
        verbose_name='Jadwal Dokter',
        related_name='reservasi'
    )
    tanggal_reservasi = models.DateField('Tanggal Reservasi')
    keluhan = models.TextField('Keluhan', blank=True)
    status_reservasi = models.CharField(
        'Status',
        max_length=15,
        choices=STATUS_CHOICES,
        default='AKTIF'
    )
    created_at = models.DateTimeField('Dibuat pada', auto_now_add=True)

    class Meta:
        verbose_name = 'Reservasi'
        verbose_name_plural = 'Reservasi'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.nama} — {self.jadwal.dokter.nama} ({self.tanggal_reservasi})'


class Antrian(models.Model):
    """Nomor antrean yang dihasilkan dari reservasi."""
    STATUS_CHOICES = [
        ('MENUNGGU', 'Menunggu'),
        ('DIPANGGIL', 'Dipanggil'),
        ('SELESAI', 'Selesai'),
        ('DIBATALKAN', 'Dibatalkan'),
    ]

    reservasi = models.OneToOneField(
        Reservasi,
        on_delete=models.CASCADE,
        verbose_name='Reservasi',
        related_name='antrian'
    )
    nomor_antrian = models.PositiveIntegerField('Nomor Antrean')
    status = models.CharField(
        'Status',
        max_length=15,
        choices=STATUS_CHOICES,
        default='MENUNGGU'
    )
    waktu_dipanggil = models.DateTimeField('Waktu Dipanggil', null=True, blank=True)
    estimasi_menit = models.PositiveIntegerField('Estimasi Tunggu (menit)', default=0)
    created_at = models.DateTimeField('Dibuat pada', auto_now_add=True)

    class Meta:
        verbose_name = 'Antrean'
        verbose_name_plural = 'Antrean'
        ordering = ['nomor_antrian']

    def __str__(self):
        return f'No. {self.nomor_antrian} — {self.reservasi.user.nama} ({self.reservasi.tanggal_reservasi})'

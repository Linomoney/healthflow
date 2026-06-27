from django.db import models


class JenisLayanan(models.Model):
    """Jenis layanan medis yang tersedia di klinik."""
    nama_layanan = models.CharField('Nama Layanan', max_length=100)
    deskripsi = models.TextField('Deskripsi', blank=True)
    aktif = models.BooleanField('Aktif', default=True)

    class Meta:
        verbose_name = 'Jenis Layanan'
        verbose_name_plural = 'Jenis Layanan'
        ordering = ['nama_layanan']

    def __str__(self):
        return self.nama_layanan


class Dokter(models.Model):
    """Data dokter yang berpraktik di klinik."""
    nama = models.CharField('Nama Dokter', max_length=150)
    klinik = models.ForeignKey(
        'core.Klinik',
        on_delete=models.PROTECT,
        related_name='dokter',
        verbose_name='Klinik / Tempat Praktik'
    )
    jenis_layanan = models.ForeignKey(
        JenisLayanan,
        on_delete=models.PROTECT,
        verbose_name='Jenis Layanan',
        related_name='dokter'
    )
    foto = models.ImageField('Foto', upload_to='dokter/', null=True, blank=True)
    aktif = models.BooleanField('Aktif', default=True)

    class Meta:
        verbose_name = 'Dokter'
        verbose_name_plural = 'Dokter'
        ordering = ['nama']

    def __str__(self):
        return f'dr. {self.nama} — {self.jenis_layanan} ({self.klinik.nama})'



class JadwalDokter(models.Model):
    """Jadwal praktik dokter per hari dengan kuota harian."""
    HARI_CHOICES = [
        ('Senin', 'Senin'),
        ('Selasa', 'Selasa'),
        ('Rabu', 'Rabu'),
        ('Kamis', 'Kamis'),
        ('Jumat', 'Jumat'),
        ('Sabtu', 'Sabtu'),
        ('Minggu', 'Minggu'),
    ]

    HARI_ORDER = {
        'Senin': 0, 'Selasa': 1, 'Rabu': 2, 'Kamis': 3,
        'Jumat': 4, 'Sabtu': 5, 'Minggu': 6
    }

    dokter = models.ForeignKey(
        Dokter,
        on_delete=models.CASCADE,
        verbose_name='Dokter',
        related_name='jadwal'
    )
    hari = models.CharField('Hari', max_length=10, choices=HARI_CHOICES)
    jam_mulai = models.TimeField('Jam Mulai')
    jam_selesai = models.TimeField('Jam Selesai')
    kuota_harian = models.PositiveIntegerField('Kuota Harian', default=20)
    aktif = models.BooleanField('Aktif', default=True)

    class Meta:
        verbose_name = 'Jadwal Dokter'
        verbose_name_plural = 'Jadwal Dokter'
        unique_together = ('dokter', 'hari', 'jam_mulai')

    def __str__(self):
        return f'{self.dokter.nama} — {self.hari} {self.jam_mulai:%H:%M}–{self.jam_selesai:%H:%M}'

    def sisa_kuota(self, tanggal):
        """Hitung sisa kuota untuk tanggal tertentu."""
        # pyrefly: ignore [missing-import]
        from apps.reservations.models import Reservasi
        terpakai = Reservasi.objects.filter(
            jadwal=self,
            tanggal_reservasi=tanggal,
            status_reservasi='AKTIF'
        ).count()
        return max(0, self.kuota_harian - terpakai)

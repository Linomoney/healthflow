from django.db import models


class Banner(models.Model):
    """Banner promo yang tampil di halaman home pasien."""
    judul = models.CharField('Judul', max_length=200)
    deskripsi = models.TextField('Deskripsi', blank=True)
    gambar = models.ImageField('Gambar', upload_to='banners/')
    aktif = models.BooleanField('Aktif', default=True)
    urutan = models.PositiveIntegerField('Urutan', default=0)
    created_at = models.DateTimeField('Dibuat pada', auto_now_add=True)

    class Meta:
        verbose_name = 'Banner'
        verbose_name_plural = 'Banner'
        ordering = ['urutan', '-created_at']

    def __str__(self):
        return self.judul


class Klinik(models.Model):
    """Klinik atau tempat praktik berobat, termasuk apotek mitra."""
    TIPE_CHOICES = [
        ('Klinik', 'Klinik / Tempat Praktik'),
        ('Apotek', 'Apotek / Farmasi'),
    ]

    nama = models.CharField('Nama Tempat Praktik', max_length=200)
    tipe = models.CharField('Tipe Tempat', max_length=20, choices=TIPE_CHOICES, default='Klinik')
    alamat = models.TextField('Alamat')
    jam_operasional = models.CharField('Jam Operasional', max_length=200)
    telepon = models.CharField('Telepon', max_length=30)
    deskripsi = models.TextField('Deskripsi', blank=True)
    latitude = models.FloatField('Latitude', default=-6.3503)
    longitude = models.FloatField('Longitude', default=106.8643)
    aktif = models.BooleanField('Aktif', default=True)

    class Meta:
        verbose_name = 'Tempat Praktik'
        verbose_name_plural = 'Tempat Praktik'
        ordering = ['nama']

    def __str__(self):
        return f'{self.nama} ({self.get_tipe_display()})'



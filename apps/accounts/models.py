from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class CustomUserManager(BaseUserManager):
    """Manager untuk CustomUser — login memakai email, bukan username."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email wajib diisi.')
        email = self.normalize_email(email)
        extra_fields.setdefault('username', email)
        extra_fields.setdefault('role', 'pasien')
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('nama', 'Administrator')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser harus memiliki is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser harus memiliki is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """Model pengguna kustom — login via email, dengan field role."""

    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('pasien', 'Pasien'),
    ]

    email = models.EmailField('Email', unique=True)
    nama = models.CharField('Nama Lengkap', max_length=150)
    no_hp = models.CharField('No. HP', max_length=20, blank=True)
    alamat = models.TextField('Alamat', blank=True)
    role = models.CharField('Role', max_length=10, choices=ROLE_CHOICES, default='pasien')
    foto_profil = models.ImageField('Foto Profil', upload_to='profil/', null=True, blank=True)
    created_at = models.DateTimeField('Dibuat pada', auto_now_add=True)
    updated_at = models.DateTimeField('Diperbarui pada', auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nama']

    objects = CustomUserManager()

    class Meta:
        verbose_name = 'Pengguna'
        verbose_name_plural = 'Pengguna'

    def __str__(self):
        return f'{self.nama} ({self.email})'

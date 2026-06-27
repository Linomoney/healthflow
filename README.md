# HealthFlow

HealthFlow adalah sistem manajemen antrean digital klinik berbasis web, yang dirancang khusus untuk **Klinik Cisalak Pasar**. Sistem ini menggantikan proses antrean manual dengan alur digital yang efisien, transparan, dan responsif. Pasien dapat melakukan registrasi, mencari dokter, melakukan reservasi (booking) dari rumah, dan memantau status antrean secara real-time. Administrator dan petugas medis dapat mengelola data master, memanggil pasien, menandai kunjungan selesai, dan menghasilkan laporan rekapitulasi periodik.

---

## 🌟 Fitur Utama

### 📱 Antarmuka Pasien (Mobile-First)
- **Registrasi & Login Mandiri**: Akun pasien menggunakan Email sebagai pengidentifikasi utama.
- **Pencarian Dokter & Layanan**: Melihat daftar poli (Umum, Gigi, Anak/KIA, Gizi) serta jadwal dokter yang aktif.
- **Reservasi Online**: Melakukan booking konsultasi H-1 atau pada hari aktif jadwal dengan pembatasan kuota harian otomatis.
- **Pemantauan Antrean Real-Time**: Halaman antrean aktif dengan pembaruan otomatis (HTMX polling) yang menunjukkan nomor antrean pasien, nomor yang sedang dipanggil, estimasi waktu tunggu, dan notifikasi peringatan jika giliran sudah dekat (≤ 2 antrean di depan).
- **Riwayat Kunjungan**: Melihat catatan medis dan resep obat yang diberikan dokter/admin pada kunjungan-kunjungan sebelumnya.

### 💻 Panel Administrator (Desktop-Optimized)
- **Dasbor Statistik**: Tampilan rekap antrean aktif hari ini, jumlah pasien terdaftar, dokter aktif, dan reservasi harian.
- **CRUD Data Master**: Manajemen pengguna (admin/pasien), data dokter, jenis layanan/poli, jadwal praktek, dan banner promosi.
- **Manajer Antrean Aktif**: Kontrol pemanggilan pasien ("Panggil Berikutnya"), penandaan selesai layanan ("Tandai Selesai" yang otomatis mencatat riwayat kunjungan), dan fungsi reset antrean.
- **Profil Klinik**: Pengaturan satu pintu untuk informasi dasar klinik (nama, alamat, jam operasional, telepon).
- **Laporan Rekapitulasi**: Filter data kunjungan berdasarkan periode (harian, mingguan, bulanan, custom range) dengan ekspor instan ke file **Excel (.xlsx)** dan **PDF (.pdf)** serta dukungan cetak ramah printer (`@media print`).

---

## 🛠️ Tech Stack

- **Framework**: Django 5.2+ (Python 3.10+)
- **Database**: SQLite3 (Production-ready untuk skala klinik lokal)
- **Frontend**: Bootstrap 5 (CSS & JS via CDN), Bootstrap Icons CDN
- **Dynamic UX**: HTMX 1.9 (untuk live polling & update antrean tanpa reload halaman)
- **Excel Export**: openpyxl
- **PDF Export**: xhtml2pdf
- **Static Asset Middleware**: WhiteNoise

---

## 📁 Struktur Folder Proyek

```text
c:\Angga\andra\healthflow\
├── apps/
│   ├── accounts/      # Manajemen User, Autentikasi, dan Hak Akses (RBAC)
│   ├── core/          # Halaman Utama, Banner Promosi, Profil Klinik, Dasbor Admin
│   ├── doctors/       # Jenis Layanan (Poli), Dokter, dan Jadwal Praktik
│   ├── reports/       # Laporan Rekapitulasi & Ekspor (Excel/PDF)
│   ├── reservations/  # Pembuatan Reservasi, Antrean, dan Alur Pemanggilan
│   └── visits/        # Pencatatan Riwayat Kunjungan Pasien
├── config/            # Pengaturan Utama Django (settings, urls, wsgi)
├── media/             # Folder Penyimpanan Upload File (Foto Dokter, Banner)
├── static/            # File Statis Kustom (CSS kustom, JS, Images)
├── templates/         # Template HTML global dan per modul
├── manage.py          # Script CLI Django
└── requirements.txt   # File Dependencies Proyek
```

---

## 🚀 Panduan Instalasi & Menjalankan Aplikasi

### 1. Prasyarat
Pastikan Anda sudah menginstal **Python 3.10 atau versi terbaru** di sistem operasi Windows Anda.

### 2. Kloning / Buka Folder Proyek
Buka terminal (PowerShell atau Command Prompt) di dalam directory proyek:
```powershell
cd c:\Angga\andra\healthflow
```

### 3. Buat dan Aktifkan Virtual Environment
```powershell
python -m venv ..\venv
..\venv\Scripts\activate
```

### 4. Instal Dependencies
```powershell
pip install -r requirements.txt
```

### 5. Buat File Konfigurasi Lingkungan (`.env`)
Buat file `.env` di root direktori proyek (`c:\Angga\andra\healthflow\.env`) dengan isi sebagai berikut:
```env
SECRET_KEY=django-insecure-your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
```

### 6. Jalankan Migrasi Database
```powershell
python manage.py makemigrations accounts core doctors reservations visits
python manage.py migrate
```

### 7. Isi Data Awal (Seeding)
Gunakan perintah kustom untuk memasukkan data uji otomatis (admin, pasien dummy, poli, dokter, jadwal, banner, dan riwayat kunjungan):
```powershell
python manage.py seed_data
```

### 8. Jalankan Server Lokal
```powershell
python manage.py runserver
```
Buka peramban (browser) dan akses alamat:
- Antarmuka Pasien: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- Panel Admin: [http://127.0.0.1:8000/admin-panel/login/](http://127.0.0.1:8000/admin-panel/login/)

---

## 🔑 Akun Default (Hasil Seeding)

### 👤 Akun Administrator
- **Email**: `admin@healthflow.test`
- **Password**: `admin123`

### 👥 Akun Pasien Dummy
1. **Email**: `pasien1@healthflow.test` | **Password**: `pasien123`
2. **Email**: `pasien2@healthflow.test` | **Password**: `pasien123`
3. **Email**: `pasien3@healthflow.test` | **Password**: `pasien123`

---

## 🧪 Menjalankan Automated Tests
Sistem ini dilengkapi dengan automated test suite untuk memvalidasi proses login, registrasi pasien baru, pembatasan kuota harian, penomoran antrean berurutan secara atomic, dan pembuatan riwayat kunjungan otomatis.

Untuk menjalankan pengujian:
```powershell
python manage.py test
```

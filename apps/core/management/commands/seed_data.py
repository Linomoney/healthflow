import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.utils import timezone
import io

try:
    from PIL import Image, ImageDraw
except ImportError:
    Image = None

# pyrefly: ignore [missing-import]
from apps.core.models import Banner, Klinik
# pyrefly: ignore [missing-import]
from apps.doctors.models import JenisLayanan, Dokter, JadwalDokter
# pyrefly: ignore [missing-import]
from apps.reservations.models import Reservasi, Antrian
# pyrefly: ignore [missing-import]
from apps.visits.models import RiwayatKunjungan

User = get_user_model()


class Command(BaseCommand):
    help = "Seed database dengan data awal untuk pengujian HealthFlow"

    def handle(self, *args, **kwargs):
        self.stdout.write("Memulai seeding data...")

        # 1. Buat Admin / Superuser
        admin_email = "admin@healthflow.test"
        admin_user, created = User.objects.get_or_create(
            email=admin_email,
            defaults={
                "username": "admin",
                "nama": "Administrator Utama",
                "no_hp": "081234567890",
                "role": "admin",
                "is_staff": True,
                "is_superuser": True,
            }
        )
        if created:
            admin_user.set_password("admin123")
            admin_user.save()
            self.stdout.write(self.style.SUCCESS(f"Admin dibuat: {admin_email} / admin123"))
        else:
            self.stdout.write(f"Admin {admin_email} sudah ada.")

        # 2. Buat Dummy Pasien
        patients_data = [
            ("pasien1@healthflow.test", "Budi Santoso", "081298765432", "Jl. Margonda Raya No. 12, Depok"),
            ("pasien2@healthflow.test", "Siti Aminah", "085698765432", "Jl. Raya Cisalak No. 45, Depok"),
            ("pasien3@healthflow.test", "Rian Wijaya", "087798765432", "Perumahan Permata Depok Blok A4/10, Depok"),
        ]
        patients = []
        for email, nama, no_hp, alamat in patients_data:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "username": email.split("@")[0],
                    "nama": nama,
                    "no_hp": no_hp,
                    "alamat": alamat,
                    "role": "pasien",
                }
            )
            if created:
                user.set_password("pasien123")
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Pasien dibuat: {email} / pasien123"))
            patients.append(user)

        # 3. Buat Jenis Layanan
        layanan_data = [
            ("Poli Umum", "Layanan pemeriksaan kesehatan umum dan konsultasi medis."),
            ("Poli Gigi", "Layanan perawatan gigi, pembersihan karang gigi, dan pencabutan."),
            ("Poli Anak/KIA", "Layanan kesehatan ibu, anak, imunisasi, dan tumbuh kembang."),
            ("Poli Gizi", "Konsultasi gizi, diet terencana, dan pemantauan status nutrisi."),
        ]
        layanan_dict = {}
        for nama, deskripsi in layanan_data:
            layanan, created = JenisLayanan.objects.get_or_create(
                nama_layanan=nama,
                defaults={"deskripsi": deskripsi, "aktif": True}
            )
            layanan_dict[nama] = layanan
            if created:
                self.stdout.write(self.style.SUCCESS(f"Layanan dibuat: {nama}"))

        # 4. Generate Dummy Images (untuk foto dokter dan banner)
        dummy_doctor_image = None
        dummy_banner_image_1 = None
        dummy_banner_image_2 = None

        if Image:
            # Foto Dokter
            img_doc = Image.new("RGB", (300, 300), color="#26C6DA")
            d_doc = ImageDraw.Draw(img_doc)
            d_doc.text((100, 140), "FOTO DOKTER", fill="white")
            f_doc = io.BytesIO()
            img_doc.save(f_doc, format="JPEG")
            dummy_doctor_image = ContentFile(f_doc.getvalue(), name="doctor_placeholder.jpg")

            # Banner 1
            img_b1 = Image.new("RGB", (800, 400), color="#1E88E5")
            d_b1 = ImageDraw.Draw(img_b1)
            d_b1.text((300, 180), "PROMO IMUNISASI", fill="white")
            f_b1 = io.BytesIO()
            img_b1.save(f_b1, format="JPEG")
            dummy_banner_image_1 = ContentFile(f_b1.getvalue(), name="banner_imunisasi.jpg")

            # Banner 2
            img_b2 = Image.new("RGB", (800, 400), color="#43C6AC")
            d_b2 = ImageDraw.Draw(img_b2)
            d_b2.text((300, 180), "KONSULTASI ONLINE", fill="white")
            f_b2 = io.BytesIO()
            img_b2.save(f_b2, format="JPEG")
            dummy_banner_image_2 = ContentFile(f_b2.getvalue(), name="banner_konsultasi.jpg")

        # 5. Buat Tempat Praktik (Klinik & Apotek)
        klinik_data = [
            ("Klinik Cisalak Pasar", "Klinik", "Jl. Raya Cisalak Pasar No. 12, Cisalak, Depok", "Senin - Sabtu: 08:00 - 17:00", "021-7712345", "Klinik kesehatan umum dengan pelayanan lengkap.", -6.3503, 106.8643),
            ("Praktik Mandiri Bidan Siti Aminah", "Klinik", "Jl. Kemuning No. 5, Cisalak Pasar, Depok", "Senin - Jumat: 09:00 - 16:00", "0812-3456-789", "Praktik mandiri bidan untuk ibu hamil, persalinan, dan KIA.", -6.3485, 106.8625),
            ("Praktik Mandiri drg. Budi Setiawan", "Klinik", "Jl. Dahlia No. 18, Cisalak Pasar, Depok", "Senin - Sabtu: 13:00 - 20:00", "0856-7890-123", "Praktik mandiri dokter gigi umum dan spesialis anak.", -6.3525, 106.8665),
            ("Apotek Kimia Farma Cisalak", "Apotek", "Jl. Raya Bogor No. 34, Cisalak, Depok", "24 Jam", "021-8771234", "Apotek Kimia Farma cabang Cisalak Depok.", -6.3490, 106.8650),
            ("Apotek K-24 Cisalak", "Apotek", "Jl. Raya Bogor No. 56, Cisalak, Depok", "24 Jam", "021-8775678", "Apotek K-24 buka 24 jam di Cisalak Depok.", -6.3515, 106.8630),
            ("Apotek Century Cisalak Pasar", "Apotek", "Ruko Cisalak Indah No. 3, Depok", "08:00 - 22:00", "021-8779012", "Apotek Century di kawasan ruko Cisalak.", -6.3505, 106.8670),
        ]
        kliniks = {}
        for nama, tipe, alamat, jam_operasional, telepon, deskripsi, lat, lng in klinik_data:
            klinik, created = Klinik.objects.get_or_create(
                nama=nama,
                defaults={
                    "tipe": tipe,
                    "alamat": alamat,
                    "jam_operasional": jam_operasional,
                    "telepon": telepon,
                    "deskripsi": deskripsi,
                    "latitude": lat,
                    "longitude": lng,
                    "aktif": True,
                }
            )
            kliniks[nama] = klinik
            if created:
                self.stdout.write(self.style.SUCCESS(f"Tempat Praktik dibuat: {nama} ({tipe})"))

        # 6. Buat Dokter
        dokter_data = [
            ("Andi Pratama", "Poli Umum", "Klinik Cisalak Pasar"),
            ("Budi Setiawan", "Poli Gigi", "Praktik Mandiri drg. Budi Setiawan"),
            ("Citra Lestari", "Poli Anak/KIA", "Praktik Mandiri Bidan Siti Aminah"),
            ("Dewi Sartika", "Poli Gizi", "Klinik Cisalak Pasar"),
            ("Eko Prasetyo", "Poli Umum", "Klinik Cisalak Pasar"),
        ]
        dokters = []
        for nama, nama_layanan, nama_klinik in dokter_data:
            layanan = layanan_dict[nama_layanan]
            klinik = kliniks[nama_klinik]
            dokter, created = Dokter.objects.get_or_create(
                nama=nama,
                klinik=klinik,
                defaults={
                    "jenis_layanan": layanan,
                    "aktif": True,
                }
            )
            if created and dummy_doctor_image:
                dokter.foto.save("doc_placeholder.jpg", dummy_doctor_image)
                dokter.save()
            dokters.append(dokter)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Dokter dibuat: dr. {nama}"))

        # 7. Buat Jadwal Dokter
        hari_list = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"]
        jadwals = []
        for idx, dokter in enumerate(dokters):
            # Berikan tiap dokter jadwal di 3 hari yang berbeda
            for i in range(3):
                hari = hari_list[(idx + i) % len(hari_list)]
                jadwal, created = JadwalDokter.objects.get_or_create(
                    dokter=dokter,
                    hari=hari,
                    jam_mulai=datetime.time(8 + i*2, 0),
                    defaults={
                        "jam_selesai": datetime.time(11 + i*2, 0),
                        "kuota_harian": 15,
                        "aktif": True,
                    }
                )
                jadwals.append(jadwal)
                if created:
                    self.stdout.write(f"Jadwal dibuat: {dokter.nama} — {hari}")

        # 8. Buat Banner Promo
        banners_data = [
            ("Imunisasi Anak Gratis", "Imunisasi dasar lengkap untuk anak usia 0-2 tahun setiap hari Rabu.", dummy_banner_image_1, 1),
            ("Konsultasi Gizi Khusus", "Dapatkan potongan harga konsultasi gizi dengan Ahli Gizi kami khusus bulan ini.", dummy_banner_image_2, 2),
        ]
        for judul, deskripsi, img_file, urutan in banners_data:
            banner, created = Banner.objects.get_or_create(
                judul=judul,
                defaults={
                    "deskripsi": deskripsi,
                    "urutan": urutan,
                    "aktif": True,
                }
            )
            if created and img_file:
                banner.gambar.save(f"banner_{urutan}.jpg", img_file)
                banner.save()
            if created:
                self.stdout.write(self.style.SUCCESS(f"Banner dibuat: {judul}"))

        # 9. Buat Sample Kunjungan Selesai & Reservasi
        today = timezone.localdate()
        yesterday = today - datetime.timedelta(days=1)
        
        # Buat riwayat kunjungan kemarin untuk dummy pasien
        if jadwals:
            # Riwayat Kunjungan Budi Santoso
            RiwayatKunjungan.objects.get_or_create(
                user=patients[0],
                dokter=dokters[0],
                defaults={
                    "catatan": "Pasien mengeluh flu ringan. Diberikan parasetamol dan vitamin C. Istirahat cukup.",
                    "tanggal_kunjungan": yesterday,
                }
            )
            # Riwayat Kunjungan Siti Aminah
            RiwayatKunjungan.objects.get_or_create(
                user=patients[1],
                dokter=dokters[1],
                defaults={
                    "catatan": "Pemeriksaan gigi berlubang kiri bawah. Dilakukan penambalan sementara.",
                    "tanggal_kunjungan": yesterday,
                }
            )
            self.stdout.write(self.style.SUCCESS("Sample Riwayat Kunjungan kemarin berhasil dibuat."))

        self.stdout.write(self.style.SUCCESS("Database seeding SELESAI!"))

import datetime
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

# pyrefly: ignore [missing-import]
from apps.doctors.models import JenisLayanan, Dokter, JadwalDokter
# pyrefly: ignore [missing-import]
from apps.reservations.models import Reservasi, Antrian
# pyrefly: ignore [missing-import]
from apps.visits.models import RiwayatKunjungan

User = get_user_model()


class ReservationTests(TestCase):
    def setUp(self):
        # Create users
        self.patient = User.objects.create_user(
            email="patient@healthflow.test",
            password="patientpassword",
            nama="Budi Santoso"
        )
        self.admin = User.objects.create_user(
            email="admin@healthflow.test",
            password="adminpassword",
            nama="Admin Cisalak",
            role="admin",
            is_staff=True
        )
        
        # Create specialty and doctor
        # pyrefly: ignore [missing-import]
        from apps.core.models import Klinik
        self.klinik = Klinik.objects.create(
            nama="Klinik Cisalak Pasar",
            alamat="Jl. Raya Cisalak Pasar No. 12, Depok",
            jam_operasional="Senin - Sabtu: 08:00 - 17:00",
            telepon="021-7712345"
        )
        self.specialty = JenisLayanan.objects.create(
            nama_layanan="Poli Umum",
            deskripsi="Layanan umum"
        )
        self.doctor = Dokter.objects.create(
            nama="Andi Pratama",
            klinik=self.klinik,
            jenis_layanan=self.specialty
        )

        # Get day of week for tomorrow
        self.tomorrow = timezone.localdate() + datetime.timedelta(days=1)
        # HARI_MAP mapping weekday number to day name
        hari_map = {
            0: 'Senin', 1: 'Selasa', 2: 'Rabu', 3: 'Kamis',
            4: 'Jumat', 5: 'Sabtu', 6: 'Minggu'
        }
        self.tomorrow_day_name = hari_map[self.tomorrow.weekday()]

        # Create Doctor Schedule for tomorrow
        self.schedule = JadwalDokter.objects.create(
            dokter=self.doctor,
            hari=self.tomorrow_day_name,
            jam_mulai=datetime.time(9, 0),
            jam_selesai=datetime.time(12, 0),
            kuota_harian=2,  # Low quota to easily test validation
            aktif=True
        )

    def test_reservation_creation_success(self):
        """Test booking reservation and generating queue number."""
        self.client.login(username="patient@healthflow.test", password="patientpassword")
        
        url = reverse("reservasi_create", kwargs={"jadwal_id": self.schedule.pk})
        data = {
            "tanggal": self.tomorrow.strftime("%Y-%m-%d"),
            "keluhan": "Batuk dan pilek sejak 2 hari yang lalu."
        }
        response = self.client.post(url, data)
        
        # Should redirect to queue monitoring
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("antrean_saya"))
        
        # Verify reservation and queue exist
        reservations = Reservasi.objects.filter(user=self.patient, jadwal=self.schedule)
        self.assertEqual(reservations.count(), 1)
        
        res = reservations.first()
        self.assertEqual(res.status_reservasi, "AKTIF")
        self.assertEqual(res.keluhan, "Batuk dan pilek sejak 2 hari yang lalu.")
        
        # Verify sequential queue number starts at 1
        queue = Antrian.objects.get(reservasi=res)
        self.assertEqual(queue.nomor_antrian, 1)
        self.assertEqual(queue.status, "MENUNGGU")

    def test_reservation_quota_enforcement(self):
        """Test that reservations cannot exceed the quota limit."""
        # Create second patient
        other_patient = User.objects.create_user(
            email="patient2@healthflow.test",
            password="patientpassword",
            nama="Siti Aminah"
        )
        
        # Patient 1 books first slot
        Reservasi.objects.create(
            user=self.patient,
            jadwal=self.schedule,
            tanggal_reservasi=self.tomorrow,
            status_reservasi="AKTIF"
        )
        # Patient 2 books second slot
        Reservasi.objects.create(
            user=other_patient,
            jadwal=self.schedule,
            tanggal_reservasi=self.tomorrow,
            status_reservasi="AKTIF"
        )
        
        # Create third patient to attempt booking
        third_patient = User.objects.create_user(
            email="patient3@healthflow.test",
            password="patientpassword",
            nama="Rian Wijaya"
        )
        self.client.login(username="patient3@healthflow.test", password="patientpassword")
        
        url = reverse("reservasi_create", kwargs={"jadwal_id": self.schedule.pk})
        data = {
            "tanggal": self.tomorrow.strftime("%Y-%m-%d"),
            "keluhan": "Sakit kepala."
        }
        
        # Try booking third slot (exceeding quota=2)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)  # Re-renders form due to error
        
        # Verify third reservation was NOT created
        self.assertFalse(Reservasi.objects.filter(user=third_patient, jadwal=self.schedule).exists())

    def test_admin_queue_actions(self):
        """Test calling next queue and completing queue (creating RiwayatKunjungan)."""
        # Create an active reservation & queue
        res = Reservasi.objects.create(
            user=self.patient,
            jadwal=self.schedule,
            tanggal_reservasi=timezone.localdate(), # today for active queue monitoring
            status_reservasi="AKTIF"
        )
        queue = Antrian.objects.create(
            reservasi=res,
            nomor_antrian=1,
            status="MENUNGGU"
        )
        
        self.client.login(username="admin@healthflow.test", password="adminpassword")
        
        # 1. Test "Call Patient" (panggil antrean)
        call_url = reverse("admin_panggil_antrean", kwargs={"dokter_id": self.doctor.pk})
        response = self.client.post(call_url)
        self.assertEqual(response.status_code, 302)
        
        queue.refresh_from_db()
        self.assertEqual(queue.status, "DIPANGGIL")
        self.assertIsNotNone(queue.waktu_dipanggil)

        # 2. Test "Mark Completed" (selesai antrean)
        complete_url = reverse("admin_selesai_antrean", kwargs={"pk": queue.pk})
        response = self.client.post(complete_url)
        self.assertEqual(response.status_code, 302)
        
        queue.refresh_from_db()
        self.assertEqual(queue.status, "SELESAI")
        
        res.refresh_from_db()
        self.assertEqual(res.status_reservasi, "SELESAI")
        
        # 3. Verify RiwayatKunjungan is auto-created
        visits = RiwayatKunjungan.objects.filter(user=self.patient, dokter=self.doctor)
        self.assertEqual(visits.count(), 1)
        self.assertEqual(visits.first().reservasi, res)

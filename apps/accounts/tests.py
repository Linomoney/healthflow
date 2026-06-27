from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class AuthenticationTests(TestCase):
    def setUp(self):
        # Create an admin user
        self.admin_user = User.objects.create_user(
            email="admin_test@healthflow.test",
            password="adminpassword",
            nama="Admin Tester",
            role="admin",
            is_staff=True,
        )
        # Create a patient user
        self.patient_user = User.objects.create_user(
            email="patient_test@healthflow.test",
            password="patientpassword",
            nama="Patient Tester",
            role="pasien",
        )

    def test_patient_registration_success(self):
        """Test user registration as a patient."""
        url = reverse("daftar")
        data = {
            "nama": "New Patient",
            "email": "new_patient@healthflow.test",
            "no_hp": "08122334455",
            "alamat": "Jl. Test No. 1",
            "password": "securepassword123",
            "password_confirm": "securepassword123",
        }
        response = self.client.post(url, data)
        # Verify redirect to home (since it logs the user in and redirects to home)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("home"))
        # Verify user is created with correct defaults
        new_user = User.objects.get(email="new_patient@healthflow.test")
        self.assertEqual(new_user.role, "pasien")
        self.assertTrue(new_user.check_password("securepassword123"))

    def test_patient_registration_password_mismatch(self):
        """Test registration fails when passwords do not match."""
        url = reverse("daftar")
        data = {
            "nama": "New Patient",
            "email": "new_patient@healthflow.test",
            "no_hp": "08122334455",
            "alamat": "Jl. Test No. 1",
            "password": "securepassword123",
            "password_confirm": "differentpassword",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200) # Form re-renders
        self.assertFalse(User.objects.filter(email="new_patient@healthflow.test").exists())

    def test_login_success(self):
        """Test login with valid credentials."""
        url = reverse("login")
        data = {
            "email": "patient_test@healthflow.test",
            "password": "patientpassword",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("home"))

    def test_login_failure(self):
        """Test login fails with invalid credentials."""
        url = reverse("login")
        data = {
            "email": "patient_test@healthflow.test",
            "password": "wrongpassword",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200) # Re-renders login page

    def test_admin_access_control(self):
        """Test that only admin users can access the admin panel."""
        admin_dashboard_url = reverse("admin_dashboard")
        
        # 1. Unauthenticated user should be redirected
        response = self.client.get(admin_dashboard_url)
        self.assertEqual(response.status_code, 302)
        
        # 2. Patient user should be redirected (no access)
        self.client.login(username="patient_test@healthflow.test", password="patientpassword")
        response = self.client.get(admin_dashboard_url)
        self.assertEqual(response.status_code, 302)
        self.client.logout()

        # 3. Admin user should access successfully
        self.client.login(username="admin_test@healthflow.test", password="adminpassword")
        response = self.client.get(admin_dashboard_url)
        self.assertEqual(response.status_code, 200)

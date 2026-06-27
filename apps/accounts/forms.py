from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model

User = get_user_model()


class LoginForm(forms.Form):
    """Form login pasien — email + password."""
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Masukkan email Anda',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Masukkan password',
        })
    )


class RegisterForm(forms.ModelForm):
    """Form registrasi pasien baru."""
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buat password',
        })
    )
    password_confirm = forms.CharField(
        label='Konfirmasi Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ulangi password',
        })
    )

    class Meta:
        model = User
        fields = ['nama', 'email']
        widgets = {
            'nama': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nama lengkap Anda',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email Anda',
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email sudah terdaftar. Silakan gunakan email lain.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', 'Password tidak cocok.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email  # set username = email for compatibility
        user.role = 'pasien'
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class ProfilForm(forms.ModelForm):
    """Form update profil pasien."""

    class Meta:
        model = User
        fields = ['nama', 'username', 'no_hp', 'alamat', 'foto_profil']
        widgets = {
            'nama': forms.TextInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'no_hp': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '08xxxxxxxxxx'}),
            'alamat': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'nama': 'Nama Lengkap',
            'username': 'Username',
            'no_hp': 'No. HP',
            'alamat': 'Alamat',
            'foto_profil': 'Foto Profil',
        }


class ChangePasswordForm(forms.Form):
    """Form ganti password — wajib isi password lama."""
    password_lama = forms.CharField(
        label='Password Saat Ini',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password_baru = forms.CharField(
        label='Password Baru',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password_baru_confirm = forms.CharField(
        label='Ulangi Password Baru',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_password_lama(self):
        password_lama = self.cleaned_data.get('password_lama')
        if not self.user.check_password(password_lama):
            raise forms.ValidationError('Password saat ini salah.')
        return password_lama

    def clean(self):
        cleaned_data = super().clean()
        baru = cleaned_data.get('password_baru')
        confirm = cleaned_data.get('password_baru_confirm')
        if baru and confirm and baru != confirm:
            self.add_error('password_baru_confirm', 'Password baru tidak cocok.')
        return cleaned_data


class AdminUserForm(forms.ModelForm):
    """Form admin untuk CRUD pengguna."""
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text='Kosongkan jika tidak ingin mengubah password.'
    )

    class Meta:
        model = User
        fields = ['nama', 'email', 'username', 'no_hp', 'alamat', 'role', 'foto_profil', 'is_active']
        widgets = {
            'nama': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'no_hp': forms.TextInput(attrs={'class': 'form-control'}),
            'alamat': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        if not user.username:
            user.username = user.email
        if commit:
            user.save()
        return user

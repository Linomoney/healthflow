from django import forms
from .models import JenisLayanan, Dokter, JadwalDokter


class JenisLayananForm(forms.ModelForm):
    class Meta:
        model = JenisLayanan
        fields = ['nama_layanan', 'deskripsi', 'aktif']
        widgets = {
            'nama_layanan': forms.TextInput(attrs={'class': 'form-control'}),
            'deskripsi': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'aktif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class DokterForm(forms.ModelForm):
    class Meta:
        model = Dokter
        fields = ['nama', 'klinik', 'jenis_layanan', 'foto', 'aktif']
        widgets = {
            'nama': forms.TextInput(attrs={'class': 'form-control'}),
            'klinik': forms.Select(attrs={'class': 'form-select'}),
            'jenis_layanan': forms.Select(attrs={'class': 'form-select'}),
            'aktif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }



class JadwalDokterForm(forms.ModelForm):
    class Meta:
        model = JadwalDokter
        fields = ['hari', 'jam_mulai', 'jam_selesai', 'kuota_harian', 'aktif']
        widgets = {
            'hari': forms.Select(attrs={'class': 'form-select'}),
            'jam_mulai': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'jam_selesai': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'kuota_harian': forms.NumberInput(attrs={'class': 'form-control'}),
            'aktif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

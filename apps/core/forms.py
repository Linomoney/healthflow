from django import forms
from .models import Banner, Klinik


class BannerForm(forms.ModelForm):
    class Meta:
        model = Banner
        fields = ['judul', 'deskripsi', 'gambar', 'aktif', 'urutan']
        widgets = {
            'judul': forms.TextInput(attrs={'class': 'form-control'}),
            'deskripsi': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'aktif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'urutan': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class KlinikForm(forms.ModelForm):
    class Meta:
        model = Klinik
        fields = ['nama', 'tipe', 'alamat', 'jam_operasional', 'telepon', 'deskripsi', 'latitude', 'longitude', 'aktif']
        widgets = {
            'nama': forms.TextInput(attrs={'class': 'form-control'}),
            'tipe': forms.Select(attrs={'class': 'form-select'}),
            'alamat': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'jam_operasional': forms.TextInput(attrs={'class': 'form-control'}),
            'telepon': forms.TextInput(attrs={'class': 'form-control'}),
            'deskripsi': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'aktif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


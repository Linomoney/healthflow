from django import forms


class ReservasiForm(forms.Form):
    """Form reservasi: pilih tanggal & isi keluhan."""
    tanggal = forms.DateField(
        label='Tanggal Kunjungan',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        })
    )
    keluhan = forms.CharField(
        label='Keluhan (opsional)',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Deskripsikan keluhan Anda...',
        })
    )

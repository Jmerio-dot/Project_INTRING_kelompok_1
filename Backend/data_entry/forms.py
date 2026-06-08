"""
data_entry/forms.py
Django Forms menggunakan crispy-forms + bootstrap4
Sesuai requirement praktikum Modul 4.
"""
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, Div, HTML
from .models import Pengguna, Content


class PenggunaForm(forms.ModelForm):
    """
    Form untuk input data Pengguna (Parent).
    Menggunakan crispy forms dengan Bootstrap 4 layout.
    """
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Masukkan password...'}),
        label='Password',
        min_length=6,
        required=False,
    )
    konfirmasi_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Konfirmasi password...'}),
        label='Konfirmasi Password',
        required=False,
    )

    class Meta:
        model  = Pengguna
        fields = [
            'nama_lengkap', 'email', 'username',
            'role', 'bio', 'no_telepon', 'alamat', 'tanggal_lahir',
            'foto_profil', 'aktif',
        ]
        widgets = {
            'nama_lengkap':  forms.TextInput(attrs={'placeholder': 'Nama lengkap Anda...'}),
            'email':         forms.EmailInput(attrs={'placeholder': 'email@contoh.com'}),
            'username':      forms.TextInput(attrs={'placeholder': 'username_unik'}),
            'bio':           forms.Textarea(attrs={'rows': 3, 'placeholder': 'Ceritakan tentang diri Anda...'}),
            'no_telepon':    forms.TextInput(attrs={'placeholder': '08xx-xxxx-xxxx'}),
            'alamat':        forms.Textarea(attrs={'rows': 2, 'placeholder': 'Alamat lengkap...'}),
            'tanggal_lahir': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'POST'
        self.helper.form_enctype = 'multipart/form-data'
        self.helper.form_tag = True
        self.helper.layout = Layout(
            HTML('<h5 class="text-primary mb-3"><i class="bi bi-person-fill"></i> Data Pengguna</h5>'),
            Row(
                Column('nama_lengkap', css_class='form-group col-md-6 mb-0'),
                Column('email',        css_class='form-group col-md-6 mb-0'),
                css_class='form-row',
            ),
            Row(
                Column('username',             css_class='form-group col-md-4 mb-0'),
                Column('password',             css_class='form-group col-md-4 mb-0'),
                Column('konfirmasi_password',  css_class='form-group col-md-4 mb-0'),
                css_class='form-row',
            ),
            Row(
                Column('role',          css_class='form-group col-md-4 mb-0'),
                Column('no_telepon',    css_class='form-group col-md-4 mb-0'),
                Column('tanggal_lahir', css_class='form-group col-md-4 mb-0'),
                css_class='form-row',
            ),
            Field('bio'),
            Field('alamat'),
            Row(
                Column('foto_profil', css_class='form-group col-md-6 mb-0'),
                Column('aktif',       css_class='form-group col-md-6 mb-0'),
                css_class='form-row',
            ),
            # Tombol submit — tanpa HTML() agar tidak ada masalah template tag
            Submit('submit', 'Simpan Pengguna', css_class='btn btn-primary btn-lg mr-2'),
        )

    def clean(self):
        cleaned = super().clean()
        pw  = cleaned.get('password')
        pw2 = cleaned.get('konfirmasi_password')
        if pw and pw2 and pw != pw2:
            raise forms.ValidationError('Password dan konfirmasi password tidak cocok!')
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        import hashlib
        raw_pw = self.cleaned_data.get('password', '')
        if raw_pw:
            instance.password = hashlib.sha256(raw_pw.encode()).hexdigest()
        elif not instance.pk:
            # Baru, wajib ada password
            instance.password = hashlib.sha256(b'password123').hexdigest()
        if commit:
            instance.save()
        return instance


class ContentForm(forms.ModelForm):
    """
    Form untuk input data Content (Child).
    Sesuai requirement PDF:
    - author: dropdown Pengguna (tampilkan email karena __str__ return email)
    - date_created, set_view (publish/not publish), article
    """
    class Meta:
        model  = Content
        fields = [
            'author', 'judul', 'date_created', 'set_view',
            'article', 'kategori', 'ringkasan', 'thumbnail', 'tags',
        ]
        widgets = {
            'judul':        forms.TextInput(attrs={'placeholder': 'Judul artikel...'}),
            'date_created': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
            'article': forms.Textarea(attrs={
                'rows': 10,
                'placeholder': 'Tulis isi artikel di sini...',
            }),
            'ringkasan': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Ringkasan singkat artikel...',
            }),
            'tags': forms.TextInput(attrs={
                'placeholder': 'teknologi, AI, Django (pisah koma)',
            }),
        }
        labels = {
            'author':       'Penulis (Author)',
            'judul':        'Judul Artikel',
            'date_created': 'Tanggal Dibuat',
            'set_view':     'Status Publikasi',
            'article':      'Isi Artikel',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dropdown tampilkan email Pengguna (sesuai __str__ yang return email)
        self.fields['author'].queryset = Pengguna.objects.filter(aktif=True).order_by('email')
        self.fields['author'].empty_label = '-- Pilih Penulis --'

        self.helper = FormHelper()
        self.helper.form_method = 'POST'
        self.helper.form_enctype = 'multipart/form-data'
        self.helper.form_tag = True
        self.helper.layout = Layout(
            HTML('<h5 class="text-success mb-3"><i class="bi bi-file-earmark-text"></i> Data Konten / Artikel</h5>'),
            Row(
                Column('author',   css_class='form-group col-md-6 mb-0'),
                Column('set_view', css_class='form-group col-md-3 mb-0'),
                Column('kategori', css_class='form-group col-md-3 mb-0'),
                css_class='form-row',
            ),
            Row(
                Column('judul',        css_class='form-group col-md-8 mb-0'),
                Column('date_created', css_class='form-group col-md-4 mb-0'),
                css_class='form-row',
            ),
            Field('ringkasan'),
            Field('article'),
            Row(
                Column('thumbnail', css_class='form-group col-md-6 mb-0'),
                Column('tags',      css_class='form-group col-md-6 mb-0'),
                css_class='form-row',
            ),
            Submit('submit', 'Simpan Konten', css_class='btn btn-success btn-lg mr-2'),
        )

"""
data_entry/models.py
Model Parent-Child sesuai praktikum Pemrograman Web Modul 4.

Pengguna (Parent) → Content (Child, ON DELETE CASCADE)

Sesuai requirement PDF:
- Pengguna: model parent dengan __str__ mengembalikan email
- Content: model child dengan ForeignKey ke Pengguna (CASCADE)
- Content fields: author, date_created, set_view, article
"""
from django.db import models
from django.utils import timezone


class Pengguna(models.Model):
    """
    Model Parent (Pengguna).
    Jika Pengguna dihapus → semua Content-nya ikut terhapus (CASCADE).
    """
    ROLE_CHOICES = [
        ('admin',  'Administrator'),
        ('editor', 'Editor'),
        ('viewer', 'Viewer'),
    ]

    nama_lengkap = models.CharField(max_length=200, verbose_name='Nama Lengkap')
    email        = models.EmailField(unique=True, verbose_name='Email')
    username     = models.CharField(max_length=100, unique=True, verbose_name='Username')
    password     = models.CharField(max_length=200, verbose_name='Password (Hash)')
    role         = models.CharField(max_length=20, choices=ROLE_CHOICES, default='viewer', verbose_name='Peran')
    bio          = models.TextField(blank=True, default='', verbose_name='Bio')
    no_telepon   = models.CharField(max_length=20, blank=True, default='', verbose_name='No. Telepon')
    alamat       = models.TextField(blank=True, default='', verbose_name='Alamat')
    tanggal_lahir= models.DateField(null=True, blank=True, verbose_name='Tanggal Lahir')
    foto_profil  = models.ImageField(upload_to='pengguna/foto/', null=True, blank=True, verbose_name='Foto Profil')
    aktif        = models.BooleanField(default=True, verbose_name='Aktif')
    dibuat_pada  = models.DateTimeField(default=timezone.now, verbose_name='Dibuat Pada')
    diperbarui   = models.DateTimeField(auto_now=True, verbose_name='Diperbarui')

    class Meta:
        db_table       = 'data_entry_pengguna'
        verbose_name   = 'Pengguna'
        verbose_name_plural = 'Pengguna'
        ordering       = ['nama_lengkap']

    def __str__(self):
        """
        Sesuai requirement praktikum: mengembalikan email
        agar dropdown di form Content menampilkan info yang terbaca.
        """
        return self.email

    def get_full_display(self):
        return f'{self.nama_lengkap} ({self.email})'


class Content(models.Model):
    """
    Model Child (Content).
    Jika Pengguna (parent) dihapus → Content ikut terhapus (ON DELETE CASCADE).

    Fields sesuai PDF:
    - author      : ForeignKey → Pengguna (CASCADE)
    - date_created: DateTimeField
    - set_view    : ChoiceField (publish / not publish)
    - article     : TextField
    """
    SET_VIEW_CHOICES = [
        ('publish',     'Publish'),
        ('not_publish', 'Not Publish'),
    ]

    KATEGORI_CHOICES = [
        ('teknologi', 'Teknologi'),
        ('sains',     'Sains & Riset'),
        ('bisnis',    'Bisnis & Manajemen'),
        ('tutorial',  'Tutorial & Panduan'),
        ('berita',    'Berita & Update'),
        ('lainnya',   'Lainnya'),
    ]

    # Relasi Parent-Child (sesuai praktikum)
    author       = models.ForeignKey(
        Pengguna,
        on_delete=models.CASCADE,         # ON DELETE CASCADE sesuai requirement
        related_name='contents',
        verbose_name='Penulis',
    )

    # Fields sesuai PDF
    judul        = models.CharField(max_length=500, verbose_name='Judul Artikel')
    date_created = models.DateTimeField(default=timezone.now, verbose_name='Tanggal Dibuat')
    set_view     = models.CharField(
        max_length=20,
        choices=SET_VIEW_CHOICES,
        default='not_publish',
        verbose_name='Status Publikasi',
    )
    article      = models.TextField(verbose_name='Isi Artikel')

    # Field tambahan
    kategori     = models.CharField(
        max_length=50,
        choices=KATEGORI_CHOICES,
        default='teknologi',
        verbose_name='Kategori',
    )
    ringkasan    = models.TextField(blank=True, default='', verbose_name='Ringkasan')
    thumbnail    = models.ImageField(upload_to='content/thumbnail/', null=True, blank=True, verbose_name='Thumbnail')
    tags         = models.CharField(max_length=300, blank=True, default='', verbose_name='Tags (pisah dengan koma)')
    view_count   = models.IntegerField(default=0, verbose_name='Jumlah Dilihat')
    diperbarui   = models.DateTimeField(auto_now=True, verbose_name='Terakhir Diperbarui')

    class Meta:
        db_table       = 'data_entry_content'
        verbose_name   = 'Konten'
        verbose_name_plural = 'Konten'
        ordering       = ['-date_created']

    def __str__(self):
        return f'{self.judul} — oleh {self.author.email}'

    @property
    def is_published(self):
        return self.set_view == 'publish'

    @property
    def tags_list(self):
        if self.tags:
            return [t.strip() for t in self.tags.split(',') if t.strip()]
        return []

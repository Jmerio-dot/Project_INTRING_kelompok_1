# IntRing PM — Project Management Platform

Platform manajemen proyek berbasis web (Jira-inspired) dengan **Django REST Framework** backend dan frontend HTML/JS. Dibangun sebagai tugas praktikum Pemrograman Web Modul 4 — Data Entri Parent-Child.

---

## Struktur Folder

```
C:\Kuliah\UIUX\
├── Frontend/          ← HTML/CSS/JS frontend (sudah ada)
│   ├── app.js         ← API helper (diarahkan ke Django port 8000)
│   ├── dashboard.html
│   ├── board.html
│   ├── projects.html
│   ├── login.html
│   └── ...
│
└── Backend/           ← Django backend (BARU)
    ├── manage.py
    ├── requirements.txt
    ├── seed_data.py   ← Script untuk isi data demo
    ├── intring_django.db
    │
    ├── intring_backend/   ← Django project config
    │   ├── settings.py
    │   └── urls.py
    │
    ├── core/              ← App utama (REST API + models PM)
    │   ├── models.py      ← User, Project, Sprint, Issue, Comment, Attachment, ActivityLog
    │   ├── serializers.py
    │   ├── views.py       ← Semua API endpoint
    │   ├── urls.py
    │   └── admin.py
    │
    └── data_entry/        ← App praktikum (Parent-Child)
        ├── models.py      ← Pengguna (parent) + Content (child CASCADE)
        ├── forms.py       ← Django Forms dengan crispy-forms
        ├── views.py       ← CRUD views untuk Pengguna & Content
        ├── urls.py
        └── admin.py
```

---

## Cara Setup & Menjalankan

### 1. Siapkan Environment

```bash
# Masuk ke folder Backend
cd C:\Kuliah\UIUX\Backend

# Install semua dependencies
pip install -r requirements.txt
```

### 2. Setup Database

```bash
# Buat tabel di database
python manage.py makemigrations
python manage.py migrate

# Isi data demo (user, proyek, pengguna, konten)
python seed_data.py
```

### 3. Jalankan Server Django

```bash
python manage.py runserver 8000
```

Server berjalan di: **http://127.0.0.1:8000**

### 4. Jalankan Frontend

Buka file `Frontend/login.html` langsung di browser, atau jalankan server statis:

```bash
cd C:\Kuliah\UIUX\Frontend
# Pakai Python HTTP server (opsional)
python -m http.server 5500
```

Atau buka `Frontend/login.html` langsung di browser.

---

## Akun Login Demo

| Role  | Email                | Password  |
|-------|---------------------|-----------|
| Admin | admin@intring.ai    | admin123  |
| Demo  | demo@intring.ai     | demo123   |
| Dev   | dev@intring.ai      | dev123    |

---

## URL Penting

| URL | Keterangan |
|-----|-----------|
| `http://127.0.0.1:8000/admin/` | Django Admin Panel |
| `http://127.0.0.1:8000/data-entry/` | Halaman Data Entry (praktikum) |
| `http://127.0.0.1:8000/data-entry/pengguna/` | Daftar Pengguna (Parent) |
| `http://127.0.0.1:8000/data-entry/content/` | Daftar Konten (Child) |
| `http://127.0.0.1:8000/api/auth/login` | Login API |
| `http://127.0.0.1:8000/api/projects` | Projects API |
| `http://127.0.0.1:8000/api/dashboard` | Dashboard API |

---

## REST API Endpoints

### Auth
```
POST   /api/auth/login        → Login, dapat JWT token
POST   /api/auth/register     → Register user baru
GET    /api/auth/me           → Info user yang login
```

### Projects
```
GET    /api/projects          → Semua proyek user
POST   /api/projects          → Buat proyek baru
GET    /api/projects/:id      → Detail proyek
PUT    /api/projects/:id      → Update proyek
DELETE /api/projects/:id      → Hapus proyek
GET    /api/projects/:id/board → Kanban board
```

### Issues
```
GET    /api/projects/:id/issues  → Semua issue di proyek
POST   /api/projects/:id/issues  → Buat issue baru
GET    /api/issues/:id           → Detail issue
PUT    /api/issues/:id           → Update issue
PATCH  /api/issues/:id/status   → Update status saja
DELETE /api/issues/:id           → Hapus issue
```

### Sprints, Comments, Attachments, Dashboard
```
GET/POST /api/projects/:id/sprints     → Sprint management
GET/POST /api/issues/:id/comments      → Komentar issue
GET/POST /api/issues/:id/attachments   → File lampiran
GET      /api/dashboard                → Data dashboard
```

---

## Fitur Data Entry (Praktikum Modul 4)

Sesuai requirement PDF **"Pertemuan 4 Pemrograman Web Part 2"**:

### Model Parent-Child

```python
# Pengguna (Parent)
class Pengguna(models.Model):
    nama_lengkap = models.CharField(...)
    email        = models.EmailField(unique=True)
    username     = models.CharField(unique=True)
    # ...

    def __str__(self):
        return self.email  # ← Sesuai requirement: dropdown tampilkan email

# Content (Child) — ON DELETE CASCADE
class Content(models.Model):
    author       = models.ForeignKey(
        Pengguna,
        on_delete=models.CASCADE  # ← Hapus Pengguna → Content ikut terhapus
    )
    date_created = models.DateTimeField(...)
    set_view     = models.CharField(choices=[('publish','Publish'), ('not_publish','Not Publish')])
    article      = models.TextField(...)
```

### URL Data Entry
```
/data-entry/                 → Overview & statistik
/data-entry/pengguna/        → Daftar Pengguna
/data-entry/pengguna/tambah/ → Form tambah Pengguna (set_pengguna)
/data-entry/content/         → Daftar Konten
/data-entry/content/tambah/  → Form tambah Konten (set_content)
```

---

## Tech Stack

**Backend:**
- Python 3.14 + Django 6.0
- Django REST Framework 3.17
- djangorestframework-simplejwt (JWT Auth)
- django-crispy-forms + crispy-bootstrap4
- django-cors-headers
- SQLite (development)

**Frontend:**
- HTML5 + Vanilla CSS + JavaScript
- Tema: Ocean Blue + Sky Blue gradient

---

## Menjalankan Migrations (Praktikum)

```bash
# Setelah membuat/mengubah model
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

> **Catatan:** Error HTTP 500 "no such table" terjadi jika model belum di-migrate.
> Solusi: jalankan `makemigrations` dan `migrate` terlebih dahulu.

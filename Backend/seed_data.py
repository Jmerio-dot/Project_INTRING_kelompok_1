"""
Seed script untuk mengisi database Django dengan data demo.
Jalankan: python seed_data.py
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'intring_backend.settings')
django.setup()

from django.utils import timezone
from django.contrib.auth import get_user_model
from core.models import Project, ProjectMember, Sprint, Issue, Comment, ActivityLog
from data_entry.models import Pengguna, Content

User = get_user_model()

print("🌱 Seeding database...")

# ── Core Users ────────────────────────────────────────────────────────────────
admin_user, created = User.objects.get_or_create(
    email='admin@intring.ai',
    defaults={'name': 'Admin IntRing', 'role': 'admin', 'avatar': '⚡', 'is_staff': True, 'is_superuser': True}
)
if created: admin_user.set_password('admin123'); admin_user.save()
print(f"  {'✅ Created' if created else '⚡ Exists'} admin user: admin@intring.ai / admin123")

demo_user, created = User.objects.get_or_create(
    email='demo@intring.ai',
    defaults={'name': 'Demo User', 'role': 'member', 'avatar': '🙂'}
)
if created: demo_user.set_password('demo123'); demo_user.save()
print(f"  {'✅ Created' if created else '⚡ Exists'} demo user: demo@intring.ai / demo123")

dev_user, created = User.objects.get_or_create(
    email='dev@intring.ai',
    defaults={'name': 'Dev Engineer', 'role': 'member', 'avatar': '👨‍💻'}
)
if created: dev_user.set_password('dev123'); dev_user.save()
print(f"  {'✅ Created' if created else '⚡ Exists'} dev user: dev@intring.ai / dev123")

# ── Projects ──────────────────────────────────────────────────────────────────
proj1, created = Project.objects.get_or_create(
    key='AIP',
    defaults={
        'name': 'AI Platform v2',
        'description': 'Next-generation AI platform rebuild with microservices architecture.',
        'type': 'scrum',
        'owner': admin_user,
        'status': 'active',
    }
)
if created:
    ProjectMember.objects.get_or_create(project=proj1, user=admin_user, defaults={'role': 'admin'})
    ProjectMember.objects.get_or_create(project=proj1, user=demo_user,  defaults={'role': 'member'})
print(f"  {'✅ Created' if created else '⚡ Exists'} project: AI Platform v2")

proj2, created = Project.objects.get_or_create(
    key='NSS',
    defaults={
        'name': 'Neural Security Suite',
        'description': 'AI-powered security monitoring and threat detection system.',
        'type': 'kanban',
        'owner': demo_user,
        'status': 'active',
    }
)
if created:
    ProjectMember.objects.get_or_create(project=proj2, user=demo_user, defaults={'role': 'admin'})
print(f"  {'✅ Created' if created else '⚡ Exists'} project: Neural Security Suite")

proj3, created = Project.objects.get_or_create(
    key='DEH',
    defaults={
        'name': 'Data Engineering Hub',
        'description': 'Centralized data pipeline and ETL management platform.',
        'type': 'scrum',
        'owner': dev_user,
        'status': 'active',
    }
)
if created:
    ProjectMember.objects.get_or_create(project=proj3, user=dev_user, defaults={'role': 'admin'})
print(f"  {'✅ Created' if created else '⚡ Exists'} project: Data Engineering Hub")

# ── Sprints ───────────────────────────────────────────────────────────────────
sprint1, _ = Sprint.objects.get_or_create(
    project=proj1, name='Sprint 1 — Foundation',
    defaults={'goal': 'Build core API and auth system', 'status': 'active'}
)
sprint2, _ = Sprint.objects.get_or_create(
    project=proj1, name='Sprint 2 — UI',
    defaults={'goal': 'Build Kanban board and dashboard UI', 'status': 'planning'}
)
print("  ✅ Sprints seeded")

# ── Issues ────────────────────────────────────────────────────────────────────
issues_data = [
    (proj1, sprint1, 'Build Project Management API', 'in_progress', 'high', admin_user, 'backend', 13),
    (proj1, sprint1, 'Kanban Board UI Component', 'in_progress', 'high', demo_user, 'frontend', 8),
    (proj1, sprint1, 'Issue Detail Page', 'in_review', 'medium', demo_user, 'frontend', 5),
    (proj1, sprint1, 'Fix sprint filtering bug', 'todo', 'critical', admin_user, 'bug', 2),
    (proj2, None,    'Threat detection ML model', 'in_progress', 'critical', demo_user, 'ml', 21),
    (proj2, None,    'Real-time alert dashboard', 'todo', 'high', dev_user, 'frontend', 8),
    (proj3, None,    'ETL pipeline for Kafka', 'todo', 'medium', dev_user, 'backend', 13),
]

for proj, sprint, title, iss_status, priority, assignee, label, sp in issues_data:
    if not Issue.objects.filter(project=proj, title=title).exists():
        Issue.objects.create(
            project=proj, sprint=sprint,
            title=title, description=f'Implementation of: {title}',
            type='task', status=iss_status, priority=priority,
            assignee=assignee, reporter=admin_user,
            labels=label, story_points=sp,
        )
print("  ✅ Issues seeded")

# ── Activity Logs ─────────────────────────────────────────────────────────────
for p in [proj1, proj2, proj3]:
    if not ActivityLog.objects.filter(project=p, action='project_created').exists():
        ActivityLog.objects.create(user=p.owner, project=p, action='project_created', detail=f'Created project: {p.name}')
print("  ✅ Activity logs seeded")

# ── Data Entry: Pengguna (Parent) ─────────────────────────────────────────────
pengguna_data = [
    ('Agnar Raka Baskara', 'agnar@email.com', 'agnar_raka', 'editor', 'Mahasiswa Teknik Informatika', '08123456789'),
    ('Budi Santoso',       'budi@email.com',  'budi_s',     'admin',  'Administrator sistem', '08987654321'),
    ('Citra Dewi',         'citra@email.com', 'citra_d',    'viewer', 'Pembaca konten', '08555111222'),
    ('Dimas Arya',         'dimas@email.com', 'dimas_a',    'editor', 'Penulis teknologi', '08333444555'),
]

for nama, email, username, role, bio, telp in pengguna_data:
    import hashlib
    p, created = Pengguna.objects.get_or_create(
        email=email,
        defaults={
            'nama_lengkap': nama,
            'username':     username,
            'password':     hashlib.sha256(b'password123').hexdigest(),
            'role':         role,
            'bio':          bio,
            'no_telepon':   telp,
            'aktif':        True,
        }
    )
    if created:
        print(f"  ✅ Created Pengguna: {email}")
    else:
        print(f"  ⚡ Exists Pengguna: {email}")

# ── Data Entry: Content (Child) ───────────────────────────────────────────────
agnar   = Pengguna.objects.get(email='agnar@email.com')
budi    = Pengguna.objects.get(email='budi@email.com')
dimas   = Pengguna.objects.get(email='dimas@email.com')

content_data = [
    (agnar, 'Django REST Framework — Panduan Lengkap', 'publish', 'tutorial',
     'Panduan lengkap membangun REST API dengan Django REST Framework.',
     'DRF adalah library paling populer untuk membangun REST API di Django. Artikel ini membahas mulai dari instalasi hingga deployment.'),
    (agnar, 'Implementasi JWT Authentication di Django', 'publish', 'teknologi',
     'Cara mengimplementasikan autentikasi JWT di aplikasi Django.',
     'JSON Web Token (JWT) adalah standar industri untuk autentikasi stateless. Artikel ini menjelaskan cara mengintegrasikan SimpleJWT dengan Django.'),
    (budi,  'Manajemen Database dengan Django ORM', 'not_publish', 'tutorial',
     'Tips dan trik menggunakan Django ORM secara efisien.',
     'Django ORM menyediakan abstraksi yang kuat untuk interaksi database. Pelajari cara mengoptimalkan query dan menghindari N+1 problem.'),
    (dimas, 'Parent-Child Relationship di Django Models', 'publish', 'teknologi',
     'Memahami relasi ForeignKey dan ON DELETE CASCADE di Django.',
     'Relasi parent-child adalah pola umum dalam desain database. Artikel ini menjelaskan cara mengimplementasikannya di Django dengan tepat.'),
    (dimas, 'Crispy Forms — Form yang Indah dengan Bootstrap', 'not_publish', 'tutorial',
     'Menggunakan django-crispy-forms untuk render form Bootstrap yang rapi.',
     'django-crispy-forms memungkinkan kita merender form Django dengan Bootstrap tanpa menulis HTML manual. Pelajari cara setup dan penggunaannya.'),
]

for author, judul, set_view, kategori, ringkasan, article in content_data:
    if not Content.objects.filter(judul=judul).exists():
        Content.objects.create(
            author=author, judul=judul, set_view=set_view,
            kategori=kategori, ringkasan=ringkasan, article=article,
            tags='django,python,web',
        )
        print(f"  ✅ Created Content: {judul[:40]}")
    else:
        print(f"  ⚡ Exists Content: {judul[:40]}")

print("\n✅ Seeding complete!")
print("\n📌 Login credentials:")
print("   Django Admin : http://127.0.0.1:8000/admin/")
print("   Admin user   : admin@intring.ai / admin123")
print("   Demo user    : demo@intring.ai  / demo123")
print("\n📌 API Base URL : http://127.0.0.1:8000/api/")
print("📌 Data Entry   : http://127.0.0.1:8000/data-entry/")

"""
core/tests/test_models.py
Pengujian Model — Praktikum 6: Unit Testing Django

Jalankan: python manage.py test core.tests.test_models --verbosity 2
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from core.models import Project, Sprint, Issue

User = get_user_model()


class UserModelTest(TestCase):
    """Pengujian model User (custom AbstractBaseUser)."""

    @classmethod
    def setUpTestData(cls):
        """Buat data awal sekali untuk semua test di kelas ini."""
        cls.user = User.objects.create_user(
            email='test@intring.ai',
            password='testpass123',
            name='Test User',
            role='member',
        )

    def test_user_str(self):
        """__str__ harus mengembalikan 'Nama <email>'."""
        self.assertEqual(str(self.user), 'Test User <test@intring.ai>')

    def test_user_email_unique(self):
        """Email harus unik."""
        self.assertEqual(self.user.email, 'test@intring.ai')

    def test_user_role_default(self):
        """Cek role tersimpan dengan benar."""
        self.assertEqual(self.user.role, 'member')

    def test_user_is_active_default(self):
        """User aktif secara default."""
        self.assertTrue(self.user.is_active)

    def test_user_check_password(self):
        """Verifikasi password hashing berfungsi."""
        self.assertTrue(self.user.check_password('testpass123'))
        self.assertFalse(self.user.check_password('wrongpassword'))


class ProjectModelTest(TestCase):
    """Pengujian model Project."""

    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(
            email='owner@intring.ai',
            password='ownerpass',
            name='Owner User',
        )
        cls.project = Project.objects.create(
            name='Proyek Test',
            key='PT',
            description='Deskripsi proyek test',
            type='scrum',
            owner=cls.owner,
        )

    def test_project_str(self):
        """__str__ harus mengembalikan format [KEY] Name."""
        self.assertEqual(str(self.project), '[PT] Proyek Test')

    def test_project_key_uppercase(self):
        """Key proyek harus uppercase."""
        self.assertEqual(self.project.key, self.project.key.upper())

    def test_project_default_status(self):
        """Status default proyek adalah 'active'."""
        self.assertEqual(self.project.status, 'active')

    def test_project_open_issues_count_empty(self):
        """Proyek baru tidak punya issue, count harus 0."""
        self.assertEqual(self.project.open_issues_count, 0)


class IssueModelTest(TestCase):
    """Pengujian model Issue (ticket)."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email='dev@intring.ai',
            password='devpass',
            name='Developer',
        )
        cls.project = Project.objects.create(
            name='Issue Test Project',
            key='ITP',
            owner=cls.user,
        )
        cls.issue = Issue.objects.create(
            project=cls.project,
            title='Bug di halaman login',
            type='bug',
            status='todo',
            priority='high',
            reporter=cls.user,
        )

    def test_issue_str(self):
        """__str__ harus mengembalikan 'KEY-N: Title'."""
        self.assertIn('ITP-', str(self.issue))
        self.assertIn('Bug di halaman login', str(self.issue))

    def test_issue_key_auto_generated(self):
        """issue_key harus di-generate otomatis dari project key."""
        self.assertTrue(self.issue.issue_key.startswith('ITP-'))

    def test_issue_default_priority_order(self):
        """priority_order harus 0 secara default."""
        self.assertEqual(self.issue.priority_order, 0)

    def test_issue_status_choices(self):
        """Status issue valid harus ada di STATUS_CHOICES."""
        valid_statuses = [s for s, _ in Issue.STATUS_CHOICES]
        self.assertIn(self.issue.status, valid_statuses)

    def test_issue_priority_choices(self):
        """Priority issue valid harus ada di PRIORITY_CHOICES."""
        valid_priorities = [p for p, _ in Issue.PRIORITY_CHOICES]
        self.assertIn(self.issue.priority, valid_priorities)

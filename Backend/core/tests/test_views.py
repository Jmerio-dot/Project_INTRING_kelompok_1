"""
core/tests/test_views.py
Pengujian Views / API — Praktikum 6: Unit Testing Django

Menggunakan Django Test Client untuk simulasi request HTTP.
Jalankan: python manage.py test core.tests.test_views --verbosity 2
"""
import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from core.models import Project, Issue

User = get_user_model()


class AuthAPITest(TestCase):
    """Pengujian API Authentication (Login & Register)."""

    def setUp(self):
        """Setup sebelum setiap test — buat user demo."""
        self.client = Client()
        self.user = User.objects.create_user(
            email='api_test@intring.ai',
            password='testpass123',
            name='API Test User',
        )

    def test_login_success(self):
        """Login dengan kredensial benar harus mengembalikan token."""
        response = self.client.post(
            '/api/auth/login',
            data=json.dumps({'email': 'api_test@intring.ai', 'password': 'testpass123'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('token', data)
        self.assertIn('user', data)
        self.assertEqual(data['user']['email'], 'api_test@intring.ai')

    def test_login_wrong_password(self):
        """Login dengan password salah harus 401."""
        response = self.client.post(
            '/api/auth/login',
            data=json.dumps({'email': 'api_test@intring.ai', 'password': 'wrong'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn('error', response.json())

    def test_login_unknown_email(self):
        """Login dengan email yang tidak ada harus 401."""
        response = self.client.post(
            '/api/auth/login',
            data=json.dumps({'email': 'nobody@intring.ai', 'password': 'test'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 401)

    def test_register_success(self):
        """Register user baru harus mengembalikan token (201)."""
        response = self.client.post(
            '/api/auth/register',
            data=json.dumps({
                'name': 'New User',
                'email': 'newuser@intring.ai',
                'password': 'newpass123',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn('token', data)
        self.assertEqual(data['user']['name'], 'New User')

    def test_me_endpoint_without_auth(self):
        """Akses /api/auth/me tanpa token harus 401."""
        response = self.client.get('/api/auth/me')
        self.assertEqual(response.status_code, 401)

    def _get_token(self):
        """Helper: login dan kembalikan JWT token."""
        res = self.client.post(
            '/api/auth/login',
            data=json.dumps({'email': 'api_test@intring.ai', 'password': 'testpass123'}),
            content_type='application/json',
        )
        return res.json()['token']

    def test_me_endpoint_with_auth(self):
        """Akses /api/auth/me dengan token valid harus mengembalikan data user."""
        token = self._get_token()
        response = self.client.get(
            '/api/auth/me',
            HTTP_AUTHORIZATION=f'Bearer {token}',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['email'], 'api_test@intring.ai')


class ProjectAPITest(TestCase):
    """Pengujian API Projects."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='projtest@intring.ai',
            password='pass123',
            name='Proj Tester',
        )
        # Login untuk dapat token
        res = self.client.post(
            '/api/auth/login',
            data=json.dumps({'email': 'projtest@intring.ai', 'password': 'pass123'}),
            content_type='application/json',
        )
        self.token = res.json()['token']
        self.auth_header = {'HTTP_AUTHORIZATION': f'Bearer {self.token}'}

    def test_create_project(self):
        """Membuat proyek baru harus berhasil (201)."""
        response = self.client.post(
            '/api/projects',
            data=json.dumps({
                'name': 'Test Project Baru',
                'key': 'TPB',
                'description': 'Proyek untuk unit test',
                'type': 'kanban',
            }),
            content_type='application/json',
            **self.auth_header,
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['key'], 'TPB')
        self.assertEqual(data['name'], 'Test Project Baru')

    def test_list_projects_empty(self):
        """List proyek user baru harus kosong."""
        response = self.client.get('/api/projects', **self.auth_header)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

    def test_list_projects_after_create(self):
        """Setelah buat proyek, list harus menampilkan proyek tersebut."""
        # Buat proyek dulu
        self.client.post(
            '/api/projects',
            data=json.dumps({'name': 'Proyek A', 'key': 'PRA', 'type': 'scrum'}),
            content_type='application/json',
            **self.auth_header,
        )
        response = self.client.get('/api/projects', **self.auth_header)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_dashboard_accessible(self):
        """Dashboard harus bisa diakses dengan token."""
        response = self.client.get('/api/dashboard', **self.auth_header)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('totalProjects', data)
        self.assertIn('assignedToMe', data)
        self.assertIn('recentProjects', data)


class SearchAPITest(TestCase):
    """Pengujian Search API — Praktikum 6."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='search_test@intring.ai',
            password='pass123',
            name='Search Tester',
        )
        res = self.client.post(
            '/api/auth/login',
            data=json.dumps({'email': 'search_test@intring.ai', 'password': 'pass123'}),
            content_type='application/json',
        )
        self.token = res.json()['token']
        self.auth = {'HTTP_AUTHORIZATION': f'Bearer {self.token}'}

        # Buat proyek dan issue untuk ditest
        self.project = Project.objects.create(
            name='AI Search Engine',
            key='ASE',
            owner=self.user,
        )
        Issue.objects.create(
            project=self.project,
            title='Perbaiki fitur pencarian',
            type='bug',
            status='todo',
            reporter=self.user,
        )

    def test_search_returns_results(self):
        """Search harus mengembalikan hasil yang relevan."""
        response = self.client.get('/api/search?q=AI', **self.auth)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('projects', data)
        self.assertIn('issues', data)
        self.assertGreater(len(data['projects']), 0)

    def test_search_issue_by_keyword(self):
        """Search berdasarkan keyword di judul issue."""
        response = self.client.get('/api/search?q=pencarian', **self.auth)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(len(data['issues']), 0)

    def test_search_short_query_returns_empty(self):
        """Query kurang dari 2 karakter harus kembalikan hasil kosong."""
        response = self.client.get('/api/search?q=a', **self.auth)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['issues']), 0)
        self.assertEqual(len(data['projects']), 0)

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.http import HttpResponseRedirect
from rest_framework.routers import DefaultRouter
from core import views_extra
from core.views_extra import ProjectViewSet, IssueViewSet

FRONTEND_DIR = settings.BASE_DIR.parent / 'Frontend'

# ── DRF Router — Praktikum 10: RESTful API dengan ViewSet ────────────────────
router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='viewset-project')
router.register(r'issues',   IssueViewSet,   basename='viewset-issue')

urlpatterns = [
    path('admin/', admin.site.urls),

    # ── REST API (APIView — endpoint utama) ──────────────────────────────────
    path('api/', include('core.urls')),

    # ── REST API v2 (ViewSet + Router — Praktikum 10) ───────────────────────
    path('api/v2/', include(router.urls)),

    # ── Django Form Views (data entry praktikum) ─────────────────────────────
    path('data-entry/', include('data_entry.urls')),

    # ── Praktikum 9: Cetak Dokumen & PDF Viewer ──────────────────────────────
    path('cetak/',    views_extra.halaman_cetak,     name='halaman_cetak'),
    path('pdf-view/', views_extra.halaman_utama_pdf, name='halaman_pdf'),
    path('pdf-file/', views_extra.buka_pdf,          name='buka_pdf_file'),

    # ── Praktikum 9b: Halaman Grafik Chart.js ────────────────────────────────
    path('grafik/',          views_extra.halaman_grafik,  name='halaman_grafik'),
    path('api/data-grafik/', views_extra.data_grafik_api, name='data_grafik'),

    # ── Frontend HTML Files (serve dari Django) ───────────────────────────────
    path('', lambda req: HttpResponseRedirect('/login.html')),
    re_path(r'^(?P<path>.+\.html)$', lambda req, path: serve(req, path, document_root=FRONTEND_DIR)),
    re_path(r'^(?P<path>.+\.js)$',   lambda req, path: serve(req, path, document_root=FRONTEND_DIR)),
    re_path(r'^(?P<path>.+\.css)$',  lambda req, path: serve(req, path, document_root=FRONTEND_DIR)),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) \
  + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Serve uploads dari folder Frontend
urlpatterns += [
    re_path(r'^uploads/(?P<path>.*)$', serve, {
        'document_root': FRONTEND_DIR / 'uploads',
    }),
]

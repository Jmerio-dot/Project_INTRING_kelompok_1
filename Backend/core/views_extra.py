"""
core/views_extra.py
Fitur tambahan dari referensi praktikum:
- Praktikum 9a: Cetak dokumen & PDF viewer
- Praktikum 9b: Data API untuk Chart.js (grafik proyek)
"""
import os
import json
from django.http import JsonResponse, FileResponse, Http404
from django.shortcuts import render
from django.conf import settings
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from .models import Project, Issue, Sprint, ActivityLog
from django.contrib.auth import get_user_model

User = get_user_model()


# ─────────────────────────────────────────────────────────────────────────────
# PRAKTIKUM 9a — Cetak Dokumen & PDF Viewer
# ─────────────────────────────────────────────────────────────────────────────

def halaman_cetak(request):
    """
    View untuk mencetak laporan proyek.
    Praktikum 9: Cetak Dokumen — menggunakan window.print() di browser.
    Template menggunakan @media print CSS untuk menyembunyikan tombol saat print.
    """
    # Ambil data proyek untuk laporan
    project_id = request.GET.get('project_id')
    project = None
    issues  = []
    sprints = []

    if project_id:
        try:
            project = Project.objects.get(pk=project_id)
            issues  = Issue.objects.filter(project=project).select_related('assignee', 'reporter')
            sprints = Sprint.objects.filter(project=project)
        except Project.DoesNotExist:
            pass

    # Statistik untuk laporan
    stats = {
        'total':      issues.count() if issues else 0,
        'todo':       issues.filter(status='todo').count() if issues else 0,
        'in_progress':issues.filter(status='in_progress').count() if issues else 0,
        'in_review':  issues.filter(status='in_review').count() if issues else 0,
        'done':       issues.filter(status='done').count() if issues else 0,
    }
    stats['completion_rate'] = (
        round(stats['done'] / stats['total'] * 100) if stats['total'] else 0
    )

    return render(request, 'core/cetak_dokumen.html', {
        'project':  project,
        'issues':   issues,
        'sprints':  sprints,
        'stats':    stats,
        'title':    f'Laporan Proyek — {project.name}' if project else 'Laporan Semua Proyek',
    })


def buka_pdf(request):
    """
    View untuk membuka file PDF di browser (bukan download).
    Praktikum 9: FileResponse dengan content_type='application/pdf'
    """
    pdf_path = os.path.join(settings.BASE_DIR, 'static', 'dokumen', 'sampel.pdf')
    if not os.path.exists(pdf_path):
        raise Http404("File PDF tidak ditemukan.")
    file_pdf = open(pdf_path, 'rb')
    return FileResponse(file_pdf, content_type='application/pdf')


def halaman_utama_pdf(request):
    """
    Halaman yang menampilkan PDF viewer dengan iframe dan link buka tab baru.
    Praktikum 9: Menampilkan PDF di web.
    """
    return render(request, 'core/lihat_pdf.html', {
        'title': 'Lihat Dokumen PDF',
    })


# ─────────────────────────────────────────────────────────────────────────────
# PRAKTIKUM 9b — Data API untuk Chart.js (Grafik Proyek)
# ─────────────────────────────────────────────────────────────────────────────

def halaman_grafik(request):
    """
    Halaman grafik/analitik proyek menggunakan Chart.js.
    Praktikum 9b: Menampilkan data di web dengan grafik.
    """
    return render(request, 'core/grafik.html', {
        'title': 'Analitik & Grafik Proyek',
    })


def data_grafik_api(request):
    """
    Endpoint JSON untuk Chart.js.
    Praktikum 9b: Data grafik dari Django database.
    Returns:
        - issue_per_status: jumlah issue per status di semua proyek
        - issue_per_priority: jumlah issue per prioritas
        - issue_per_type: jumlah issue per tipe
        - project_activity: 5 proyek dengan issue terbanyak
    """
    # Grafik 1 — Issue per Status
    status_data = {
        'labels': ['To Do', 'In Progress', 'In Review', 'Done'],
        'data': [
            Issue.objects.filter(status='todo').count(),
            Issue.objects.filter(status='in_progress').count(),
            Issue.objects.filter(status='in_review').count(),
            Issue.objects.filter(status='done').count(),
        ],
        'colors': [
            'rgba(100, 116, 139, 0.8)',   # todo - slate
            'rgba(3, 105, 161, 0.8)',      # in_progress - blue
            'rgba(109, 40, 217, 0.8)',     # in_review - violet
            'rgba(21, 128, 61, 0.8)',      # done - green
        ],
    }

    # Grafik 2 — Issue per Prioritas
    priority_data = {
        'labels': ['Critical', 'High', 'Medium', 'Low'],
        'data': [
            Issue.objects.filter(priority='critical').count(),
            Issue.objects.filter(priority='high').count(),
            Issue.objects.filter(priority='medium').count(),
            Issue.objects.filter(priority='low').count(),
        ],
        'colors': [
            'rgba(220, 38, 38, 0.8)',   # critical - red
            'rgba(234, 88, 12, 0.8)',   # high - orange
            'rgba(202, 138, 4, 0.8)',   # medium - yellow
            'rgba(22, 163, 74, 0.8)',   # low - green
        ],
    }

    # Grafik 3 — Proyek dengan issue terbanyak (top 5)
    top_projects = Project.objects.annotate(
        issue_total=Count('issues', distinct=True)
    ).filter(issue_total__gt=0).order_by('-issue_total')[:5]

    project_data = {
        'labels': [p.name for p in top_projects],
        'data':   [p.issue_total for p in top_projects],
        'colors': [
            'rgba(0, 119, 182, 0.8)',
            'rgba(0, 150, 199, 0.8)',
            'rgba(72, 202, 228, 0.8)',
            'rgba(144, 224, 239, 0.8)',
            'rgba(202, 240, 248, 0.8)',
        ],
    }

    # Statistik global
    stats = {
        'total_projects': Project.objects.count(),
        'total_issues':   Issue.objects.count(),
        'total_users':    User.objects.count(),
        'done_rate':      round(
            Issue.objects.filter(status='done').count() /
            max(Issue.objects.count(), 1) * 100
        ),
    }

    return JsonResponse({
        'issue_per_status':   status_data,
        'issue_per_priority': priority_data,
        'project_activity':   project_data,
        'stats':              stats,
    })


# ─────────────────────────────────────────────────────────────────────────────
# PRAKTIKUM 10 — RESTful API (DRF ViewSet + Router)
# Sudah diimplementasikan di core/urls.py menggunakan APIView
# Berikut adalah ViewSet version untuk referensi
# ─────────────────────────────────────────────────────────────────────────────

from rest_framework import viewsets, permissions
from .serializers import IssueSerializer, ProjectSerializer

class ProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet untuk Project — Praktikum 10: RESTful API dengan DRF.
    Otomatis meng-generate endpoint:
      GET    /api/v2/projects/        → list
      POST   /api/v2/projects/        → create
      GET    /api/v2/projects/{id}/   → retrieve
      PUT    /api/v2/projects/{id}/   → update
      PATCH  /api/v2/projects/{id}/  → partial_update
      DELETE /api/v2/projects/{id}/  → destroy
    """
    serializer_class     = ProjectSerializer
    permission_classes   = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Hanya tampilkan proyek milik user atau yang dia ikuti."""
        user = self.request.user
        return Project.objects.filter(
            Q(owner=user) | Q(memberships__user=user)
        ).distinct().order_by('-updated_at')

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class IssueViewSet(viewsets.ModelViewSet):
    """
    ViewSet untuk Issue — Praktikum 10: RESTful API dengan DRF.
    Mendukung filter berdasarkan project, status, priority via query params.
    """
    serializer_class   = IssueSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        accessible_projects = Project.objects.filter(
            Q(owner=user) | Q(memberships__user=user)
        ).distinct()
        qs = Issue.objects.filter(
            project__in=accessible_projects
        ).select_related('assignee', 'reporter', 'sprint', 'project')

        # Filter params
        project_id = self.request.query_params.get('project')
        status     = self.request.query_params.get('status')
        priority   = self.request.query_params.get('priority')
        assignee   = self.request.query_params.get('assignee')

        if project_id: qs = qs.filter(project_id=project_id)
        if status:     qs = qs.filter(status=status)
        if priority:   qs = qs.filter(priority=priority)
        if assignee:   qs = qs.filter(assignee_id=assignee)

        return qs.order_by('-updated_at')

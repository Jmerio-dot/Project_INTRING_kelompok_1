from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # ── Auth ──────────────────────────────────────────────────────────────────
    path('auth/login',    views.LoginView.as_view(),   name='login'),
    path('auth/register', views.RegisterView.as_view(), name='register'),
    path('auth/me',       views.MeView.as_view(),       name='me'),
    path('auth/refresh',  TokenRefreshView.as_view(),   name='token_refresh'),

    # ── Profile ───────────────────────────────────────────────────────────────
    path('profile',       views.ProfileUpdateView.as_view(), name='profile_update'),
    path('profile/photo', views.ProfilePhotoView.as_view(),  name='profile_photo'),

    # ── Users ─────────────────────────────────────────────────────────────────
    path('users',         views.UserListView.as_view(), name='users'),
    path('admin/users',   views.AdminUserListView.as_view(), name='admin_users'),

    # ── Projects ──────────────────────────────────────────────────────────────
    path('projects',                    views.ProjectListCreateView.as_view(), name='projects'),
    path('projects/<int:pk>',           views.ProjectDetailView.as_view(),     name='project_detail'),
    path('projects/<int:pk>/complete',  views.ProjectCompleteView.as_view(),   name='project_complete'),
    path('projects/<int:pk>/board',     views.BoardView.as_view(),             name='project_board'),
    path('projects/<int:pk>/transcript',views.ProjectTranscriptView.as_view(),name='project_transcript'),
    path('projects/<int:pk>/stats',     views.ProjectStatsView.as_view(),      name='project_stats'),

    # ── Project Members ───────────────────────────────────────────────────────
    path('projects/<int:pk>/members',           views.ProjectMembersView.as_view(),      name='project_members'),
    path('projects/<int:pk>/members/<int:uid>', views.ProjectMemberDetailView.as_view(), name='project_member_detail'),

    # ── Sprints ───────────────────────────────────────────────────────────────
    path('projects/<int:pk>/sprints', views.SprintListCreateView.as_view(), name='project_sprints'),
    path('sprints/<int:pk>',          views.SprintDetailView.as_view(),      name='sprint_detail'),

    # ── Issues ────────────────────────────────────────────────────────────────
    path('projects/<int:pk>/issues', views.IssueListCreateView.as_view(), name='project_issues'),
    path('issues/<int:pk>',          views.IssueDetailView.as_view(),      name='issue_detail'),
    path('issues/<int:pk>/status',   views.IssueStatusPatchView.as_view(), name='issue_status'),
    path('issues/reorder',           views.IssuePriorityReorderView.as_view(), name='issue_reorder'),

    # ── Comments ──────────────────────────────────────────────────────────────
    path('issues/<int:pk>/comments', views.CommentListCreateView.as_view(), name='issue_comments'),
    path('comments/<int:pk>',        views.CommentDetailView.as_view(),      name='comment_detail'),

    # ── Attachments ───────────────────────────────────────────────────────────
    path('issues/<int:pk>/attachments', views.AttachmentListCreateView.as_view(), name='issue_attachments'),
    path('attachments/<int:pk>',        views.AttachmentDetailView.as_view(),     name='attachment_detail'),

    # ── Dashboard ─────────────────────────────────────────────────────────────
    path('dashboard',     views.DashboardView.as_view(),    name='dashboard'),
    path('my-issues',     views.MyIssuesView.as_view(),     name='my_issues'),
    path('notifications', views.NotificationView.as_view(), name='notifications'),

    # 🔍 Search (Praktikum 6) ────────────────────────────────────────────────────────
    path('search',        views.SearchView.as_view(),       name='search'),

    # 🤖 Intelligence Creation API ──────────────────────────────────────────────
    path('integration/send-to-creation', views.SendToCreationWebhook.as_view(), name='webhook_send_creation'),
    path('integration/ic-projects',      views.ICProjectsAPIView.as_view(),     name='ic_projects'),
    path('integration/ic-issues/<int:pk>', views.ICIssueDetailAPIView.as_view(), name='ic_issue_detail'),
    path('integration/ic-issues/<int:pk>/update', views.ICIssueUpdateAPIView.as_view(), name='ic_issue_update'),

    # 🌟 Team Submissions & Client Reports ────────────────────────────────────────
    path('projects/<int:pk>/submissions', views.TeamSubmissionListCreateView.as_view(), name='project_submissions'),
    path('submissions/<int:pk>',          views.TeamSubmissionDeleteView.as_view(),     name='submission_delete'),
    path('external-submission/',          views.ExternalSubmissionView.as_view(),       name='external_submission'),
    path('projects/<int:pk>/client-reports', views.ClientReportListCreateView.as_view(),  name='project_reports'),
    path('projects/<int:pk>/client-report',  views.ClientReportListCreateView.as_view(),  name='project_report_create'),
    path('client-reports/<int:pk>',          views.ClientReportDeleteView.as_view(),      name='report_delete'),
    path('report/<str:token>',               views.PublicClientReportView.as_view(),      name='public_report'),
]

"""
Core API Views — semua endpoint REST yang dipakai frontend JS.
Menggantikan Node.js/Express server.js dengan Django REST Framework.
"""
from django.utils import timezone
from django.db.models import Q, Count
from django.contrib.auth import get_user_model
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Project, ProjectMember, Sprint, Issue, Comment, Attachment, ActivityLog
from .serializers import (
    UserSerializer, UserRegisterSerializer, UserProfileUpdateSerializer,
    ProjectSerializer, ProjectCreateSerializer, ProjectMemberSerializer,
    SprintSerializer, IssueSerializer, IssueCreateUpdateSerializer,
    CommentSerializer, AttachmentSerializer, ActivityLogSerializer,
)

User = get_user_model()


def log_activity(user, project=None, issue=None, action='', detail=''):
    ActivityLog.objects.create(
        user=user, project=project, issue=issue,
        action=action, detail=detail,
    )


# ── AUTH ──────────────────────────────────────────────────────────────────────
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email    = request.data.get('email', '')
        password = request.data.get('password', '')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'Email atau kata sandi salah'}, status=status.HTTP_401_UNAUTHORIZED)
        if not user.check_password(password):
            return Response({'error': 'Email atau kata sandi salah'}, status=status.HTTP_401_UNAUTHORIZED)
        refresh = RefreshToken.for_user(user)
        return Response({
            'token':   str(refresh.access_token),
            'refresh': str(refresh),
            'user':    UserSerializer(user, context={'request': request}).data,
        })


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        s = UserRegisterSerializer(data=request.data)
        if not s.is_valid():
            first_err = next(iter(s.errors.values()))[0]
            return Response({'error': str(first_err)}, status=status.HTTP_400_BAD_REQUEST)
        user = s.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'token':   str(refresh.access_token),
            'refresh': str(refresh),
            'user':    UserSerializer(user, context={'request': request}).data,
        }, status=status.HTTP_201_CREATED)


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user, context={'request': request}).data)


# ── PROFILE ───────────────────────────────────────────────────────────────────
class ProfileUpdateView(APIView):
    def put(self, request):
        s = UserProfileUpdateSerializer(request.user, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(UserSerializer(request.user, context={'request': request}).data)


class ProfilePhotoView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        photo = request.FILES.get('photo')
        if not photo:
            return Response({'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)
        request.user.profile_photo = photo
        request.user.save(update_fields=['profile_photo'])
        return Response({'profile_photo_url': request.build_absolute_uri(request.user.profile_photo.url)})


# ── USERS ────────────────────────────────────────────────────────────────────
class UserListView(APIView):
    def get(self, request):
        users = User.objects.all().order_by('name')
        return Response(UserSerializer(users, many=True, context={'request': request}).data)


class AdminUserListView(APIView):
    """Admin endpoint: returns all registered users with full details."""
    def get(self, request):
        from django.db.models import Count
        users = User.objects.all().annotate(
            issue_count=Count('assigned_issues', distinct=True)
        ).order_by('-created_at')
        data = []
        for u in users:
            data.append({
                'id': u.id,
                'name': u.name,
                'email': u.email,
                'avatar': u.avatar,
                'role': u.role,
                'is_active': u.is_active,
                'issue_count': u.issue_count,
                'created_at': u.created_at.isoformat() if u.created_at else None,
                'last_login': u.last_login.isoformat() if u.last_login else None,
            })
        return Response(data)


# ── PROJECTS ─────────────────────────────────────────────────────────────────
class ProjectListCreateView(APIView):
    def get(self, request):
        projects = Project.objects.filter(
            Q(owner=request.user) | Q(memberships__user=request.user)
        ).distinct().order_by('-updated_at')
        return Response(ProjectSerializer(projects, many=True, context={'request': request}).data)

    def post(self, request):
        s = ProjectCreateSerializer(data=request.data, context={'request': request})
        s.is_valid(raise_exception=True)
        project = s.save()
        log_activity(request.user, project=project, action='project_created', detail=f'Created project: {project.name}')
        return Response(ProjectSerializer(project, context={'request': request}).data, status=status.HTTP_201_CREATED)


class ProjectDetailView(APIView):
    def get_project(self, pk):
        try:
            return Project.objects.get(pk=pk)
        except Project.DoesNotExist:
            return None

    def get(self, request, pk):
        p = self.get_project(pk)
        if not p:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(ProjectSerializer(p, context={'request': request}).data)

    def put(self, request, pk):
        p = self.get_project(pk)
        if not p:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)
        for field in ['name', 'key', 'type', 'description', 'status']:
            if field in request.data:
                setattr(p, field, request.data[field])
        p.save()
        return Response(ProjectSerializer(p, context={'request': request}).data)

    def delete(self, request, pk):
        p = self.get_project(pk)
        if not p:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)
        p.delete()
        return Response({'success': True})

class ProjectCompleteView(APIView):
    def post(self, request, pk):
        try:
            p = Project.objects.get(pk=pk)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)
        
        unfinished = Issue.objects.filter(project=p).exclude(status='done').count()
        if unfinished > 0:
            return Response({'error': f'Terdapat {unfinished} issue yang belum selesai. Selesaikan semua issue terlebih dahulu!'}, status=status.HTTP_400_BAD_REQUEST)
            
        completion_type = request.data.get('type', 'temporary')
        p.status = 'archived' if completion_type == 'permanent' else 'done'
        p.save()
        return Response(ProjectSerializer(p, context={'request': request}).data)


# ── TRANSCRIPT ────────────────────────────────────────────────────────────────
class ProjectTranscriptView(APIView):
    def get(self, request, pk):
        try:
            p = Project.objects.get(pk=pk)
        except Project.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        issues = Issue.objects.filter(project=p).select_related(
            'assignee','reporter','sprint'
        ).prefetch_related('attachments__user').order_by('created_at')
        issues_data = IssueSerializer(issues, many=True, context={'request': request}).data
        for i, issue_obj in enumerate(issues):
            issues_data[i]['attachments'] = AttachmentSerializer(issue_obj.attachments.all(), many=True, context={'request': request}).data
        return Response({
            'project': ProjectSerializer(p, context={'request': request}).data,
            'issues':  issues_data,
        })


# ── PROJECT MEMBERS ───────────────────────────────────────────────────────────
class ProjectMembersView(APIView):
    def get(self, request, pk):
        members = ProjectMember.objects.filter(project_id=pk).select_related('user')
        return Response(ProjectMemberSerializer(members, many=True).data)

    def post(self, request, pk):
        user_id = request.data.get('user_id')
        role    = request.data.get('role', 'member')
        ProjectMember.objects.get_or_create(project_id=pk, user_id=user_id, defaults={'role': role})
        return Response({'success': True})


class ProjectMemberDetailView(APIView):
    def delete(self, request, pk, uid):
        ProjectMember.objects.filter(project_id=pk, user_id=uid).delete()
        return Response({'success': True})


# ── SPRINTS ───────────────────────────────────────────────────────────────────
class SprintListCreateView(APIView):
    def get(self, request, pk):
        sprints = Sprint.objects.filter(project_id=pk).annotate(
            issue_count=Count('issues', distinct=True),
            done_count=Count('issues', filter=Q(issues__status='done'), distinct=True),
        )
        return Response(SprintSerializer(sprints, many=True).data)

    def post(self, request, pk):
        data = {**request.data, 'project': pk}
        s = SprintSerializer(data=data)
        if not s.is_valid():
            return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)
        sprint = Sprint.objects.create(
            project_id=pk,
            name=request.data.get('name',''),
            goal=request.data.get('goal',''),
            status='planning',
            start_date=request.data.get('start_date') or None,
            end_date=request.data.get('end_date') or None,
        )
        sprint = Sprint.objects.annotate(
            issue_count=Count('issues', distinct=True),
            done_count=Count('issues', filter=Q(issues__status='done'), distinct=True),
        ).get(id=sprint.id)
        return Response(SprintSerializer(sprint).data, status=status.HTTP_201_CREATED)


class SprintDetailView(APIView):
    def put(self, request, pk):
        try:
            sprint = Sprint.objects.get(pk=pk)
        except Sprint.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        for f in ['name','goal','status','start_date','end_date']:
            if f in request.data:
                setattr(sprint, f, request.data[f] or None)
        sprint.save()
        return Response(SprintSerializer(sprint).data)

    def delete(self, request, pk):
        try:
            sprint = Sprint.objects.get(pk=pk)
        except Sprint.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        sprint.issues.update(sprint=None)
        sprint.delete()
        return Response({'success': True})


# ── ISSUES ────────────────────────────────────────────────────────────────────
class IssueListCreateView(APIView):
    def get(self, request, pk):
        qs = Issue.objects.filter(project_id=pk).select_related(
            'assignee','reporter','sprint','project'
        )
        sprint   = request.query_params.get('sprint')
        backlog  = request.query_params.get('backlog')
        iss_stat = request.query_params.get('status')
        assignee = request.query_params.get('assignee')
        iss_type = request.query_params.get('type')
        if sprint:         qs = qs.filter(sprint_id=sprint)
        if backlog=='true': qs = qs.filter(sprint__isnull=True)
        if iss_stat:       qs = qs.filter(status=iss_stat)
        if assignee:       qs = qs.filter(assignee_id=assignee)
        if iss_type:       qs = qs.filter(type=iss_type)
        qs = qs.order_by('priority_order', '-created_at')
        return Response(IssueSerializer(qs, many=True, context={'request': request}).data)

    def post(self, request, pk):
        try:
            project = Project.objects.get(pk=pk)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)
        title = request.data.get('title','').strip()
        if not title:
            return Response({'error': 'Title is required'}, status=status.HTTP_400_BAD_REQUEST)
        issue = Issue.objects.create(
            project    = project,
            sprint_id  = request.data.get('sprint_id') or None,
            title      = title,
            description= request.data.get('description',''),
            type       = request.data.get('type','task'),
            status     = request.data.get('status','todo'),
            priority   = request.data.get('priority','medium'),
            assignee_id= request.data.get('assignee_id') or None,
            reporter   = request.user,
            labels     = request.data.get('labels',''),
            story_points=request.data.get('story_points') or None,
            due_date   = request.data.get('due_date') or None,
            meaningful_objectives=request.data.get('meaningful_objectives', {}),
            intelligence_experience=request.data.get('intelligence_experience', {}),
            intelligence_implementation=request.data.get('intelligence_implementation', {}),
            creation_status=request.data.get('creation_status', {}),
        )
        project.save()  # bumps updated_at
        log_activity(request.user, project=project, issue=issue,
                     action='issue_created', detail=f'Created: {title}')
        return Response(IssueSerializer(issue, context={'request': request}).data, status=status.HTTP_201_CREATED)


class BoardView(APIView):
    def get(self, request, pk):
        sprint_id = request.query_params.get('sprint_id')
        qs = Issue.objects.filter(project_id=pk).select_related('assignee','reporter','sprint','project')
        if sprint_id:
            qs = qs.filter(sprint_id=sprint_id)
        else:
            active = Sprint.objects.filter(project_id=pk, status='active').first()
            if active:
                qs = qs.filter(sprint=active)
        board = {'todo': [], 'in_progress': [], 'in_review': [], 'done': []}
        for issue in qs.order_by('priority_order'):
            col = issue.status if issue.status in board else 'todo'
            board[col].append(IssueSerializer(issue, context={'request': request}).data)
        return Response(board)


class IssueDetailView(APIView):
    def get_issue(self, pk):
        try:
            return Issue.objects.select_related('assignee','reporter','sprint','project').get(pk=pk)
        except Issue.DoesNotExist:
            return None

    def get(self, request, pk):
        issue = self.get_issue(pk)
        if not issue:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(IssueSerializer(issue, context={'request': request}).data)

    def put(self, request, pk):
        issue = self.get_issue(pk)
        if not issue:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        old_status = issue.status
        for f in ['title','description','type','status','priority','labels','story_points','due_date','meaningful_objectives','intelligence_experience','intelligence_implementation','creation_status']:
            if f in request.data:
                val = request.data[f]
                if not val and f in ['story_points','due_date']:
                    val = None
                elif not val and f in ['meaningful_objectives','intelligence_experience','intelligence_implementation','creation_status']:
                    val = {}
                elif not val:
                    val = ''
                setattr(issue, f, val)
        if 'assignee_id' in request.data:
            issue.assignee_id = request.data['assignee_id'] or None
        if 'sprint_id' in request.data:
            issue.sprint_id = request.data['sprint_id'] or None
        issue.save()
        if old_status != issue.status:
            log_activity(request.user, project=issue.project, issue=issue,
                        action='status_changed', detail=f'{old_status} → {issue.status}')
        return Response(IssueSerializer(issue, context={'request': request}).data)

    def delete(self, request, pk):
        issue = self.get_issue(pk)
        if not issue:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        issue.delete()
        return Response({'success': True})


class IssueStatusPatchView(APIView):
    def patch(self, request, pk):
        try:
            issue = Issue.objects.get(pk=pk)
        except Issue.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        old_status = issue.status
        issue.status = request.data.get('status', issue.status)
        issue.save(update_fields=['status','updated_at'])
        log_activity(request.user, project=issue.project, issue=issue,
                    action='status_changed', detail=f'{old_status} → {issue.status}')
        return Response({'success': True})


# ── COMMENTS ──────────────────────────────────────────────────────────────────
class CommentListCreateView(APIView):
    def get(self, request, pk):
        comments = Comment.objects.filter(issue_id=pk).select_related('user')
        return Response(CommentSerializer(comments, many=True).data)

    def post(self, request, pk):
        content = request.data.get('content','').strip()
        if not content:
            return Response({'error': 'Content required'}, status=status.HTTP_400_BAD_REQUEST)
        comment = Comment.objects.create(issue_id=pk, user=request.user, content=content)
        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)


class CommentDetailView(APIView):
    def delete(self, request, pk):
        try:
            comment = Comment.objects.get(pk=pk, user=request.user)
            comment.delete()
            return Response({'success': True})
        except Comment.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)


# ── ATTACHMENTS ───────────────────────────────────────────────────────────────
class AttachmentListCreateView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, pk):
        attachments = Attachment.objects.filter(issue_id=pk).select_related('user')
        return Response(AttachmentSerializer(attachments, many=True, context={'request': request}).data)

    def post(self, request, pk):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)
        att = Attachment.objects.create(
            issue_id=pk, user=request.user,
            file=file, original_name=file.name,
            mimetype=file.content_type, size=file.size,
        )
        try:
            issue = Issue.objects.get(pk=pk)
            log_activity(request.user, project=issue.project, issue=issue,
                        action='file_attached', detail=f'Attached: {file.name}')
        except Issue.DoesNotExist:
            pass
        return Response(AttachmentSerializer(att, context={'request': request}).data, status=status.HTTP_201_CREATED)


class AttachmentDetailView(APIView):
    def delete(self, request, pk):
        try:
            att = Attachment.objects.get(pk=pk)
            att.file.delete(save=False)
            att.delete()
            return Response({'success': True})
        except Attachment.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)


# ── DASHBOARD ─────────────────────────────────────────────────────────────────
class DashboardView(APIView):
    def get(self, request):
        user     = request.user
        today    = timezone.now().date()
        projects = Project.objects.filter(
            Q(owner=user) | Q(memberships__user=user)
        ).distinct()
        total_projects  = projects.count()
        assigned_to_me  = Issue.objects.filter(assignee=user).exclude(status='done').count()
        in_progress     = Issue.objects.filter(assignee=user, status='in_progress').count()
        completed_today = Issue.objects.filter(assignee=user, status='done', updated_at__date=today).count()
        my_issues = Issue.objects.filter(assignee=user).exclude(status='done').select_related(
            'project','sprint','assignee','reporter'
        ).order_by('-updated_at')[:8]
        recent_projects = projects.order_by('-updated_at')[:6]
        recent_activity = ActivityLog.objects.select_related('user','project','issue').order_by('-created_at')[:10]

        # Chart data: issue status distribution
        from django.db.models import Count
        status_counts = Issue.objects.filter(project__in=projects).values('status').annotate(count=Count('id'))
        status_chart = {s['status']: s['count'] for s in status_counts}

        # Chart data: issue priority distribution
        priority_counts = Issue.objects.filter(project__in=projects).values('priority').annotate(count=Count('id'))
        priority_chart = {p['priority']: p['count'] for p in priority_counts}

        # Admin stats: total registered users
        total_users = User.objects.count()

        return Response({
            'totalProjects':  total_projects,
            'assignedToMe':   assigned_to_me,
            'inProgress':     in_progress,
            'completedToday': completed_today,
            'myIssues':       IssueSerializer(my_issues, many=True, context={'request': request}).data,
            'recentProjects': ProjectSerializer(recent_projects, many=True, context={'request': request}).data,
            'recentActivity': ActivityLogSerializer(recent_activity, many=True).data,
            'statusChart':    status_chart,
            'priorityChart':  priority_chart,
            'totalUsers':     total_users,
        })



# ── SEARCH (Praktikum 6 — pencarian data) ────────────────────────────────────
class SearchView(APIView):
    """
    Endpoint pencarian global — issues, projects, users.
    Implementasi sesuai Praktikum 6: Search Feature.
    Cara kerja:
    1. Terima keyword dari query param ?q=
    2. Lakukan query ke database dengan Q objects (OR conditions)
    3. Kembalikan hasil terfilter per kategori
    """
    def get(self, request):
        q = request.query_params.get('q', '').strip()
        if not q or len(q) < 2:
            return Response({'issues': [], 'projects': [], 'users': [], 'query': q})

        # Filter proyek yang bisa diakses user
        accessible_projects = Project.objects.filter(
            Q(owner=request.user) | Q(memberships__user=request.user)
        ).distinct()

        # Search Issues — berdasarkan title, description, issue_key, labels
        issues = Issue.objects.filter(
            project__in=accessible_projects
        ).filter(
            Q(title__icontains=q)       |
            Q(description__icontains=q) |
            Q(issue_key__icontains=q)   |
            Q(labels__icontains=q)
        ).select_related('assignee','reporter','sprint','project').order_by('-updated_at')[:15]

        # Search Projects — berdasarkan name, key, description
        projects = accessible_projects.filter(
            Q(name__icontains=q)        |
            Q(key__icontains=q)         |
            Q(description__icontains=q)
        ).order_by('-updated_at')[:10]

        # Search Users — berdasarkan name, email (hanya yang punya akses)
        users = User.objects.filter(
            Q(name__icontains=q) |
            Q(email__icontains=q)
        ).order_by('name')[:10]

        return Response({
            'query':    q,
            'issues':   IssueSerializer(issues, many=True, context={'request': request}).data,
            'projects': ProjectSerializer(projects, many=True, context={'request': request}).data,
            'users':    UserSerializer(users, many=True, context={'request': request}).data,
            'total':    issues.count() + projects.count() + users.count(),
        })


# ── PROJECT STATS / ANALYTICS ─────────────────────────────────────────────────
class ProjectStatsView(APIView):
    """
    Statistik lengkap sebuah proyek — untuk halaman analytics.
    """
    def get(self, request, pk):
        try:
            project = Project.objects.get(pk=pk)
        except Project.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        issues = Issue.objects.filter(project=project)

        # Status breakdown
        by_status = {}
        for s, _ in Issue.STATUS_CHOICES:
            by_status[s] = issues.filter(status=s).count()

        # Priority breakdown
        by_priority = {}
        for p, _ in Issue.PRIORITY_CHOICES:
            by_priority[p] = issues.filter(priority=p).count()

        # Type breakdown
        by_type = {}
        for t, _ in Issue.TYPE_CHOICES:
            by_type[t] = issues.filter(type=t).count()

        # Sprint progress
        sprints = Sprint.objects.filter(project=project).order_by('created_at')
        sprint_data = []
        for sp in sprints:
            total = sp.issues.count()
            done  = sp.issues.filter(status='done').count()
            sprint_data.append({
                'id': sp.id, 'name': sp.name, 'status': sp.status,
                'total': total, 'done': done,
                'progress': round(done / total * 100) if total else 0,
            })

        # Top assignees
        from django.db.models import Count as DCount
        assignees = issues.exclude(assignee=None).values(
            'assignee__id', 'assignee__name', 'assignee__avatar'
        ).annotate(count=DCount('id')).order_by('-count')[:5]

        return Response({
            'project':      ProjectSerializer(project, context={'request': request}).data,
            'total_issues': issues.count(),
            'by_status':    by_status,
            'by_priority':  by_priority,
            'by_type':      by_type,
            'sprints':      sprint_data,
            'assignees':    list(assignees),
            'completion_rate': round(
                issues.filter(status='done').count() / issues.count() * 100
            ) if issues.count() else 0,
        })


# ── ISSUE PRIORITY REORDER ────────────────────────────────────────────────────
class IssuePriorityReorderView(APIView):
    """
    Update urutan prioritas issue (untuk drag & drop di Kanban/Backlog).
    Body: { "order": [id1, id2, id3, ...] }
    """
    def post(self, request):
        order = request.data.get('order', [])
        for idx, issue_id in enumerate(order):
            Issue.objects.filter(pk=issue_id).update(priority_order=idx)
        return Response({'success': True, 'updated': len(order)})


# ── NOTIFICATIONS / ACTIVITY FEED ─────────────────────────────────────────────
class NotificationView(APIView):
    """
    Ambil notifikasi / activity log untuk user yang sedang login.
    """
    def get(self, request):
        # Ambil semua activity di project yang user ikuti
        user = request.user
        accessible_projects = Project.objects.filter(
            Q(owner=user) | Q(memberships__user=user)
        ).distinct()

        activities = ActivityLog.objects.filter(
            project__in=accessible_projects
        ).select_related('user','project','issue').order_by('-created_at')[:30]

        # Tandai mana yang "baru" (dalam 24 jam terakhir)
        from datetime import timedelta
        cutoff = timezone.now() - timedelta(hours=24)
        data = ActivityLogSerializer(activities, many=True).data
        for item in data:
            from dateutil import parser as dateparser
            try:
                created = dateparser.parse(item['created_at'])
                item['is_new'] = created >= cutoff
            except Exception:
                item['is_new'] = False

        return Response({
            'notifications': data,
            'unread_count': sum(1 for d in data if d.get('is_new')),
        })


# ── MY ISSUES (untuk halaman profil / personal task view) ────────────────────
class MyIssuesView(APIView):
    """
    Semua issue yang di-assign ke user yang login, dengan filter.
    """
    def get(self, request):
        user   = request.user
        status_filter = request.query_params.get('status', '')
        qs = Issue.objects.filter(assignee=user).select_related(
            'project', 'sprint', 'assignee', 'reporter'
        )
        if status_filter:
            qs = qs.filter(status=status_filter)
        qs = qs.order_by('priority_order', '-updated_at')
        return Response(IssueSerializer(qs, many=True, context={'request': request}).data)

# ─────────────────────────────────────────────────────────────────────────────
# 🤖 INTELLIGENCE CREATION APIS
# ─────────────────────────────────────────────────────────────────────────────

class SendToCreationWebhook(APIView):
    """
    API Mock untuk simulasi pengiriman data project/issue ke "Intelligence Creation".
    Dalam sistem nyata, ini akan men-trigger POST ke web eksternal kelompok lain.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        issue_id = request.data.get('issue_id')
        project_id = request.data.get('project_id')
        
        # Simulasi log aktivitas bahwa data telah terkirim
        issue = Issue.objects.filter(id=issue_id).first()
        if issue:
            log_activity(request.user, issue.project, issue, 'Sent to Intelligence Creation', f'Issue {issue.issue_key} data was dispatched.')

        return Response({
            "status": "success",
            "message": f"Successfully sent project {project_id}, issue {issue_id} to Intelligence Creation team."
        }, status=status.HTTP_200_OK)


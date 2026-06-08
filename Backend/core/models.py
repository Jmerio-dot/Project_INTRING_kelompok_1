"""
Core models — mencerminkan schema database yang sudah ada (Node.js/SQLite)
Semua model ini digunakan oleh REST API untuk frontend JS.
"""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


# ── Custom User ──────────────────────────────────────────────────────────────
class UserManager(BaseUserManager):
    def create_user(self, email, name, password=None, **extra):
        if not email:
            raise ValueError('Email wajib diisi')
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None, **extra):
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        extra.setdefault('role', 'admin')
        return self.create_user(email, name, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [('admin', 'Admin'), ('member', 'Member'), ('viewer', 'Viewer')]

    name           = models.CharField(max_length=150)
    email          = models.EmailField(unique=True)
    avatar         = models.CharField(max_length=10, default='🙂')
    role           = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    bio            = models.TextField(blank=True, default='')
    location       = models.CharField(max_length=200, blank=True, default='')
    website        = models.URLField(blank=True, default='')
    profile_photo  = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
    is_active      = models.BooleanField(default=True)
    is_staff       = models.BooleanField(default=False)
    created_at     = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['name']
    objects = UserManager()

    class Meta:
        db_table = 'core_users'
        verbose_name = 'Pengguna'
        verbose_name_plural = 'Pengguna'

    def __str__(self):
        return f'{self.name} <{self.email}>'

    @property
    def profile_photo_url(self):
        if self.profile_photo:
            return self.profile_photo.url
        return ''


# ── Project ──────────────────────────────────────────────────────────────────
class Project(models.Model):
    TYPE_CHOICES   = [('scrum', 'Scrum'), ('kanban', 'Kanban')]
    STATUS_CHOICES = [('active', 'Active'), ('archived', 'Archived'), ('done', 'Done')]

    name        = models.CharField(max_length=200)
    key         = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True, default='')
    type        = models.CharField(max_length=20, choices=TYPE_CHOICES, default='scrum')
    owner       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_projects')
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    members     = models.ManyToManyField(User, through='ProjectMember', related_name='projects')
    created_at  = models.DateTimeField(default=timezone.now)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table  = 'core_projects'
        ordering  = ['-updated_at']

    def __str__(self):
        return f'[{self.key}] {self.name}'

    @property
    def open_issues_count(self):
        return self.issues.exclude(status='done').count()



class ProjectMember(models.Model):
    ROLE_CHOICES = [('admin', 'Admin'), ('member', 'Member'), ('viewer', 'Viewer')]
    project      = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='memberships')
    user         = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    role         = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')

    class Meta:
        db_table    = 'core_project_members'
        unique_together = ('project', 'user')

    def __str__(self):
        return f'{self.user.name} @ {self.project.key} ({self.role})'


# ── Sprint ────────────────────────────────────────────────────────────────────
class Sprint(models.Model):
    STATUS_CHOICES = [('planning', 'Planning'), ('active', 'Active'), ('done', 'Done')]

    project    = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='sprints')
    name       = models.CharField(max_length=200)
    goal       = models.TextField(blank=True, default='')
    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')
    start_date = models.DateField(null=True, blank=True)
    end_date   = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'core_sprints'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.project.key} – {self.name}'

    @property
    def issue_count(self):
        return self.issues.count()

    @property
    def done_count(self):
        return self.issues.filter(status='done').count()


# ── Issue ─────────────────────────────────────────────────────────────────────
class Issue(models.Model):
    TYPE_CHOICES     = [('task','Task'),('story','Story'),('bug','Bug'),('epic','Epic'),('subtask','Subtask')]
    STATUS_CHOICES   = [('todo','To Do'),('in_progress','In Progress'),('in_review','In Review'),('done','Done')]
    PRIORITY_CHOICES = [('low','Low'),('medium','Medium'),('high','High'),('critical','Critical')]

    project        = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='issues')
    sprint         = models.ForeignKey(Sprint, on_delete=models.SET_NULL, null=True, blank=True, related_name='issues')
    issue_key      = models.CharField(max_length=30)
    title          = models.CharField(max_length=500)
    description    = models.TextField(blank=True, default='')
    type           = models.CharField(max_length=20, choices=TYPE_CHOICES, default='task')
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    priority       = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    assignee       = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_issues')
    reporter       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reported_issues')
    labels         = models.CharField(max_length=500, blank=True, default='')
    story_points   = models.IntegerField(null=True, blank=True)
    due_date       = models.DateField(null=True, blank=True)
    priority_order = models.IntegerField(default=0)

    # Intelligence Issue Workflow Fields
    meaningful_objectives       = models.JSONField(blank=True, null=True, default=dict)
    intelligence_experience     = models.JSONField(blank=True, null=True, default=dict)
    intelligence_implementation = models.JSONField(blank=True, null=True, default=dict)
    creation_status             = models.JSONField(blank=True, null=True, default=dict)

    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'core_issues'
        ordering = ['priority_order', '-created_at']

    def __str__(self):
        return f'{self.issue_key}: {self.title}'

    def save(self, *args, **kwargs):
        if not self.issue_key:
            count = Issue.objects.filter(project=self.project).count()
            self.issue_key = f'{self.project.key}-{count + 1}'
        super().save(*args, **kwargs)


# ── Comment ───────────────────────────────────────────────────────────────────
class Comment(models.Model):
    issue      = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='comments')
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content    = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'core_comments'
        ordering = ['created_at']

    def __str__(self):
        return f'Comment by {self.user.name} on {self.issue.issue_key}'


# ── Attachment ────────────────────────────────────────────────────────────────
class Attachment(models.Model):
    issue         = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='attachments')
    user          = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attachments')
    file          = models.FileField(upload_to='attachments/%Y/%m/')
    original_name = models.CharField(max_length=500)
    mimetype      = models.CharField(max_length=200, blank=True, default='')
    size          = models.IntegerField(default=0)
    created_at    = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'core_attachments'
        ordering = ['-created_at']

    def __str__(self):
        return self.original_name


# ── Activity Log ──────────────────────────────────────────────────────────────
class ActivityLog(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    project    = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    issue      = models.ForeignKey(Issue, on_delete=models.SET_NULL, null=True, blank=True, related_name='activities')
    action     = models.CharField(max_length=100)
    detail     = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'core_activity_log'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.name}: {self.action}'

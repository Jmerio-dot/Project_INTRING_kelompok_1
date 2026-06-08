"""
DRF Serializers untuk semua model Core
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Project, ProjectMember, Sprint, Issue, Comment, Attachment, ActivityLog

User = get_user_model()


# ── User ──────────────────────────────────────────────────────────────────────
class UserSerializer(serializers.ModelSerializer):
    profile_photo_url = serializers.SerializerMethodField()

    class Meta:
        model  = User
        fields = ['id','name','email','avatar','role','bio','location','website','profile_photo_url','created_at']

    def get_profile_photo_url(self, obj):
        req = self.context.get('request')
        if obj.profile_photo and req:
            return req.build_absolute_uri(obj.profile_photo.url)
        return ''


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model  = User
        fields = ['name','email','password']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['name','bio','location','website']


# ── Project ───────────────────────────────────────────────────────────────────
class ProjectMemberSerializer(serializers.ModelSerializer):
    id           = serializers.IntegerField(source='user.id')
    name         = serializers.CharField(source='user.name')
    email        = serializers.CharField(source='user.email')
    avatar       = serializers.CharField(source='user.avatar')
    project_role = serializers.CharField(source='role')

    class Meta:
        model  = ProjectMember
        fields = ['id','name','email','avatar','project_role']


class ProjectSerializer(serializers.ModelSerializer):
    owner_name  = serializers.CharField(source='owner.name', read_only=True)
    open_issues = serializers.SerializerMethodField()
    issue_count = serializers.SerializerMethodField()

    class Meta:
        model  = Project
        fields = ['id','name','key','description','type','status','owner_id','owner_name',
                  'open_issues','issue_count','created_at','updated_at']

    def get_open_issues(self, obj):
        # Use annotated field if present, else calculate
        if hasattr(obj, 'open_issues_ann'):
            return obj.open_issues_ann
        return obj.issues.exclude(status='done').count()

    def get_issue_count(self, obj):
        if hasattr(obj, 'issue_count_ann'):
            return obj.issue_count_ann
        return obj.issues.count()


class ProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Project
        fields = ['name','key','description','type']

    def validate_key(self, value):
        key = value.upper().replace(' ','')
        if Project.objects.filter(key=key).exists():
            raise serializers.ValidationError('Kode proyek sudah dipakai')
        return key

    def create(self, validated_data):
        validated_data['key'] = validated_data['key'].upper()
        validated_data['owner'] = self.context['request'].user
        project = super().create(validated_data)
        ProjectMember.objects.create(project=project, user=project.owner, role='admin')
        return project


# ── Sprint ────────────────────────────────────────────────────────────────────
class SprintSerializer(serializers.ModelSerializer):
    issue_count = serializers.IntegerField(read_only=True)
    done_count  = serializers.IntegerField(read_only=True)

    class Meta:
        model  = Sprint
        fields = ['id','project_id','name','goal','status','start_date','end_date',
                  'issue_count','done_count','created_at']


# ── Issue ─────────────────────────────────────────────────────────────────────
class IssueSerializer(serializers.ModelSerializer):
    assignee_name   = serializers.CharField(source='assignee.name',   read_only=True)
    assignee_avatar = serializers.CharField(source='assignee.avatar', read_only=True)
    reporter_name   = serializers.CharField(source='reporter.name',   read_only=True)
    sprint_name     = serializers.CharField(source='sprint.name',     read_only=True)
    project_name    = serializers.CharField(source='project.name',    read_only=True)
    project_key     = serializers.CharField(source='project.key',     read_only=True)

    class Meta:
        model  = Issue
        fields = ['id','project_id','project_name','project_key','sprint_id','sprint_name',
                  'issue_key','title','description','type','status','priority',
                  'assignee_id','assignee_name','assignee_avatar',
                  'reporter_id','reporter_name',
                  'labels','story_points','due_date','priority_order',
                  'meaningful_objectives', 'intelligence_experience', 'intelligence_implementation', 'creation_status',
                  'created_at','updated_at']


class IssueCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Issue
        fields = ['title','description','type','status','priority',
                  'assignee_id','sprint_id','labels','story_points','due_date','priority_order',
                  'meaningful_objectives', 'intelligence_experience', 'intelligence_implementation', 'creation_status']


# ── Comment ───────────────────────────────────────────────────────────────────
class CommentSerializer(serializers.ModelSerializer):
    user_name   = serializers.CharField(source='user.name',   read_only=True)
    user_avatar = serializers.CharField(source='user.avatar', read_only=True)

    class Meta:
        model  = Comment
        fields = ['id','issue_id','user_id','user_name','user_avatar','content','created_at']


# ── Attachment ────────────────────────────────────────────────────────────────
class AttachmentSerializer(serializers.ModelSerializer):
    uploader_name   = serializers.CharField(source='user.name',   read_only=True)
    uploader_avatar = serializers.CharField(source='user.avatar', read_only=True)
    file_url        = serializers.SerializerMethodField()

    class Meta:
        model  = Attachment
        fields = ['id','issue_id','user_id','uploader_name','uploader_avatar',
                  'original_name','mimetype','size','file_url','created_at']

    def get_file_url(self, obj):
        req = self.context.get('request')
        if obj.file and req:
            return req.build_absolute_uri(obj.file.url)
        return ''


# ── Activity Log ──────────────────────────────────────────────────────────────
class ActivityLogSerializer(serializers.ModelSerializer):
    user_name   = serializers.CharField(source='user.name',   read_only=True)
    user_avatar = serializers.CharField(source='user.avatar', read_only=True)

    class Meta:
        model  = ActivityLog
        fields = ['id','user_id','user_name','user_avatar','project_id','issue_id',
                  'action','detail','created_at']


# ── Dashboard ─────────────────────────────────────────────────────────────────
class DashboardSerializer(serializers.Serializer):
    totalProjects   = serializers.IntegerField()
    assignedToMe    = serializers.IntegerField()
    inProgress      = serializers.IntegerField()
    completedToday  = serializers.IntegerField()
    myIssues        = IssueSerializer(many=True)
    recentProjects  = ProjectSerializer(many=True)
    recentActivity  = ActivityLogSerializer(many=True)

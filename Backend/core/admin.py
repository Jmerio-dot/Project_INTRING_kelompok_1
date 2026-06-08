from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Project, ProjectMember, Sprint, Issue, Comment, Attachment, ActivityLog


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display   = ['name', 'email', 'role', 'is_active', 'is_staff', 'created_at']
    list_filter    = ['role', 'is_active', 'is_staff']
    search_fields  = ['name', 'email']
    ordering       = ['email']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Info Pribadi', {'fields': ('name', 'avatar', 'bio', 'location', 'website', 'profile_photo')}),
        ('Peran & Izin', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Tanggal', {'fields': ('created_at', 'last_login')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('name', 'email', 'password1', 'password2', 'role'),
        }),
    )
    readonly_fields = ['created_at']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display  = ['key', 'name', 'type', 'status', 'owner', 'created_at']
    list_filter   = ['type', 'status']
    search_fields = ['name', 'key']


@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display  = ['project', 'user', 'role']
    list_filter   = ['role']


@admin.register(Sprint)
class SprintAdmin(admin.ModelAdmin):
    list_display  = ['name', 'project', 'status', 'start_date', 'end_date']
    list_filter   = ['status']


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display  = ['issue_key', 'title', 'project', 'type', 'status', 'priority', 'assignee']
    list_filter   = ['type', 'status', 'priority']
    search_fields = ['title', 'issue_key']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display  = ['user', 'issue', 'created_at']


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display  = ['original_name', 'issue', 'user', 'size', 'created_at']


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display  = ['user', 'action', 'project', 'issue', 'created_at']
    list_filter   = ['action']

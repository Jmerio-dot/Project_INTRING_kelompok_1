from django.contrib import admin
from .models import Pengguna, Content


@admin.register(Pengguna)
class PenggunaAdmin(admin.ModelAdmin):
    list_display  = ['nama_lengkap', 'email', 'username', 'role', 'aktif', 'dibuat_pada']
    list_filter   = ['role', 'aktif']
    search_fields = ['nama_lengkap', 'email', 'username']
    readonly_fields = ['dibuat_pada', 'diperbarui']

    def get_queryset(self, request):
        from django.db.models import Count
        return super().get_queryset(request).annotate(content_count=Count('contents'))


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display  = ['judul', 'author', 'set_view', 'kategori', 'date_created', 'view_count']
    list_filter   = ['set_view', 'kategori']
    search_fields = ['judul', 'article', 'author__email']
    raw_id_fields = ['author']
    readonly_fields = ['view_count', 'diperbarui']

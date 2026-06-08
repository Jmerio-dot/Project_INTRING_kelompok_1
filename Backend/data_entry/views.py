"""
data_entry/views.py
View functions untuk form data entry (Parent-Child).
Sesuai requirement praktikum Modul 4.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from .models import Pengguna, Content
from .forms import PenggunaForm, ContentForm


# ── PENGGUNA (Parent) ─────────────────────────────────────────────────────────

def pengguna_list(request):
    """Daftar semua Pengguna dengan search dan pagination."""
    query = request.GET.get('q', '')
    pengguna_qs = Pengguna.objects.annotate(
        jumlah_konten=Count('contents')
    ).order_by('nama_lengkap')
    if query:
        pengguna_qs = pengguna_qs.filter(
            Q(nama_lengkap__icontains=query) |
            Q(email__icontains=query)       |
            Q(username__icontains=query)
        )
    paginator = Paginator(pengguna_qs, 10)
    page_obj  = paginator.get_page(request.GET.get('page'))
    return render(request, 'data_entry/pengguna_list.html', {
        'page_obj': page_obj,
        'query':    query,
        'total':    pengguna_qs.count(),
    })


def set_pengguna(request):
    """
    Form tambah Pengguna baru.
    Sesuai requirement PDF — menggunakan crispy forms.
    """
    if request.method == 'POST':
        form = PenggunaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, f'✅ Pengguna berhasil ditambahkan!')
            return redirect('pengguna_list')
        else:
            messages.error(request, '❌ Periksa kembali isian form.')
    else:
        form = PenggunaForm()
    return render(request, 'data_entry/pengguna_form.html', {'form': form, 'title': 'Tambah Pengguna'})


def edit_pengguna(request, pk):
    """Form edit Pengguna."""
    pengguna = get_object_or_404(Pengguna, pk=pk)
    if request.method == 'POST':
        form = PenggunaForm(request.POST, request.FILES, instance=pengguna)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Pengguna berhasil diperbarui!')
            return redirect('pengguna_list')
    else:
        form = PenggunaForm(instance=pengguna)
    return render(request, 'data_entry/pengguna_form.html', {'form': form, 'title': 'Edit Pengguna', 'pengguna': pengguna})


def hapus_pengguna(request, pk):
    """Hapus Pengguna (dan semua Content-nya via CASCADE)."""
    pengguna = get_object_or_404(Pengguna, pk=pk)
    if request.method == 'POST':
        nama = pengguna.nama_lengkap
        pengguna.delete()  # CASCADE → Content terhapus juga
        messages.success(request, f'✅ Pengguna "{nama}" dan semua kontennya berhasil dihapus.')
        return redirect('pengguna_list')
    return render(request, 'data_entry/pengguna_confirm_delete.html', {'pengguna': pengguna})


def detail_pengguna(request, pk):
    """Detail Pengguna + daftar Content miliknya."""
    pengguna = get_object_or_404(Pengguna, pk=pk)
    contents = pengguna.contents.order_by('-date_created')
    return render(request, 'data_entry/pengguna_detail.html', {
        'pengguna': pengguna,
        'contents': contents,
    })


# ── CONTENT (Child) ───────────────────────────────────────────────────────────

def content_list(request):
    """Daftar semua Content dengan filter dan search."""
    query      = request.GET.get('q', '')
    set_view   = request.GET.get('set_view', '')
    kategori   = request.GET.get('kategori', '')
    author_id  = request.GET.get('author', '')

    content_qs = Content.objects.select_related('author').order_by('-date_created')
    if query:
        content_qs = content_qs.filter(
            Q(judul__icontains=query)   |
            Q(article__icontains=query) |
            Q(author__email__icontains=query)
        )
    if set_view:
        content_qs = content_qs.filter(set_view=set_view)
    if kategori:
        content_qs = content_qs.filter(kategori=kategori)
    if author_id:
        content_qs = content_qs.filter(author_id=author_id)

    paginator = Paginator(content_qs, 10)
    page_obj  = paginator.get_page(request.GET.get('page'))

    return render(request, 'data_entry/content_list.html', {
        'page_obj':  page_obj,
        'query':     query,
        'set_view':  set_view,
        'kategori':  kategori,
        'pengguna_list': Pengguna.objects.filter(aktif=True).order_by('email'),
        'total':     content_qs.count(),
    })


def set_content(request):
    """
    Form tambah Content baru (child dari Pengguna).
    Sesuai requirement PDF: menampilkan form Content dengan dropdown author
    yang menampilkan email karena __str__ Pengguna return email.
    """
    if request.method == 'POST':
        form = ContentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Konten berhasil ditambahkan!')
            return redirect('content_list')
        else:
            messages.error(request, '❌ Periksa kembali isian form.')
    else:
        form = ContentForm()
    return render(request, 'data_entry/content.html', {'form': form, 'title': 'Tambah Konten'})


def edit_content(request, pk):
    """Form edit Content."""
    content = get_object_or_404(Content, pk=pk)
    if request.method == 'POST':
        form = ContentForm(request.POST, request.FILES, instance=content)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Konten berhasil diperbarui!')
            return redirect('content_list')
    else:
        form = ContentForm(instance=content)
    return render(request, 'data_entry/content.html', {'form': form, 'title': 'Edit Konten', 'content': content})


def hapus_content(request, pk):
    """Hapus Content."""
    content = get_object_or_404(Content, pk=pk)
    if request.method == 'POST':
        judul = content.judul
        content.delete()
        messages.success(request, f'✅ Konten "{judul}" berhasil dihapus.')
        return redirect('content_list')
    return render(request, 'data_entry/content_confirm_delete.html', {'content': content})


def detail_content(request, pk):
    """Detail Content."""
    content = get_object_or_404(Content.objects.select_related('author'), pk=pk)
    content.view_count += 1
    content.save(update_fields=['view_count'])
    return render(request, 'data_entry/content_detail.html', {'content': content})


def index(request):
    """Halaman beranda data entry."""
    stats = {
        'total_pengguna': Pengguna.objects.count(),
        'total_content':  Content.objects.count(),
        'published':      Content.objects.filter(set_view='publish').count(),
        'draft':          Content.objects.filter(set_view='not_publish').count(),
    }
    recent_content = Content.objects.select_related('author').order_by('-date_created')[:5]
    return render(request, 'data_entry/index.html', {
        'stats':          stats,
        'recent_content': recent_content,
    })

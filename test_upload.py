import os, sys, django
sys.path.append('C:\\Kuliah\\UIUX_copy\\Backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'intring_backend.settings')
django.setup()

from core.models import Issue, Attachment, User
from django.core.files.uploadedfile import SimpleUploadedFile

u = User.objects.first()
i = Issue.objects.first()

if u and i:
    f = SimpleUploadedFile("test.txt", b"file_content")
    att = Attachment.objects.create(issue=i, user=u, file=f, original_name="test.txt")
    print(f"Created attachment {att.id} with url {att.file.url}")
else:
    print("No user or issue found")

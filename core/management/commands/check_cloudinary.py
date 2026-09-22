"""
Management command: check_cloudinary
Uploads a tiny test file to Cloudinary, then reads it back using the same
logic as MedicalReport.decrypt_file(). Prints diagnostics for each method.

Usage:
    python manage.py check_cloudinary
"""
import os
import io
import requests

from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = "Verify Cloudinary upload/read round-trip and show which public_id is assigned"

    def handle(self, *args, **options):
        from cryptography.fernet import Fernet
        import cloudinary
        import cloudinary.utils
        import cloudinary.uploader

        cloud_name = getattr(settings, 'CLOUDINARY_CLOUD_NAME', '')
        api_key    = getattr(settings, 'CLOUDINARY_API_KEY', '')
        api_secret = getattr(settings, 'CLOUDINARY_API_SECRET', '')

        if not cloud_name:
            self.stderr.write(self.style.ERROR(
                "CLOUDINARY_CLOUD_NAME is not set. Check your .env / Render env vars."
            ))
            return

        self.stdout.write(self.style.SUCCESS("\n=== Cloudinary Connectivity Check ==="))
        self.stdout.write(f"Cloud name : {cloud_name}")
        self.stdout.write(f"API key    : {api_key[:6]}... (len={len(api_key)})")
        self.stdout.write(f"API secret : {api_secret[:4]}... (len={len(api_secret)})\n")

        # 1. Generate tiny encrypted test payload
        key = Fernet.generate_key()
        f_enc = Fernet(key)
        plaintext = b"CLOUDINARY_TEST_PAYLOAD"
        encrypted = f_enc.encrypt(plaintext)

        # 2. Upload via cloudinary.uploader (bypasses Django storage layer)
        self.stdout.write("Uploading test file via cloudinary.uploader ...")
        result = cloudinary.uploader.upload(
            io.BytesIO(encrypted),
            public_id="medical_reports/check_cloudinary_test",
            resource_type="raw",
            overwrite=True,
        )
        actual_public_id  = result.get('public_id', '')
        actual_secure_url = result.get('secure_url', '')
        self.stdout.write(self.style.SUCCESS("Upload SUCCESS"))
        self.stdout.write(f"  public_id  : {actual_public_id}")
        self.stdout.write(f"  secure_url : {actual_secure_url}")
        self.stdout.write(f"  bytes      : {result.get('bytes', '?')}\n")

        # 3. Method 1 - signed URL, extension-free public_id
        self.stdout.write("Method 1: signed cloudinary_url (no extension) ...")
        try:
            url, _ = cloudinary.utils.cloudinary_url(
                actual_public_id,
                resource_type='raw',
                type='upload',
                sign_url=True,
            )
            self.stdout.write(f"  URL: {url}")
            resp = requests.get(url, timeout=15)
            self.stdout.write(f"  HTTP {resp.status_code}")
            if resp.status_code == 200:
                dec = f_enc.decrypt(resp.content)
                assert dec == plaintext
                self.stdout.write(self.style.SUCCESS("  PASS - Method 1 works!"))
            else:
                self.stdout.write(self.style.ERROR(f"  FAIL: {resp.text[:200]}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  FAIL exception: {e}"))

        # 4. Method 2 - private_download_url
        self.stdout.write("\nMethod 2: private_download_url ...")
        try:
            url2 = cloudinary.utils.private_download_url(
                actual_public_id, '',
                resource_type='raw', type='upload',
            )
            self.stdout.write(f"  URL: {url2[:100]}...")
            resp2 = requests.get(url2, timeout=15)
            self.stdout.write(f"  HTTP {resp2.status_code}")
            if resp2.status_code == 200:
                dec2 = f_enc.decrypt(resp2.content)
                assert dec2 == plaintext
                self.stdout.write(self.style.SUCCESS("  PASS - Method 2 works!"))
            else:
                self.stdout.write(self.style.ERROR(f"  FAIL: {resp2.text[:200]}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  FAIL exception: {e}"))

        # 5. Method 3 - HTTP Basic auth delivery URL
        self.stdout.write("\nMethod 3: Admin delivery URL with HTTP Basic auth ...")
        try:
            delivery_url = (
                f"https://res.cloudinary.com/{cloud_name}/raw/upload/{actual_public_id}"
            )
            self.stdout.write(f"  URL: {delivery_url}")
            resp3 = requests.get(delivery_url, auth=(api_key, api_secret), timeout=15)
            self.stdout.write(f"  HTTP {resp3.status_code}")
            if resp3.status_code == 200:
                dec3 = f_enc.decrypt(resp3.content)
                assert dec3 == plaintext
                self.stdout.write(self.style.SUCCESS("  PASS - Method 3 works!"))
            else:
                self.stdout.write(self.style.ERROR(f"  FAIL: {resp3.text[:200]}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  FAIL exception: {e}"))

        # 6. List existing DB reports and their derived public_ids
        self.stdout.write("\nExisting MedicalReport records (latest 10):")
        try:
            from core.models import MedicalReport
            reports = MedicalReport.objects.order_by('-uploaded_date')[:10]
            if not reports:
                self.stdout.write("  (none)")
            for r in reports:
                name = r.report_file.name if r.report_file else 'EMPTY'
                clean = name.lstrip('media/')
                no_ext = os.path.splitext(clean)[0]
                self.stdout.write(
                    f"  id={r.id}  stored='{name}'  -> public_id='{no_ext}'"
                )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  Error: {e}"))

        self.stdout.write(self.style.SUCCESS("\n=== Done ==="))

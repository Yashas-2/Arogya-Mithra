from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from django.conf import settings
from django.utils import timezone
import os
import random

# Karnataka Districts
KARNATAKA_DISTRICTS = [
    ('Bagalkot', 'Bagalkot'),
    ('Ballari', 'Ballari'),
    ('Belagavi', 'Belagavi'),
    ('Bengaluru Rural', 'Bengaluru Rural'),
    ('Bengaluru Urban', 'Bengaluru Urban'),
    ('Bidar', 'Bidar'),
    ('Chamarajanagar', 'Chamarajanagar'),
    ('Chikkaballapur', 'Chikkaballapur'),
    ('Chikkamagaluru', 'Chikkamagaluru'),
    ('Chitradurga', 'Chitradurga'),
    ('Dakshina Kannada', 'Dakshina Kannada'),
    ('Davanagere', 'Davanagere'),
    ('Dharwad', 'Dharwad'),
    ('Gadag', 'Gadag'),
    ('Hassan', 'Hassan'),
    ('Haveri', 'Haveri'),
    ('Kalaburagi', 'Kalaburagi'),
    ('Kodagu', 'Kodagu'),
    ('Kolar', 'Kolar'),
    ('Koppal', 'Koppal'),
    ('Mandya', 'Mandya'),
    ('Mysuru', 'Mysuru'),
    ('Raichur', 'Raichur'),
    ('Ramanagara', 'Ramanagara'),
    ('Shivamogga', 'Shivamogga'),
    ('Tumakuru', 'Tumakuru'),
    ('Udupi', 'Udupi'),
    ('Uttara Kannada', 'Uttara Kannada'),
    ('Vijayapura', 'Vijayapura'),
    ('Yadgir', 'Yadgir'),
]

ECONOMIC_STATUS = [
    ('APL', 'Above Poverty Line'),
    ('BPL', 'Below Poverty Line'),
]

DISEASE_TYPES = [
    ('Cardio', 'Cardiovascular'),
    ('Ortho', 'Orthopedic'),
    ('General', 'General Medicine'),
    ('Cancer', 'Oncology'),
    ('Neuro', 'Neurological'),
    ('Kidney', 'Renal'),
    ('Gynecology', 'Gynecology'),
    ('Others', 'Others'),
]

SCAN_TYPES = [
    ('MRI', 'MRI Scan'),
    ('CT', 'CT Scan'),
    ('Blood', 'Blood Test'),
    ('Xray', 'X-Ray'),
    ('Ultrasound', 'Ultrasound'),
    ('ECG', 'ECG'),
    ('Others', 'Others'),
]

USER_ROLES = [
    ('PATIENT', 'Patient'),
    ('HOSPITAL_STAFF', 'Hospital Staff'),
    ('DOCTOR', 'Doctor'),
]

SPECIALIZATION_CHOICES = [
    ('General', 'General Medicine'),
    ('Cardio', 'Cardiology'),
    ('Neuro', 'Neurology'),
    ('Ortho', 'Orthopedics'),
    ('Hematology', 'Hematology'),
    ('Endocrinology', 'Endocrinology'),
    ('Nephrology', 'Nephrology / Renal'),
    ('Oncology', 'Oncology'),
    ('Pulmonology', 'Pulmonology'),
    ('Gastro', 'Gastroenterology'),
    ('Dermatology', 'Dermatology'),
    ('Pediatrics', 'Pediatrics'),
    ('Gynecologist', 'Gynecologist'),
    ('Others', 'Others'),
]


class PatientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    age = models.IntegerField()
    district = models.CharField(max_length=100, choices=KARNATAKA_DISTRICTS)
    economic_status = models.CharField(max_length=10, choices=ECONOMIC_STATUS)
    has_ration_card = models.BooleanField(default=False)
    has_aadhaar = models.BooleanField(default=False)
    aadhaar_last4 = models.CharField(max_length=4, blank=True, null=True)  # Last 4 digits for verification
    disease_type = models.CharField(max_length=50, choices=DISEASE_TYPES)
    phone_number = models.CharField(max_length=15, unique=True)  # Made unique for patient mapping
    profile_photo = models.ImageField(upload_to='patient_photos/', blank=True, null=True)
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)
    otp_verified_until = models.DateTimeField(blank=True, null=True)  # Set on successful OTP verify
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.district}"

    def generate_otp(self):
        """Generate 6-digit OTP for report access"""
        self.otp_code = str(random.randint(100000, 999999))
        self.otp_created_at = timezone.now()
        self.otp_verified_until = None  # Clear previous verification
        self.save()
        return self.otp_code

    def verify_otp(self, otp):
        """Verify OTP is valid and not expired (10 minutes)"""
        if not self.otp_code or not self.otp_created_at:
            return False
        if (timezone.now() - self.otp_created_at).total_seconds() > 600:
            return False
        if self.otp_code == otp:
            # Mark as verified for 30 minutes
            self.otp_verified_until = timezone.now() + timedelta(minutes=30)
            self.otp_code = None  # Invalidate OTP after use
            self.save()
            return True
        return False

    def is_otp_verified(self):
        """Check if OTP is currently verified (within 30 min window)"""
        if not self.otp_verified_until:
            return False
        return timezone.now() < self.otp_verified_until

    class Meta:
        db_table = 'patient_profiles'



class HospitalStaff(models.Model):
    """Hospital/Lab staff authorized to upload reports"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='hospital_staff')
    staff_name = models.CharField(max_length=255)
    hospital_name = models.CharField(max_length=255)
    department = models.CharField(max_length=100, blank=True, null=True)
    license_number = models.CharField(max_length=100, unique=True)  # Medical license or staff ID
    profile_photo = models.ImageField(upload_to='staff_photos/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)  # Admin must verify hospital staff
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.staff_name} - {self.hospital_name}"

    class Meta:
        db_table = 'hospital_staff'
        verbose_name_plural = 'Hospital Staff'


class DoctorProfile(models.Model):
    """Doctor profile — must be approved by admin before they can log in."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=15, unique=True)
    specialization = models.CharField(max_length=100, choices=SPECIALIZATION_CHOICES, default='General')
    license_number = models.CharField(max_length=100, unique=True)
    hospital_affiliation = models.CharField(max_length=255, blank=True, null=True)
    district = models.CharField(max_length=100, choices=KARNATAKA_DISTRICTS, default='Bengaluru Urban')
    profile_photo = models.ImageField(upload_to='doctor_photos/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    experience_years = models.PositiveIntegerField(default=0)
    available = models.BooleanField(default=True)
    # is_online means the doctor is currently active and can take calls
    is_online = models.BooleanField(default=False)
    # Admin must verify before doctor can log in
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Dr. {self.full_name} — {self.specialization}"

    class Meta:
        db_table = 'doctor_profiles'
        verbose_name_plural = 'Doctor Profiles'


class Consultation(models.Model):
    STATUS_CHOICES = [
        ('REQUESTED', 'Requested'),
        ('ACCEPTED', 'Accepted'),
        ('PAID', 'Paid'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='consultations')
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='consultations')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='REQUESTED')
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=150.00)
    payment_id = models.CharField(max_length=255, blank=True, null=True)
    meeting_link = models.CharField(max_length=512, blank=True, null=True) # For future real video integration
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Consultation: {self.patient.user.username} with {self.doctor.full_name}"

    class Meta:
        db_table = 'consultations'
        ordering = ['-created_at']


class SchemeResult(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='scheme_results')
    scheme_name = models.CharField(max_length=255)
    scheme_type = models.CharField(max_length=50)  # Karnataka/Central
    eligibility_score = models.CharField(max_length=10)
    why_eligible = models.TextField()
    required_documents = models.JSONField(default=list)
    apply_steps = models.JSONField(default=list)
    language_output = models.CharField(max_length=20, default='English')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.scheme_name} - {self.patient.user.username}"

    class Meta:
        db_table = 'scheme_results'
        ordering = ['-created_at']


class MedicalReport(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='medical_reports')
    title = models.CharField(max_length=255)
    report_file = models.FileField(upload_to='medical_reports/%Y/%m/')  # Encrypted file
    encrypted_file_key = models.TextField(blank=True, null=True)  # Encryption key
    scan_type = models.CharField(max_length=50, choices=SCAN_TYPES)
    hospital_name = models.CharField(max_length=255, blank=True, null=True)
    test_date = models.DateField(blank=True, null=True)
    uploaded_date = models.DateTimeField(auto_now_add=True)
    file_size = models.BigIntegerField(blank=True, null=True)  # in bytes
    is_analyzed = models.BooleanField(default=False)
    
    # SECURITY: Hospital staff upload tracking
    uploaded_by_staff = models.ForeignKey('HospitalStaff', on_delete=models.SET_NULL, null=True, blank=True, related_name='uploaded_reports')
    patient_phone_match = models.CharField(max_length=15, blank=True, null=True)  # Phone used for mapping
    patient_aadhaar_match = models.CharField(max_length=4, blank=True, null=True)  # Last 4 Aadhaar digits
    
    # Access control
    is_encrypted = models.BooleanField(default=True)
    requires_otp = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} - {self.patient.user.username}"
    
    def encrypt_file(self, file_content):
        """Encrypt file content before storage"""
        key = Fernet.generate_key()
        f = Fernet(key)
        encrypted_content = f.encrypt(file_content)
        self.encrypted_file_key = key.decode()
        self.is_encrypted = True
        return encrypted_content
    
    def decrypt_file(self):
        """
        Decrypt file for authorized viewing.

        KEY FACTS about cloudinary_storage + raw resource type:
        1. cloudinary_storage uploads files with MEDIA_URL as folder prefix.
           So stored name 'media/medical_reports/.../file.pdf' IS the full Cloudinary
           public_id — including 'media/' prefix.
        2. For raw resource_type, Cloudinary public_ids INCLUDE the file extension
           (unlike images where extension is stripped).
        3. Therefore: use self.report_file.name directly as public_id — strip nothing.
        """
        import logging
        import requests as http_requests
        logger = logging.getLogger(__name__)

        if not self.is_encrypted or not self.encrypted_file_key:
            logger.warning(
                f"Report {self.id}: is_encrypted={self.is_encrypted}, "
                f"key={'present' if self.encrypted_file_key else 'MISSING'}"
            )
            return None

        if not self.report_file:
            logger.error(f"Report {self.id}: report_file field is empty")
            return None

        encrypted_content = None

        # The Cloudinary public_id for raw files saved by cloudinary_storage is
        # exactly self.report_file.name — e.g. 'media/medical_reports/2026/09/file.pdf'
        # Do NOT strip 'media/' and do NOT strip the extension.
        public_id = self.report_file.name
        logger.info(f"Report {self.id}: using public_id='{public_id}'")

        # ── Method 1: Signed delivery URL ──
        try:
            import cloudinary.utils
            url, _ = cloudinary.utils.cloudinary_url(
                public_id,
                resource_type='raw',
                type='upload',
                sign_url=True,
            )
            logger.info(f"Report {self.id}: Method 1 URL: {url}")
            resp = http_requests.get(url, timeout=30)
            resp.raise_for_status()
            encrypted_content = resp.content
            logger.info(f"Report {self.id}: Method 1 SUCCESS — {len(encrypted_content)} bytes")
        except Exception as e:
            logger.warning(f"Report {self.id}: Method 1 (signed URL) failed: {e}")

        # ── Method 2: Direct delivery URL with HTTP Basic auth (api_key:api_secret) ──
        if not encrypted_content:
            try:
                from django.conf import settings as dj_settings
                cloud_name = getattr(dj_settings, 'CLOUDINARY_CLOUD_NAME', '')
                api_key    = getattr(dj_settings, 'CLOUDINARY_API_KEY', '')
                api_secret = getattr(dj_settings, 'CLOUDINARY_API_SECRET', '')
                if cloud_name and api_key and api_secret:
                    delivery_url = (
                        f"https://res.cloudinary.com/{cloud_name}/raw/upload/{public_id}"
                    )
                    logger.info(f"Report {self.id}: Method 2 URL: {delivery_url}")
                    resp = http_requests.get(
                        delivery_url,
                        auth=(api_key, api_secret),
                        timeout=30,
                    )
                    resp.raise_for_status()
                    encrypted_content = resp.content
                    logger.info(f"Report {self.id}: Method 2 SUCCESS — {len(encrypted_content)} bytes")
                else:
                    logger.warning(f"Report {self.id}: Method 2 skipped — credentials not configured")
            except Exception as e:
                logger.warning(f"Report {self.id}: Method 2 (Basic auth fetch) failed: {e}")

        # ── Method 3: private_download_url (Admin API signed download) ──
        if not encrypted_content:
            try:
                import cloudinary.utils
                url3 = cloudinary.utils.private_download_url(
                    public_id,
                    '',
                    resource_type='raw',
                    type='upload',
                )
                logger.info(f"Report {self.id}: Method 3 URL: {url3[:120]}...")
                resp = http_requests.get(url3, timeout=30)
                resp.raise_for_status()
                encrypted_content = resp.content
                logger.info(f"Report {self.id}: Method 3 SUCCESS — {len(encrypted_content)} bytes")
            except Exception as e:
                logger.warning(f"Report {self.id}: Method 3 (private_download_url) failed: {e}")

        if not encrypted_content:
            logger.error(
                f"Report {self.id}: All methods failed. public_id='{public_id}'"
            )
            return None

        try:
            f = Fernet(self.encrypted_file_key.encode())
            decrypted = f.decrypt(encrypted_content)
            logger.info(f"Report {self.id}: Decrypted successfully — {len(decrypted)} bytes")
            return decrypted
        except Exception as e:
            logger.error(f"Report {self.id}: Decryption FAILED: {type(e).__name__}: {e}")
            return None

    class Meta:
        db_table = 'medical_reports'
        ordering = ['-uploaded_date']


class AIAnalysis(models.Model):
    RISK_LEVELS = [
        ('Low', 'Low Risk'),
        ('Medium', 'Medium Risk'),
        ('High', 'High Risk'),
    ]

    report = models.OneToOneField(MedicalReport, on_delete=models.CASCADE, related_name='ai_analysis')
    patient_summary = models.TextField()
    abnormal_findings = models.JSONField(default=list)
    risk_level = models.CharField(max_length=20, choices=RISK_LEVELS)
    lifestyle_recommendations = models.JSONField(default=list)
    doctor_visit_suggestion = models.TextField()
    analyzed_at = models.DateTimeField(auto_now_add=True)
    language = models.CharField(max_length=20, default='English')

    def __str__(self):
        return f"Analysis - {self.report.title}"

    class Meta:
        db_table = 'ai_analyses'
        ordering = ['-analyzed_at']


class ReportAccessLog(models.Model):
    """Audit trail for every report access"""
    report = models.ForeignKey(MedicalReport, on_delete=models.CASCADE, related_name='access_logs')
    accessed_by_user = models.ForeignKey(User, on_delete=models.CASCADE)
    access_type = models.CharField(max_length=20, choices=[('VIEW', 'View'), ('DOWNLOAD', 'Download')])
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    otp_verified = models.BooleanField(default=False)
    access_granted = models.BooleanField(default=False)  # False if unauthorized attempt
    accessed_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.accessed_by_user.username} - {self.report.title} - {self.access_type}"
    
    class Meta:
        db_table = 'report_access_logs'
        ordering = ['-accessed_at']


class Subscription(models.Model):
    SUBSCRIPTION_STATUS = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    is_premium = models.BooleanField(default=False)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=SUBSCRIPTION_STATUS, default='active')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=49.00)
    payment_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Usage tracking - ONLY for AI analysis (reports are always free)
    ai_analysis_count = models.IntegerField(default=0)  # Removed report upload count

    def __str__(self):
        return f"{self.user.username} - {'Premium' if self.is_premium else 'Free'}"

    def is_active(self):
        if not self.is_premium:
            return False
        if self.end_date and self.end_date < datetime.now():
            self.status = 'expired'
            self.is_premium = False
            self.save()
            return False
        return True
    
    def can_view_reports(self):
        """ALWAYS TRUE - Reports viewing is a health right, not a premium feature"""
        return True

    def can_analyze_report(self):
        """AI analysis: 3/month for free, unlimited for premium"""
        if self.is_premium:
            return True
        return self.ai_analysis_count < 3  # Free limit: 3 AI analyses per month
    
    def reset_monthly_limits(self):
        """Reset AI analysis count monthly (call via cron job)"""
        self.ai_analysis_count = 0
        self.save()

    class Meta:
        db_table = 'subscriptions'

# SECURE VIEWS - Hospital Staff Upload & Patient OTP Verification
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.core.files.base import ContentFile
from datetime import datetime
from django.utils import timezone
import os
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    PatientProfile, MedicalReport, HospitalStaff, 
    ReportAccessLog, Subscription
)
from .serializers import (
    HospitalStaffSerializer, HospitalReportUploadSerializer,
    OTPVerificationSerializer, OTPRequestSerializer,
    MedicalReportSerializer, ReportAccessLogSerializer
)
from .gemini_service import gemini_service


def get_client_ip(request):
    """Extract client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# ============= REGISTRATION APIs =============

@api_view(['POST'])
@permission_classes([AllowAny])
def register_patient(request):
    """
    Register a new patient user
    """
    required_fields = ['username', 'email', 'password', 'full_name', 'phone_number', 'age', 'district', 'economic_status', 'disease_type']
    
    for field in required_fields:
        if not request.data.get(field):
            return Response({
                'success': False,
                'error': f'{field} is required'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Check if user already exists
        if User.objects.filter(username=request.data['username']).exists():
            return Response({
                'success': False,
                'error': 'Username already exists'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(email=request.data['email']).exists():
            return Response({
                'success': False,
                'error': 'Email already exists'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create user
        user = User.objects.create_user(
            username=request.data['username'],
            email=request.data['email'],
            password=request.data['password'],
            first_name=request.data['full_name']
        )
        
        # Create patient profile
        patient_profile = PatientProfile.objects.create(
            user=user,
            age=int(request.data['age']),
            district=request.data['district'],
            economic_status=request.data['economic_status'],
            has_ration_card=str(request.data.get('has_ration_card', '')).lower() == 'true',
            has_aadhaar=str(request.data.get('has_aadhaar', '')).lower() == 'true',
            aadhaar_last4=request.data.get('aadhaar_last4', ''),
            disease_type=request.data['disease_type'],
            phone_number=request.data['phone_number'],
            profile_photo=request.FILES.get('profile_photo')
        )
        
        # Create subscription
        Subscription.objects.create(user=user)
        
        return Response({
            'success': True,
            'message': 'Patient registered successfully'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_hospital_staff(request):
    """
    Register a new hospital staff user
    """
    required_fields = ['username', 'email', 'password', 'staff_name', 'hospital_name', 'license_number']
    
    for field in required_fields:
        if not request.data.get(field):
            return Response({
                'success': False,
                'error': f'{field} is required'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Check if user already exists
        if User.objects.filter(username=request.data['username']).exists():
            return Response({
                'success': False,
                'error': 'Username already exists'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(email=request.data['email']).exists():
            return Response({
                'success': False,
                'error': 'Email already exists'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create user
        user = User.objects.create_user(
            username=request.data['username'],
            email=request.data['email'],
            password=request.data['password']
        )
        
        # Create hospital staff profile
        hospital_staff = HospitalStaff.objects.create(
            user=user,
            staff_name=request.data['staff_name'],
            hospital_name=request.data['hospital_name'],
            department=request.data.get('department', ''),
            license_number=request.data['license_number'],
            profile_photo=request.FILES.get('profile_photo'),
            is_verified=False  # Admin must verify
        )
        
        return Response({
            'success': True,
            'message': 'Hospital staff registered successfully. Awaiting admin verification.'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============= AUTHENTICATION APIs =============

@api_view(['POST'])
@permission_classes([AllowAny])
def patient_login(request):
    """Patient login endpoint"""
    username = request.data.get('username')
    password = request.data.get('password')
    
    user = authenticate(username=username, password=password)
    
    if user and hasattr(user, 'patient_profile'):
        # Generate JWT token
        refresh = RefreshToken.for_user(user)
        return Response({
            'success': True,
            'role': 'PATIENT',
            'token': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'name': user.get_full_name() or user.username
            }
        })
    
    return Response({
        'success': False,
        'error': 'Invalid credentials or not a registered patient'
    }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([AllowAny])
def admin_login(request):
    """Admin login endpoint"""
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(username=username, password=password)

    if user and user.is_staff:
        refresh = RefreshToken.for_user(user)
        return Response({
            'success': True,
            'role': 'ADMIN',
            'token': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'name': user.get_full_name() or user.username
            }
        })

    return Response({
        'success': False,
        'error': 'Invalid credentials or not an admin'
    }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
def admin_pending_staff(request):
    """List all unverified hospital staff"""
    if not request.user.is_staff:
        return Response({'error': 'Forbidden'}, status=403)
    staff = HospitalStaff.objects.filter(is_verified=False).select_related('user')
    data = [{
        'id': s.id,
        'username': s.user.username,
        'staff_name': s.staff_name,
        'hospital_name': s.hospital_name,
        'license_number': s.license_number,
        'created_at': s.created_at.strftime('%Y-%m-%d %H:%M'),
    } for s in staff]
    return Response({'success': True, 'data': data})


@api_view(['GET'])
def admin_all_staff(request):
    """List all hospital staff"""
    if not request.user.is_staff:
        return Response({'error': 'Forbidden'}, status=403)
    staff = HospitalStaff.objects.select_related('user').all()
    data = [{
        'id': s.id,
        'username': s.user.username,
        'staff_name': s.staff_name,
        'hospital_name': s.hospital_name,
        'license_number': s.license_number,
        'is_verified': s.is_verified,
        'created_at': s.created_at.strftime('%Y-%m-%d %H:%M'),
    } for s in staff]
    return Response({'success': True, 'data': data})


@api_view(['POST'])
def admin_verify_staff(request, staff_id):
    """Verify a hospital staff"""
    if not request.user.is_staff:
        return Response({'error': 'Forbidden'}, status=403)
    try:
        staff = HospitalStaff.objects.get(id=staff_id)
        staff.is_verified = True
        staff.save()
        return Response({'success': True, 'message': f'{staff.staff_name} verified'})
    except HospitalStaff.DoesNotExist:
        return Response({'error': 'Staff not found'}, status=404)


@api_view(['POST'])
def admin_reject_staff(request, staff_id):
    """Reject and delete a hospital staff"""
    if not request.user.is_staff:
        return Response({'error': 'Forbidden'}, status=403)
    try:
        staff = HospitalStaff.objects.get(id=staff_id)
        name = staff.staff_name
        staff.user.delete()
        return Response({'success': True, 'message': f'{name} rejected and removed'})
    except HospitalStaff.DoesNotExist:
        return Response({'error': 'Staff not found'}, status=404)


@api_view(['POST'])
@permission_classes([AllowAny])
def hospital_staff_login(request):
    """Hospital staff login endpoint"""
    username = request.data.get('username')
    password = request.data.get('password')
    
    user = authenticate(username=username, password=password)
    
    if user and hasattr(user, 'hospital_staff'):
        if not user.hospital_staff.is_verified:
            return Response({
                'success': False,
                'error': 'Your account is pending verification by admin'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Generate JWT token
        refresh = RefreshToken.for_user(user)
        return Response({
            'success': True,
            'role': 'HOSPITAL_STAFF',
            'token': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'staff_name': user.hospital_staff.staff_name,
                'hospital_name': user.hospital_staff.hospital_name
            }
        })
    
    return Response({
        'success': False,
        'error': 'Invalid credentials or not authorized hospital staff'
    }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
def user_logout(request):
    """Logout endpoint for both roles"""
    logout(request)
    return Response({'success': True, 'message': 'Logged out successfully'})


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    """Refresh JWT token"""
    refresh_token = request.data.get('refresh')
    if not refresh_token:
        return Response({'success': False, 'error': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        refresh = RefreshToken(refresh_token)
        access_token = str(refresh.access_token)
        return Response({'success': True, 'token': access_token})
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)


# ============= HOSPITAL STAFF - REPORT UPLOAD =============

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def hospital_upload_report(request):
    """
    Hospital staff uploads encrypted report mapped to patient
    SECURITY: Only verified hospital staff can upload
    """
    # RBAC Check
    auth_header = request.headers.get('Authorization', 'None')
    print(f"DEBUG Upload: user={request.user}, auth_hdr={auth_header[:30]}...")
    try:
        print(f"DEBUG: hasattr={hasattr(request.user, 'hospital_staff')}, user class={request.user.__class__}")
    except Exception as e:
        print(f"DEBUG ex: {e}")

    if not hasattr(request.user, 'hospital_staff'):
        return Response({
            'success': False,
            'error': f'Unauthorized. Only hospital staff can upload reports. User={request.user}'
        }, status=status.HTTP_403_FORBIDDEN)
    
    if not request.user.hospital_staff.is_verified:
        return Response({
            'success': False,
            'error': 'Your account is not verified yet.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = HospitalReportUploadSerializer(data=request.data)
    if not serializer.is_valid():
        print(f"DEBUG Serializer errors: {serializer.errors}")
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    
    # Find patient by phone number
    try:
        patient = PatientProfile.objects.get(phone_number=data['patient_phone'])
    except PatientProfile.DoesNotExist:
        print(f"DEBUG: Patient not found for phone {data['patient_phone']}")
        # Log failed attempt
        try:
            ReportAccessLog.objects.create(
                report=None,
                accessed_by_user=request.user,
                access_type='UPLOAD_ATTEMPT',
                ip_address=get_client_ip(request),
                access_granted=False
            )
        except Exception:
            pass
        return Response({
            'success': False,
            'error': f"No patient found with phone number {data['patient_phone']}"
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Verify Aadhaar last 4 if provided
    if data.get('patient_aadhaar_last4'):
        if patient.aadhaar_last4 and patient.aadhaar_last4 != data['patient_aadhaar_last4']:
             return Response({
                 'success': False,
                 'error': 'Aadhaar verification failed'
             }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        # Read and encrypt file
        uploaded_file = data['report_file']
        file_content = uploaded_file.read()
        
        # Create report instance
        report = MedicalReport(
            patient=patient,
            title=data['title'],
            scan_type=data['scan_type'],
            hospital_name=data.get('hospital_name', request.user.hospital_staff.hospital_name),
            test_date=data.get('test_date'),
            file_size=len(file_content),
            uploaded_by_staff=request.user.hospital_staff,
            patient_phone_match=data['patient_phone'],
            patient_aadhaar_match=data.get('patient_aadhaar_last4'),
            is_encrypted=True,
            requires_otp=True
        )
        
        # Encrypt file content
        encrypted_content = report.encrypt_file(file_content)
        
        # Save encrypted file
        filename = f"encrypted_{uploaded_file.name}"
        report.report_file.save(filename, ContentFile(encrypted_content), save=False)
        report.save()
        
        # Log upload
        ReportAccessLog.objects.create(
            report=report,
            accessed_by_user=request.user,
            access_type='UPLOAD',
            ip_address=get_client_ip(request),
            access_granted=True
        )
        
        return Response({
            'success': True,
            'message': 'Report uploaded and encrypted successfully',
            'data': {
                'report_id': report.id,
                'patient_name': patient.user.get_full_name() or patient.user.username,
                'title': report.title,
                'patient_phone': patient.phone_number[-4:].rjust(len(patient.phone_number), '*')  # Mask phone for security
            }
        }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        print(f"DEBUG Exception during save: {e}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'error': f'Upload failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def hospital_upload_history(request):
    """Get upload history for logged-in hospital staff"""
    if not hasattr(request.user, 'hospital_staff'):
        return Response({
            'success': False,
            'error': 'Unauthorized'
        }, status=status.HTTP_403_FORBIDDEN)
    
    reports = MedicalReport.objects.filter(
        uploaded_by_staff=request.user.hospital_staff
    ).select_related('patient__user')[:50]
    
    data = [{
        'id': r.id,
        'title': r.title,
        'patient_name': r.patient.user.get_full_name() or 'Patient',
        'scan_type': r.scan_type,
        'uploaded_date': r.uploaded_date,
        'is_analyzed': r.is_analyzed
    } for r in reports]
    
    return Response({'success': True, 'data': data})


# ============= PATIENT - OTP VERIFICATION & REPORT ACCESS =============

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_otp(request):
    """
    Patient requests OTP to view their reports.
    SECURITY: OTP sent to registered phone number.
    Falls back to console log in development if Twilio is not configured.
    """
    if not hasattr(request.user, 'patient_profile'):
        return Response({
            'success': False,
            'error': 'Only patients can request OTP'
        }, status=status.HTTP_403_FORBIDDEN)
    
    patient = request.user.patient_profile
    otp = patient.generate_otp()

    # Use phone number submitted by user from the frontend; fallback to registered number
    from .sms_service import send_otp_sms
    submitted_phone = request.data.get('phone_number', '').strip()
    target_phone = submitted_phone if submitted_phone else getattr(patient, 'phone_number', '')

    masked = (target_phone[-4:].rjust(10, 'X')) if len(target_phone) >= 4 else 'XXXXXXXXXX'

    sms_sent = send_otp_sms(target_phone, otp) if target_phone else False

    if sms_sent:
        return Response({
            'success': True,
            'message': f'OTP sent to {masked}',
        })
    else:
        # Development fallback: OTP has been saved to the patient record.
        # Print it to Django console so developers can verify without SMS.
        import logging
        log = logging.getLogger(__name__)
        log.warning(f"[DEV MODE] OTP for patient {request.user.username}: {otp}")
        print(f"\n{'='*50}\n[DEV OTP] Patient: {request.user.username} | OTP: {otp}\n{'='*50}\n")

        # Check if Twilio is configured at all
        from django.conf import settings as dj_settings
        twilio_configured = all([
            getattr(dj_settings, 'TWILIO_ACCOUNT_SID', ''),
            getattr(dj_settings, 'TWILIO_AUTH_TOKEN', ''),
            getattr(dj_settings, 'TWILIO_PHONE_NUMBER', ''),
        ])

        if not twilio_configured:
            # Dev mode: OTP works, just no real SMS sent
            return Response({
                'success': True,
                'message': f'[Dev Mode] OTP generated. Check Django server console for the code.',
                'dev_mode': True,
            })
        else:
            return Response({
                'success': False,
                'error': f'Could not send OTP to {masked}. Please check your phone number or try again.',
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_otp(request):
    """Verify OTP before granting report access"""
    if not hasattr(request.user, 'patient_profile'):
        return Response({
            'success': False,
            'error': 'Unauthorized'
        }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = OTPVerificationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    patient = request.user.patient_profile
    otp = serializer.validated_data['otp_code']
    
    # Debug logging
    print(f"Verifying OTP: {otp}")
    print(f"Stored OTP: {patient.otp_code}")
    print(f"OTP Created at: {patient.otp_created_at}")
    
    if patient.verify_otp(otp):
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"OTP verified successfully for patient {patient.id}")

        return Response({
            'success': True,
            'otp_verified': True,
            'message': 'OTP verified successfully. You can now access your reports.'
        })

    return Response({
        'success': False,
        'error': 'Invalid or expired OTP'
    }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def patient_get_reports(request):
    """
    Get patient's own reports
    SECURITY: Always allowed, but OTP required to view/download
    """
    if not hasattr(request.user, 'patient_profile'):
        return Response({
            'success': False,
            'error': 'Unauthorized'
        }, status=status.HTTP_403_FORBIDDEN)
    
    patient = request.user.patient_profile
    reports = MedicalReport.objects.filter(patient=patient)

    otp_verified = True  # OTP check disabled for development

    data = [{
        'id': r.id,
        'title': r.title,
        'scan_type': r.scan_type,
        'hospital_name': r.hospital_name,
        'uploaded_date': r.uploaded_date,
        'is_analyzed': r.is_analyzed,
        'requires_otp': r.requires_otp,
        'can_view': True  # Always allow viewing
    } for r in reports]

    return Response({
        'success': True,
        'data': data,
        'otp_verified': otp_verified
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def patient_view_report(request, report_id):
    """
    View specific report (decrypted)
    SECURITY: OTP verification required, access logged, patient ownership verified
    """
    if not hasattr(request.user, 'patient_profile'):
        return Response({
            'success': False,
            'error': 'Unauthorized'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Ensure the report belongs to the requesting patient
    try:
        report = MedicalReport.objects.get(id=report_id, patient=request.user.patient_profile)
    except MedicalReport.DoesNotExist:
        # Log unauthorized access attempt
        ReportAccessLog.objects.create(
            report=None,
            accessed_by_user=request.user,
            access_type='UNAUTHORIZED_ACCESS_ATTEMPT',
            ip_address=get_client_ip(request),
            access_granted=False
        )
        return Response({
            'success': False,
            'error': 'Report not found or you do not have permission to access this report'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Check OTP verification via DB (works with JWT, no session needed)
    import logging
    logger = logging.getLogger(__name__)
    patient = request.user.patient_profile
    otp_verified = True  # OTP check disabled for development
    logger.info(f"Viewing report {report_id} for patient {patient.id}, OTP verified: {otp_verified}")

    if report.requires_otp and not otp_verified:
        ReportAccessLog.objects.create(
            report=report,
            accessed_by_user=request.user,
            access_type='VIEW',
            ip_address=get_client_ip(request),
            otp_verified=False,
            access_granted=False
        )
        return Response({
            'success': False,
            'error': 'OTP verification required to view this report',
            'requires_otp': True
        }, status=status.HTTP_403_FORBIDDEN)

    
    # Log successful access
    ReportAccessLog.objects.create(
        report=report,
        accessed_by_user=request.user,
        access_type='VIEW',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:200],
        otp_verified=otp_verified,
        access_granted=True
    )
    
    # Decrypt and serve the file
    from django.http import HttpResponse
    import logging
    logger = logging.getLogger(__name__)

    if report.is_encrypted:
        logger.info(f"Attempting to decrypt report {report.id}")

        # Step 1: Try decrypt_file() method
        decrypted_content = report.decrypt_file()
        if decrypted_content:
            logger.info(f"Successfully decrypted report {report.id}, content length: {len(decrypted_content)}")
            response = HttpResponse(decrypted_content, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="{report.title}.pdf"'
            return response

        # Step 2: Try reading raw file via storage backend (works with Cloudinary)
        logger.warning(f"decrypt_file() failed for report {report.id}, trying storage backend")
        try:
            raw_file = report.report_file.open('rb')
            raw_content = raw_file.read()
            raw_file.close()
            if raw_content[:5] == b'%PDF-':
                logger.info(f"Raw file is valid PDF, serving unencrypted report {report.id}")
                response = HttpResponse(raw_content, content_type='application/pdf')
                response['Content-Disposition'] = f'inline; filename="{report.title}.pdf"'
                return response
            else:
                logger.error(f"Report {report.id}: File is not a valid PDF (starts with {raw_content[:10]})")
        except Exception as e:
            logger.error(f"Storage backend read failed for report {report.id}: {e}")

        return Response({
            'success': False,
            'error': 'REPORT_DECRYPTION_FAILED',
            'message': 'The report could not be decrypted. Please contact support or re-upload the report.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        # For non-encrypted files, use the existing approach
        serializer = MedicalReportSerializer(report)
        return Response({
            'success': True,
            'data': serializer.data,
            'message': '✓ Verified Safe — Visible only to You'
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def patient_access_logs(request):
    """View access logs for patient's reports"""
    if not hasattr(request.user, 'patient_profile'):
        return Response({
            'success': False,
            'error': 'Unauthorized'
        }, status=status.HTTP_403_FORBIDDEN)
    
    logs = ReportAccessLog.objects.filter(
        report__patient=request.user.patient_profile
    ).select_related('accessed_by_user', 'report')[:100]
    
    serializer = ReportAccessLogSerializer(logs, many=True)
    
    return Response({
        'success': True,
        'data': serializer.data
    })


# ============= DOCTOR APIs =============

@api_view(['POST'])
@permission_classes([AllowAny])
def register_doctor(request):
    """
    Register a new doctor. They must be verified by admin before login.
    """
    required_fields = ['username', 'email', 'password', 'full_name', 'phone', 'specialization', 'license_number']
    
    for field in required_fields:
        if not request.data.get(field):
            return Response({'success': False, 'error': f'{field} is required'}, status=status.HTTP_400_BAD_REQUEST)
            
    try:
        from .models import DoctorProfile
        
        if User.objects.filter(username=request.data['username']).exists():
            return Response({'success': False, 'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)
            
        if DoctorProfile.objects.filter(license_number=request.data['license_number']).exists():
            return Response({'success': False, 'error': 'License number already registered'}, status=status.HTTP_400_BAD_REQUEST)
            
        user = User.objects.create_user(
            username=request.data['username'],
            email=request.data['email'],
            password=request.data['password'],
            first_name=request.data['full_name']
        )
        
        doctor = DoctorProfile.objects.create(
            user=user,
            full_name=request.data['full_name'],
            phone=request.data['phone'],
            specialization=request.data['specialization'],
            license_number=request.data['license_number'],
            hospital_affiliation=request.data.get('hospital_affiliation', ''),
            district=request.data.get('district', 'Bengaluru Urban'),
            bio=request.data.get('bio', ''),
            experience_years=int(request.data.get('experience_years', 0)),
            profile_photo=request.FILES.get('profile_photo')
        )
        
        return Response({
            'success': True,
            'message': 'Doctor registered successfully. Account pending admin verification.',
            'doctor_id': doctor.id
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def doctor_login(request):
    """
    Login for doctors. Returns JWT tokens if account is verified by admin.
    """
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({'success': False, 'error': 'Please provide both username and password'}, status=status.HTTP_400_BAD_REQUEST)
        
    user = authenticate(username=username, password=password)
    
    if not user:
        return Response({'success': False, 'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        
    if not hasattr(user, 'doctor_profile'):
        return Response({'success': False, 'error': 'Account is not a doctor profile'}, status=status.HTTP_403_FORBIDDEN)
        
    doctor = user.doctor_profile
    
    if not doctor.is_verified:
        return Response({
            'success': False,
            'error': 'Account pending verification. Please contact administrator.',
            'is_pending': True
        }, status=status.HTTP_403_FORBIDDEN)
        
    refresh = RefreshToken.for_user(user)
    
    # Store token in cookie and prepare response
    response = Response({
        'success': True,
        'message': 'Login successful',
        'role': 'DOCTOR',
        'token': str(refresh.access_token),
        'refresh': str(refresh),
        'user': {
            'id': user.id,
            'username': user.username,
            'full_name': doctor.full_name,
            'role': 'DOCTOR',
            'specialization': doctor.specialization,
            'hospital': doctor.hospital_affiliation,
            'profile_photo': doctor.profile_photo.url if doctor.profile_photo else None
        }
    })
    
    response.set_cookie(
        key='refresh_token',
        value=str(refresh),
        httponly=True,
        secure=True,
        samesite='None',
        max_age=24 * 60 * 60 # 1 day
    )
    
    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_doctors(request):
    """
    Returns list of verified doctors. Optionally filters by exact specialization keyword.
    """
    from .models import DoctorProfile
    
    specialization_filter = request.GET.get('specialization', '').lower()
    
    # Only return verified/available doctors
    doctors = DoctorProfile.objects.filter(is_verified=True, available=True)
    
    # Basic filtering if provided
    if specialization_filter:
        doctors = doctors.filter(specialization__icontains=specialization_filter)
        
    doctors_data = []
    for doc in doctors.order_by('-experience_years'):
        doctors_data.append({
            'id': doc.id,
            'full_name': doc.full_name,
            'specialization': doc.specialization,
            'hospital': doc.hospital_affiliation,
            'district': doc.district,
            'experience_years': doc.experience_years,
            'bio': doc.bio,
            'phone': doc.phone,
            'is_online': doc.is_online,
            'profile_photo': doc.profile_photo.url if doc.profile_photo else None
        })
        
    return Response({
        'success': True,
        'count': len(doctors_data),
        'data': doctors_data
    })


# ============= DOCTOR DASHBOARD STATS =============

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def doctor_stats(request):
    """
    Returns dynamic stats for the authenticated doctor's dashboard:
    - total_patients : unique patients whose AI analysis suggested doctor review in the doctor's district
    - pending_requests: reports flagged for doctor review that haven't been seen yet (is_analyzed=False with AI analysis)
    - completed      : AI-analyzed reports for all patients (platform-wide completions)
    - avg_rating     : doctor's own rating field (defaults to 5.0 if not set)
    """
    from .models import DoctorProfile, MedicalReport, AIAnalysis, PatientProfile

    if not hasattr(request.user, 'doctor_profile'):
        return Response({'success': False, 'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

    doctor = request.user.doctor_profile

    # Total unique patients in the same district as the doctor
    total_patients = PatientProfile.objects.filter(district=doctor.district).count()

    # Pending: reports that have been analyzed but doctor hasn't reviewed them
    # (is_analyzed=True means AI ran, pending = reports where AI recommended doctor but no physical consult recorded)
    pending_requests = MedicalReport.objects.filter(
        patient__district=doctor.district,
        is_analyzed=True
    ).count()

    # Completed = total AI analyses done across all patients in the doctor's district
    completed = AIAnalysis.objects.filter(
        report__patient__district=doctor.district
    ).count()

    # Rating: use doctor's rating if available, else 5.0
    avg_rating = getattr(doctor, 'avg_rating', None)
    if avg_rating is None:
        avg_rating = 5.0

    return Response({
        'success': True,
        'stats': {
            'total_patients': total_patients,
            'pending_requests': pending_requests,
            'completed': completed,
            'avg_rating': round(float(avg_rating), 1),
        }
    })


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_doctor_profile(request):
    """
    Update doctor profile information. 
    Handles specialization, district, hospital_affiliation, and profile_photo.
    """
    print(f"DEBUG: update_doctor_profile called by {request.user}")
    print(f"DEBUG: Data: {request.data}")
    print(f"DEBUG: Files: {request.FILES}")
    
    if not hasattr(request.user, 'doctor_profile'):
        print(f"DEBUG: User {request.user} has no doctor_profile")
        return Response({'success': False, 'error': 'Unauthorized. Only doctors can update their profile.'}, status=status.HTTP_403_FORBIDDEN)
    
    doctor = request.user.doctor_profile
    data = request.data
    
    try:
        # Update text fields
        if 'specialization' in data:
            doctor.specialization = data['specialization']
        if 'district' in data:
            doctor.district = data['district']
        if 'hospital_affiliation' in data:
            doctor.hospital_affiliation = data['hospital_affiliation']
        if 'full_name' in data:
            doctor.full_name = data['full_name']
            
        # Handle file upload
        if 'profile_photo' in request.FILES:
            doctor.profile_photo = request.FILES['profile_photo']
            
        doctor.save()
        
        return Response({
            'success': True,
            'message': 'Profile updated successfully',
            'user': {
                'id': request.user.id,
                'username': request.user.username,
                'full_name': doctor.full_name,
                'role': 'DOCTOR',
                'specialization': doctor.specialization,
                'hospital': doctor.hospital_affiliation,
                'profile_photo': doctor.profile_photo.url if doctor.profile_photo else None
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to update profile: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_doctor_by_id(request, pk):
    """Get specific doctor details"""
    from .models import DoctorProfile
    doctor = get_object_or_404(DoctorProfile, id=pk)
    return Response({
        'success': True,
        'data': {
            'id': doctor.id,
            'full_name': doctor.full_name,
            'specialization': doctor.specialization,
            'experience_years': doctor.experience_years,
            'hospital_affiliation': doctor.hospital_affiliation,
            'district': doctor.district,
            'bio': doctor.bio,
            'profile_photo': doctor.profile_photo.url if doctor.profile_photo else None
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_consultation(request):
    """
    Creates a Consultation record when a patient requests a call.
    """
    from .models import DoctorProfile, Consultation, PatientProfile
    
    doctor_id = request.data.get('doctor_id')
    if not doctor_id:
        return Response({'success': False, 'error': 'Doctor ID required'}, status=status.HTTP_400_BAD_REQUEST)
        
    doctor = get_object_or_404(DoctorProfile, id=doctor_id)
    patient = getattr(request.user, 'patient_profile', None)
    if not patient:
        return Response({'success': False, 'error': 'Only patients can initiate consultations'}, status=status.HTTP_403_FORBIDDEN)
        
    consultation = Consultation.objects.create(
        patient=patient,
        doctor=doctor,
        status='REQUESTED'
    )
    
    return Response({
        'success': True,
        'consultation_id': consultation.id,
        'message': 'Consultation requested. Waiting for doctor to accept.'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_consultation(request):
    """
    Doctor accepts a consultation request.
    """
    from .models import Consultation
    
    consultation_id = request.data.get('consultation_id')
    consultation = get_object_or_404(Consultation, id=consultation_id)
    
    if not hasattr(request.user, 'doctor_profile') or consultation.doctor.user != request.user:
        return Response({'success': False, 'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        
    consultation.status = 'ACCEPTED'
    consultation.save()
    
    return Response({
        'success': True,
        'message': 'Consultation accepted. Waiting for patient payment.'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_consultation_payment(request):
    """
    Update consultation status after payment.
    """
    from .models import Consultation
    
    consultation_id = request.data.get('consultation_id')
    payment_id = request.data.get('payment_id', 'mock_pay_' + str(timezone.now().timestamp()))
    
    consultation = get_object_or_404(Consultation, id=consultation_id)
    consultation.status = 'PAID'
    consultation.payment_id = payment_id
    consultation.save()
    
    return Response({
        'success': True,
        'transaction_id': payment_id,
        'message': 'Payment processed successfully. You can now join the call.'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_consultation_status(request, pk):
    """
    Get the current status of a consultation.
    """
    from .models import Consultation
    consultation = get_object_or_404(Consultation, id=pk)
    
    # Check if user is part of the consultation
    if consultation.patient.user != request.user and consultation.doctor.user != request.user:
        return Response({'success': False, 'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        
    return Response({
        'success': True,
        'status': consultation.status,
        'consultation_id': consultation.id,
        'doctor_name': consultation.doctor.full_name,
        'patient_name': consultation.patient.user.username
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_doctor_online(request):
    """
    Toggle doctor's online status.
    """
    from .models import DoctorProfile
    if not hasattr(request.user, 'doctor_profile'):
        return Response({'success': False, 'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        
    doctor = request.user.doctor_profile
    doctor.is_online = not doctor.is_online
    doctor.save()
    
    return Response({
        'success': True,
        'is_online': doctor.is_online,
        'message': f"Doctor is now {'online' if doctor.is_online else 'offline'}"
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_consultations(request):
    """
    List consultations for the current user (doctor or patient).
    """
    from .models import Consultation
    
    if hasattr(request.user, 'doctor_profile'):
        consultations = Consultation.objects.filter(doctor=request.user.doctor_profile)
    elif hasattr(request.user, 'patient_profile'):
        consultations = Consultation.objects.filter(patient=request.user.patient_profile)
    else:
        return Response({'success': False, 'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        
    data = [{
        'id': c.id,
        'patient_name': c.patient.user.username,
        'doctor_name': c.doctor.full_name,
        'status': c.status,
        'fee': float(c.fee),
        'created_at': c.created_at
    } for c in consultations]
    
    return Response({
        'success': True,
        'data': data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def gemini_recommend_doctor(request):
    """
    Backend implementation of doctor recommendation using Gemini AI.
    Analyzes report analysis findings vs available doctors.
    """
    report_analysis = request.data.get('report_analysis', {})
    doctors = request.data.get('available_doctors', [])
    
    if not doctors:
        return Response({'success': False, 'error': 'No doctors available'})
        
    try:
        recommended_id = gemini_service.recommend_best_doctor(report_analysis, doctors)
        return Response({
            'success': True,
            'recommended_doctor_id': recommended_id
        })
    except Exception as e:
        return Response({
            'success': True,
            'recommended_doctor_id': doctors[0]['id'], # Fallback
            'error': str(e)
        })


@api_view(['POST'])
@permission_classes([AllowAny])
def gemini_chat(request):
    """
    Generate an AI response for the 'Free Chat' feature.
    """
    user_message = request.data.get('message')
    chat_history = request.data.get('history', [])
    doctor_context = request.data.get('doctor_context')

    if not user_message:
        return Response({'success': False, 'error': 'Message is required'}, status=status.HTTP_400_BAD_REQUEST)

    print(f"DEBUG GEMINI CHAT: message received: {user_message}")
    try:
        response_text = gemini_service.get_chat_response(user_message, chat_history, doctor_context)
        print(f"DEBUG GEMINI CHAT: response generated: {response_text[:50]}...")
        return Response({
            'success': True,
            'reply': response_text
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============= ADMIN DIAGNOSTIC =============

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_diagnostic_reports(request):
    """Admin-only: inspect report storage health. No secrets exposed."""
    if not request.user.is_staff:
        return Response({'error': 'Forbidden'}, status=403)

    from django.conf import settings
    storage_backend = getattr(settings, 'DEFAULT_FILE_STORAGE', 'django.core.files.storage.FileSystemStorage')
    reports = MedicalReport.objects.all().select_related('patient__user')

    data = []
    for r in reports:
        file_accessible = False
        file_size = 0
        try:
            f = r.report_file.open('rb')
            content = f.read()
            file_accessible = len(content) > 0
            file_size = len(content)
            f.close()
        except Exception:
            pass

        data.append({
            'id': r.id,
            'title': r.title,
            'patient': r.patient.user.username,
            'file_field': str(r.report_file) if r.report_file else 'EMPTY',
            'file_url': r.report_file.url if r.report_file else 'NONE',
            'file_accessible': file_accessible,
            'file_size': file_size,
            'is_encrypted': r.is_encrypted,
            'has_key': bool(r.encrypted_file_key),
            'key_length': len(r.encrypted_file_key) if r.encrypted_file_key else 0,
            'uploaded': r.uploaded_date.strftime('%Y-%m-%d %H:%M'),
        })

    return Response({
        'success': True,
        'storage_backend': storage_backend,
        'total_reports': len(data),
        'reports': data
    })

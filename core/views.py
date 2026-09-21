from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from datetime import datetime, timedelta
import PyPDF2
import io
import os

from .models import (
    PatientProfile, SchemeResult, MedicalReport, 
    AIAnalysis, Subscription, KARNATAKA_DISTRICTS,
    DISEASE_TYPES, SCAN_TYPES, ECONOMIC_STATUS
)
from .serializers import (
    PatientProfileSerializer, SchemeResultSerializer,
    MedicalReportSerializer, AIAnalysisSerializer,
    SubscriptionSerializer, SchemeCheckRequestSerializer,
    ReportAnalysisRequestSerializer
)
from .gemini_service import gemini_service


# ============= TEMPLATE VIEWS =============
def home_view(request):
    """Landing page"""
    return render(request, 'home.html')

def scheme_checker_view(request):
    """Scheme eligibility checker page"""
    context = {
        'districts': KARNATAKA_DISTRICTS,
        'disease_types': DISEASE_TYPES,
        'economic_status': ECONOMIC_STATUS
    }
    
    # If user is authenticated, try to get their patient profile
    if request.user.is_authenticated:
        try:
            patient_profile = request.user.patient_profile
            context['patient_profile'] = patient_profile
        except:
            # User is authenticated but doesn't have a patient profile
            pass
    
    return render(request, 'scheme_checker.html', context)

def report_vault_view(request):
    """Secure medical report vault with OTP verification"""
    return render(request, 'report_vault_secure.html')

def report_analysis_view(request):
    """AI report analysis page"""
    return render(request, 'report_analysis.html')

def premium_view(request):
    """Premium subscription page"""
    return render(request, 'premium.html')

def admin_dashboard_view(request):
    """Admin dashboard to manage hospital staff"""
    return render(request, 'admin_dashboard.html')

def login_view(request):
    """Dual role login page"""
    return render(request, 'login.html')

@ensure_csrf_cookie
def hospital_dashboard_view(request):
    """Hospital staff dashboard for report upload"""
    # Make sure CSRF cookie is set
    from django.middleware.csrf import get_token
    csrf_token = get_token(request)
    response = render(request, 'hospital_dashboard.html', {'csrf_token': csrf_token})
    return response

def register_view(request):
    """User registration page"""
    return render(request, 'register.html')


# ============= API ENDPOINTS =============

@api_view(['POST'])
def check_scheme_eligibility(request):
    """
    API endpoint to check scheme eligibility using Gemini AI
    """
    serializer = SchemeCheckRequestSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    patient_data = serializer.validated_data
    
    try:
        # Call Gemini AI service
        result = gemini_service.check_scheme_eligibility(patient_data)
        
        # Save result if user is authenticated
        if request.user.is_authenticated:
            try:
                patient_profile = request.user.patient_profile
            except PatientProfile.DoesNotExist:
                # Create patient profile
                patient_profile = PatientProfile.objects.create(
                    user=request.user,
                    age=patient_data['age'],
                    district=patient_data['district'],
                    economic_status=patient_data['economic_status'],
                    has_ration_card=patient_data['has_ration_card'],
                    has_aadhaar=patient_data['has_aadhaar'],
                    disease_type=patient_data['disease_type']
                )
            
            # Save scheme result
            SchemeResult.objects.create(
                patient=patient_profile,
                scheme_name=result['scheme_name'],
                scheme_type=result['scheme_type'],
                eligibility_score=result['eligibility_score'],
                why_eligible=result['why_eligible'],
                required_documents=result['required_documents'],
                apply_steps=result['apply_steps'],
                language_output=result['language_output']
            )
        
        return Response({
            'success': True,
            'data': result
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def upload_medical_report(request):
    """
    DEPRECATED - Report upload moved to Hospital Staff portal only
    Patients cannot upload reports directly for security
    """
    return Response({
        'success': False,
        'error': 'Report upload is only available through Hospital/Lab Staff portal',
        'message': 'For security and verification, reports must be uploaded by authorized hospital staff'
    }, status=status.HTTP_403_FORBIDDEN)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_medical_reports(request):
    """
    Get all medical reports for authenticated user
    """
    try:
        patient_profile = request.user.patient_profile
        reports = MedicalReport.objects.filter(patient=patient_profile)
        serializer = MedicalReportSerializer(reports, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    except PatientProfile.DoesNotExist:
        return Response({
            'success': True,
            'data': []
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_medical_report(request):
    """
    API endpoint to analyze medical report using Gemini AI
    OPTIMIZED: Added caching to avoid redundant processing
    """
    serializer = ReportAnalysisRequestSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    report_id = serializer.validated_data['report_id']
    language = serializer.validated_data.get('language', 'English')
    
    try:
        report = get_object_or_404(MedicalReport, id=report_id, patient__user=request.user)
        
        # This avoids re-processing the same report unnecessarily
        # Look for existing analysis in the same language
        existing_analysis = AIAnalysis.objects.filter(
            report=report,
            language=language
        ).first()
        
        if existing_analysis:
            # Return cached analysis - NO LIMIT CHECK NEEDED
            analysis_serializer = AIAnalysisSerializer(existing_analysis)
            return Response({
                'success': True,
                'data': analysis_serializer.data,
                'cached': True
            }, status=status.HTTP_200_OK)
            
        # --- NEW ANALYSIS REQUIRED ---
        # NOW we check subscription limits before proceeding with Gemini call
        subscription, created = Subscription.objects.get_or_create(user=request.user)
        if not subscription.can_analyze_report():
            return Response({
                'success': False,
                'error': 'Analysis limit reached. Upgrade to Premium for unlimited analysis.',
                'upgrade_required': True
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Decrypt and process PDF
        report_text = ''
        pdf_bytes = None

        # Try decryption via model method (works with Cloudinary + local)
        try:
            decrypted = report.decrypt_file()
            if decrypted:
                pdf_bytes = decrypted
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"decrypt_file() failed for report {report.id}: {e}")

        # If decrypt failed, try reading the file directly via storage backend
        if not pdf_bytes:
            try:
                raw_file = report.report_file.open('rb')
                raw = raw_file.read()
                raw_file.close()
                if raw[:5] == b'%PDF-':
                    pdf_bytes = raw
                else:
                    # File is encrypted but decrypt failed — cannot proceed
                    return Response({
                        'success': False,
                        'error': 'REPORT_DECRYPTION_FAILED',
                        'message': 'The report could not be decrypted. Please contact support or re-upload the report.'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Direct file read failed for report {report.id}: {e}")
                return Response({
                    'success': False,
                    'error': 'REPORT_FILE_NOT_FOUND',
                    'message': 'The report file could not be accessed. It may have been removed during a server restart. Please re-upload the report.'
                }, status=status.HTTP_404_NOT_FOUND)

        if not pdf_bytes:
            return Response({
                'success': False,
                'error': 'REPORT_FILE_EMPTY',
                'message': 'The report file is empty or could not be read.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Extract text from PDF bytes
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
            text_parts = []
            for page in reader.pages:
                try:
                    text_parts.append(page.extract_text() or '')
                except Exception:
                    continue
            report_text = '\n'.join(text_parts).strip()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"PyPDF2 extraction failed for report {report.id}: {e}")

        # If PyPDF2 failed, try PyMuPDF
        if not report_text:
            try:
                import fitz
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                text_parts = []
                for page in doc:
                    text_parts.append(page.get_text())
                report_text = '\n'.join(text_parts).strip()
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"PyMuPDF extraction failed for report {report.id}: {e}")
        
        if not report_text:
            return Response({
                'success': False,
                'error': 'Could not extract text from report'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Preprocess text to optimize for AI analysis speed
        processed_text = preprocess_medical_text(report_text)
        
        # Process with Gemini AI, fallback to rule-based if it fails
        try:
            analysis_result = gemini_service.analyze_medical_report(processed_text, language)
            source = 'AI'
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Gemini AI failed for report {report.id}, using fallback: {e}")
            analysis_result = generate_fallback_analysis(processed_text, language)
            source = 'rule-based'
        
        # Save analysis
        ai_analysis, created = AIAnalysis.objects.update_or_create(
            report=report,
            defaults={
                'patient_summary': analysis_result['patient_summary'],
                'abnormal_findings': analysis_result['abnormal_findings'],
                'risk_level': analysis_result['risk_level'],
                'lifestyle_recommendations': analysis_result['lifestyle_recommendations'],
                'doctor_visit_suggestion': analysis_result['doctor_visit_suggestion'],
                'language': language
            }
        )
        
        # Mark report as analyzed
        report.is_analyzed = True
        report.save()
        
        # Update subscription count
        if created:
            subscription.ai_analysis_count += 1
            subscription.save()
        
        analysis_serializer = AIAnalysisSerializer(ai_analysis)
        
        return Response({
            'success': True,
            'data': analysis_serializer.data,
            'cached': False,
            'source': source
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_subscription_status(request):
    """
    Get subscription status for authenticated user
    """
    subscription, created = Subscription.objects.get_or_create(user=request.user)
    serializer = SubscriptionSerializer(subscription)
    
    return Response({
        'success': True,
        'data': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upgrade_to_premium(request):
    """
    Upgrade user to premium subscription
    """
    payment_id = request.data.get('payment_id')
    
    try:
        subscription, created = Subscription.objects.get_or_create(user=request.user)
        subscription.is_premium = True
        subscription.status = 'active'
        subscription.end_date = datetime.now() + timedelta(days=30)
        subscription.payment_id = payment_id
        subscription.save()
        
        return Response({
            'success': True,
            'message': 'Successfully upgraded to Premium!',
            'data': SubscriptionSerializer(subscription).data
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============= HELPER FUNCTIONS =============

def extract_text_from_pdf(file_path):
    """
    Extract text from a PDF file (handles both plain and Fernet-encrypted files).
    Returns extracted text string, or empty string on failure.
    """
    try:
        with open(file_path, 'rb') as f:
            raw = f.read()

        # Try to decrypt if it looks encrypted (Fernet tokens start with 'gAAAAA')
        try:
            from cryptography.fernet import Fernet, InvalidToken
            # Get encryption key from associated MedicalReport
            from .models import MedicalReport
            report_obj = MedicalReport.objects.filter(
                report_file=file_path.replace('\\', '/').split('media/')[-1]
            ).first()
            if report_obj and report_obj.encrypted_file_key:
                fernet = Fernet(report_obj.encrypted_file_key.encode())
                raw = fernet.decrypt(raw)
        except Exception:
            pass  # Not encrypted or key not found — use raw bytes

        reader = PyPDF2.PdfReader(io.BytesIO(raw))
        text_parts = []
        for page in reader.pages:
            try:
                text_parts.append(page.extract_text() or '')
            except Exception:
                continue
        return '\n'.join(text_parts).strip()

    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"extract_text_from_pdf failed for {file_path}: {e}")
        return ''


def preprocess_medical_text(text, max_chars=4000):
    """
    Clean and truncate medical report text before sending to Gemini AI.
    Removes excess whitespace and limits length to keep within token limits.
    """
    import re
    # Collapse multiple blank lines / spaces
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    text = text.strip()
    # Truncate to max_chars to avoid exceeding Gemini's context window
    if len(text) > max_chars:
        text = text[:max_chars]
    return text


def generate_fallback_analysis(report_text, language='English'):
    """
    Rule-based fallback when AI fails. Parses real medical values from report text
    and provides evidence-based insights. NOT dummy data.
    """
    import re

    KNOWN_RANGES = {
        'hemoglobin': {'unit': 'g/dL', 'low': 12, 'high': 16, 'male_low': 13.5, 'male_high': 17.5},
        'hb': {'unit': 'g/dL', 'low': 12, 'high': 16, 'male_low': 13.5, 'male_high': 17.5},
        'wbc': {'unit': '/uL', 'low': 4000, 'high': 11000},
        'white blood cell': {'unit': '/uL', 'low': 4000, 'high': 11000},
        'platelets': {'unit': '/uL', 'low': 150000, 'high': 400000},
        'platelet': {'unit': '/uL', 'low': 150000, 'high': 400000},
        'blood sugar': {'unit': 'mg/dL', 'low': 70, 'high': 140},
        'glucose': {'unit': 'mg/dL', 'low': 70, 'high': 140},
        'fasting glucose': {'unit': 'mg/dL', 'low': 70, 'high': 100},
        'random glucose': {'unit': 'mg/dL', 'low': 70, 'high': 140},
        'hba1c': {'unit': '%', 'low': 4, 'high': 5.7},
        'hba 1c': {'unit': '%', 'low': 4, 'high': 5.7},
        'glycated hemoglobin': {'unit': '%', 'low': 4, 'high': 5.7},
        'cholesterol': {'unit': 'mg/dL', 'low': 0, 'high': 200},
        'total cholesterol': {'unit': 'mg/dL', 'low': 0, 'high': 200},
        'hdl': {'unit': 'mg/dL', 'low': 40, 'high': 999},
        'ldl': {'unit': 'mg/dL', 'low': 0, 'high': 100},
        'triglycerides': {'unit': 'mg/dL', 'low': 0, 'high': 150},
        'creatinine': {'unit': 'mg/dL', 'low': 0.6, 'high': 1.2},
        'urea': {'unit': 'mg/dL', 'low': 10, 'high': 50},
        'bun': {'unit': 'mg/dL', 'low': 7, 'high': 20},
        'sgpt': {'unit': 'U/L', 'low': 5, 'high': 40},
        'alt': {'unit': 'U/L', 'low': 5, 'high': 40},
        'sgot': {'unit': 'U/L', 'low': 8, 'high': 33},
        'ast': {'unit': 'U/L', 'low': 8, 'high': 33},
        'tsh': {'unit': 'mIU/L', 'low': 0.4, 'high': 4.0},
        'vitamin d': {'unit': 'ng/mL', 'low': 30, 'high': 100},
        'vitamin d3': {'unit': 'ng/mL', 'low': 30, 'high': 100},
        'calcium': {'unit': 'mg/dL', 'low': 8.5, 'high': 10.5},
        'iron': {'unit': 'ug/dL', 'low': 60, 'high': 170},
        'bilirubin': {'unit': 'mg/dL', 'low': 0.1, 'high': 1.2},
        'crp': {'unit': 'mg/L', 'low': 0, 'high': 5},
        'esr': {'unit': 'mm/hr', 'low': 0, 'high': 20},
    }

    EXPLANATIONS = {
        'hemoglobin': 'Hemoglobin carries oxygen in blood. Low levels indicate anemia, causing fatigue and weakness.',
        'hb': 'Hemoglobin carries oxygen in blood. Low levels indicate anemia, causing fatigue and weakness.',
        'wbc': 'White blood cells fight infection. High levels may indicate infection or inflammation.',
        'white blood cell': 'White blood cells fight infection. High levels may indicate infection or inflammation.',
        'platelets': 'Platelets help blood clot. Low levels increase bleeding risk.',
        'blood sugar': 'Blood sugar indicates diabetes risk. High levels suggest diabetes or pre-diabetes.',
        'glucose': 'Blood glucose indicates diabetes risk. High levels suggest diabetes or pre-diabetes.',
        'hba1c': 'HBA1C shows average blood sugar over 3 months. Above 5.7% indicates pre-diabetes.',
        'cholesterol': 'Total cholesterol above 200 mg/dL increases heart disease risk.',
        'hdl': 'HDL is good cholesterol. Low levels increase heart disease risk.',
        'ldl': 'LDL is bad cholesterol. High levels increase heart disease and stroke risk.',
        'triglycerides': 'High triglycerides increase heart disease and pancreatitis risk.',
        'creatinine': 'Creatinine indicates kidney function. High levels suggest kidney problems.',
        'sgpt': 'SGPT/ALT indicates liver health. Elevated levels suggest liver damage.',
        'alt': 'ALT indicates liver health. Elevated levels suggest liver damage.',
        'sgot': 'SGOT/AST indicates liver and heart health. Elevated levels suggest tissue damage.',
        'ast': 'AST indicates liver and heart health. Elevated levels suggest tissue damage.',
        'tsh': 'TSH indicates thyroid function. High levels suggest hypothyroidism, low levels suggest hyperthyroidism.',
        'vitamin d': 'Vitamin D is essential for bone health. Low levels cause bone weakness.',
        'vitamin d3': 'Vitamin D is essential for bone health. Low levels cause bone weakness.',
        'calcium': 'Calcium is vital for bones and nerve function. Abnormal levels need attention.',
        'iron': 'Iron is essential for hemoglobin. Low levels cause anemia.',
        'bilirubin': 'Bilirubin indicates liver function. High levels may cause jaundice.',
        'crp': 'CRP indicates inflammation in the body. High levels suggest infection or autoimmune conditions.',
        'esr': 'ESR indicates inflammation. High levels suggest infection or chronic disease.',
    }

    text_lower = report_text.lower()
    abnormal_findings = []
    risk_level = 'Low'

    for param, info in KNOWN_RANGES.items():
        patterns = [
            rf'{param}[\s:]+(\d+\.?\d*)',
            rf'{param}[\s\-–]+(\d+\.?\d*)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                value = float(match.group(1))
                low = info.get('low', 0)
                high = info.get('high', 999)
                if value < low or value > high:
                    if value < low:
                        severity = 'severe' if value < low * 0.6 else 'moderate' if value < low * 0.8 else 'mild'
                        status = 'Low'
                    else:
                        severity = 'severe' if value > high * 1.5 else 'moderate' if value > high * 1.2 else 'mild'
                        status = 'High'
                    if severity in ('severe', 'moderate'):
                        risk_level = 'High'
                    elif risk_level != 'High' and severity == 'mild':
                        risk_level = 'Medium'
                    abnormal_findings.append({
                        'parameter': param.title(),
                        'value': f'{value} {info["unit"]}',
                        'normal_range': f'{low} - {high} {info["unit"]}',
                        'severity': severity,
                        'simple_explanation': EXPLANATIONS.get(param, f'{param} is {status} than normal range.')
                    })
                break

    if not abnormal_findings:
        summary = 'Based on the extracted report text, no明显 abnormal values were detected by the rule-based analysis. However, this is not a substitute for professional medical review. Please consult a doctor for a comprehensive evaluation.'
    else:
        params = ', '.join([f['parameter'] for f in abnormal_findings])
        summary = f'The report shows {len(abnormal_findings)} abnormal finding(s): {params}. {abnormal_findings[0]["simple_explanation"]} Please consult a healthcare professional for proper evaluation.'

    recommendations = [
        'Maintain a balanced diet rich in fruits, vegetables, and whole grains',
        'Stay hydrated — drink at least 2-3 liters of water daily',
        'Exercise regularly — at least 30 minutes of moderate activity daily',
        'Get adequate sleep — 7-8 hours per night',
        'Follow up with your doctor for a complete clinical evaluation',
    ]

    if risk_level == 'High':
        doctor_suggestion = 'Consult a doctor as soon as possible. The report shows values that need medical attention. Do not ignore these findings.'
    elif risk_level == 'Medium':
        doctor_suggestion = 'Schedule a doctor visit within 1-2 weeks. Some values are outside the normal range and should be evaluated.'
    else:
        doctor_suggestion = 'Continue regular health checkups. No urgent medical attention needed based on this analysis, but consult your doctor for a complete review.'

    if language == 'Kannada':
        summary_kn = summary  # Keep English for now, can be translated later
        return {
            'patient_summary': summary_kn,
            'abnormal_findings': abnormal_findings if abnormal_findings else [{'parameter': 'No Abnormalities Detected', 'value': 'N/A', 'normal_range': 'N/A', 'severity': 'low', 'simple_explanation': 'No明显 abnormal values were detected by rule-based analysis. Please consult a doctor for professional evaluation.'}],
            'risk_level': risk_level,
            'lifestyle_recommendations': recommendations,
            'doctor_visit_suggestion': doctor_suggestion
        }

    return {
        'patient_summary': summary,
        'abnormal_findings': abnormal_findings if abnormal_findings else [{'parameter': 'No Abnormalities Detected', 'value': 'N/A', 'normal_range': 'N/A', 'severity': 'low', 'simple_explanation': 'No明显 abnormal values were detected by rule-based analysis. Please consult a doctor for professional evaluation.'}],
        'risk_level': risk_level,
        'lifestyle_recommendations': recommendations,
        'doctor_visit_suggestion': doctor_suggestion
    }

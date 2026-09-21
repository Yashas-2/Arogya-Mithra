from django.urls import path
from . import views, views_secure

urlpatterns = [
    # Template views
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('hospital-dashboard/', views.hospital_dashboard_view, name='hospital_dashboard'),
    path('scheme-checker/', views.scheme_checker_view, name='scheme_checker'),
    path('report-vault/', views.report_vault_view, name='report_vault'),
    path('report-analysis/', views.report_analysis_view, name='report_analysis'),
    path('premium/', views.premium_view, name='premium'),
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    
    # Authentication APIs
    path('api/auth/patient-login/', views_secure.patient_login, name='patient_login'),
    path('api/auth/hospital-login/', views_secure.hospital_staff_login, name='hospital_login'),
    path('api/auth/admin-login/', views_secure.admin_login, name='admin_login'),
    path('api/auth/doctor-login/', views_secure.doctor_login, name='doctor_login'),
    path('api/auth/register-patient/', views_secure.register_patient, name='register_patient'),
    path('api/auth/register-hospital/', views_secure.register_hospital_staff, name='register_hospital'),
    path('api/auth/register-doctor/', views_secure.register_doctor, name='register_doctor'),
    path('api/auth/logout/', views_secure.user_logout, name='user_logout'),
    path('api/auth/refresh-token/', views_secure.refresh_token, name='refresh_token'),
    
    # Doctor APIs
    path('api/doctors/', views_secure.get_doctors, name='get_doctors'),
    path('api/doctors/<int:pk>/', views_secure.get_doctor_by_id, name='get_doctor_by_id'),
    path('api/doctor/stats/', views_secure.doctor_stats, name='doctor_stats'),
    path('api/doctor/update-profile/', views_secure.update_doctor_profile, name='update_doctor_profile'),
    path('api/doctor/toggle-online/', views_secure.toggle_doctor_online, name='toggle_doctor_online'),
    
    # Consultation & Gemini APIs
    path('api/consultations/initiate/', views_secure.initiate_consultation, name='initiate_consultation'),
    path('api/consultations/accept/', views_secure.accept_consultation, name='accept_consultation'),
    path('api/consultations/<int:pk>/status/', views_secure.get_consultation_status, name='get_consultation_status'),
    path('api/consultations/payment/', views_secure.process_consultation_payment, name='process_payment'),
    path('api/consultations/list/', views_secure.list_consultations, name='list_consultations'),
    path('api/gemini/recommend-doctor/', views_secure.gemini_recommend_doctor, name='gemini_recommend'),
    path('api/gemini/chat/', views_secure.gemini_chat, name='gemini_chat'),
    
    # Hospital Staff APIs (RBAC Protected)
    path('api/hospital/upload-report/', views_secure.hospital_upload_report, name='hospital_upload'),
    path('api/hospital/upload-history/', views_secure.hospital_upload_history, name='hospital_history'),
    path('api/hospital/delete-report/<int:report_id>/', views_secure.hospital_delete_report, name='hospital_delete_report'),
    
    # Patient OTP & Report Access APIs (RBAC Protected)
    path('api/patient/request-otp/', views_secure.request_otp, name='request_otp'),
    path('api/patient/verify-otp/', views_secure.verify_otp, name='verify_otp'),
    path('api/patient/reports/', views_secure.patient_get_reports, name='patient_reports'),
    path('api/patient/report/<int:report_id>/', views_secure.patient_view_report, name='patient_view_report'),
    path('api/patient/access-logs/', views_secure.patient_access_logs, name='patient_access_logs'),

    # Admin APIs
    path('api/admin/pending-staff/', views_secure.admin_pending_staff, name='admin_pending_staff'),
    path('api/admin/all-staff/', views_secure.admin_all_staff, name='admin_all_staff'),
    path('api/admin/verify-staff/<int:staff_id>/', views_secure.admin_verify_staff, name='admin_verify_staff'),
    path('api/admin/reject-staff/<int:staff_id>/', views_secure.admin_reject_staff, name='admin_reject_staff'),
    path('api/admin/diagnostic/reports/', views_secure.admin_diagnostic_reports, name='admin_diagnostic_reports'),
    
    # Legacy/Existing APIs
    path('api/check-eligibility/', views.check_scheme_eligibility, name='api_check_eligibility'),
    path('api/upload-report/', views.upload_medical_report, name='api_upload_report'),  # DEPRECATED
    path('api/reports/', views.get_medical_reports, name='api_get_reports'),
    path('api/analyze-report/', views.analyze_medical_report, name='api_analyze_report'),
    path('api/subscription/', views.get_subscription_status, name='api_subscription_status'),
    path('api/upgrade-premium/', views.upgrade_to_premium, name='api_upgrade_premium'),
]

# Swasthya Sakhi — Intelligent Healthcare Assistance for Karnataka Government Hospitals

## 1. Introduction

Healthcare accessibility in India, particularly within public/government hospitals, has significantly improved over the years. However, awareness, navigation and comprehension of available medical benefits remain a challenge for patients — especially those belonging to rural, low-income or non-technical backgrounds.

Swasthya Sakhi is a Smart Healthcare Platform designed to empower patients in Karnataka Government Hospitals by bridging the gap between available medical services and patient understanding. Powered by Gemini AI, it helps users identify government scheme eligibility, digitally store their hospital reports, and understand medical terms in simple Kannada and English.

## 2. Problem Statement

Despite the presence of multiple government healthcare benefit schemes (Ayushman Bharat PMJAY, Vajpayee Arogyashree, Jyothi Sanjeevini etc.), large numbers of eligible patients are unaware of the schemes they qualify for or the documentation required to apply.

Additionally, patients are often forced to physically move across hospital departments to collect and understand diagnostic reports — causing significant delays, confusion, exhaustion and anxiety.

### Identified Problems:

| Problem | Real Impact on Patients |
|---------|-------------------------|
| Lack of awareness of Govt schemes | Patients pay unnecessarily for covered treatments |
| No centralized access to reports | People walk between queues & departments |
| Medical terms difficult to understand | Leads to stress + delayed treatment decisions |
| Rural & non-digital citizens face more issues | Information doesn't reach beneficiaries properly |

## 3. Proposed Solution — Swasthya Sakhi

Swasthya Sakhi is a One-Click Healthcare Intelligence Platform that solves these problems using:

🔹 AI-driven Scheme Eligibility Predictor
🔹 Digital Medical Report Locker
🔹 Gemini-powered Report Interpretation in Simple Kannada/English

This system helps any patient in Karnataka Government Hospitals understand:

✔ Which schemes they are eligible for
✔ What documents are required
✔ How to apply step-by-step
✔ What their medical report actually means
✔ Health severity, recommendations, next actions

## 4. System Architecture Overview

```
             ┌──────────────────┐
              │   User / Patient  │
              └─────────┬────────┘
                        │
                Web UI (Glassmorphism UI)
                        │
        ┌───────────────┴────────────────┐
        │                                │
Django Backend + REST API      PostgreSQL / SQLite
        │                                │
        │                        Report Vault Storage
        │                          • Upload/Store PDF
        │                          • Secure Access / Lifetime
        │                                │
        └───────────────┬────────────────┘
                        │
                Gemini AI Engine
                  • Scheme Prediction
                  • Report Interpretation
```

## 5. Key Features

| Feature | Description |
|---------|-------------|
| Gemini Scheme Predictor | Predicts eligibility for Central + Karnataka Government Schemes using patient profile |
| Digital Health Locker | Stores medical reports permanently in cloud with end-to-end encryption |
| Gemini Medical Interpreter | Converts medical terms into simple Kannada/English with color-coded severity |
| Secure Report Access | OTP-protected access to medical reports with audit trail |
| Hospital Staff Portal | Dedicated upload portal for authorized hospital staff only |
| Super UI/UX | Premium-grade glassmorphism design for smooth navigation |
| Low Network Mode | Rural-friendly optimization |

## 6. Technology Stack

| Component | Technology |
|-----------|------------|
| Backend Framework | Django 5.2.8 + Django REST Framework 3.16.1 |
| AI Engine | Google Generative AI (Gemini) 0.8.5 |
| Frontend UI | HTML + CSS (Glassmorphism) + JavaScript |
| Database | PostgreSQL (Production) / SQLite (Development) |
| PDF Processing | PyMuPDF, PyPDF2, pytesseract |
| Authentication | Django Secure Login with Role-Based Access |
| Language Support | Kannada + English UI |
| Encryption | AES-128 encryption for medical reports |
| Security | OTP verification, session management, audit logs |

## 7. Security & Privacy Features

Swasthya Sakhi implements enterprise-grade security measures:

🔒 **End-to-End Encryption**: All medical reports are encrypted before storage
🔒 **OTP Protection**: Two-factor authentication for accessing sensitive reports
🔒 **Role-Based Access**: Separate portals for patients and hospital staff
🔒 **Audit Trail**: Complete log of all report access attempts
🔒 **Hospital Verification**: Only verified hospital staff can upload reports
🔒 **Data Privacy**: Patient data never shared with third parties

## 8. User Roles

### Patient Users
- Check government scheme eligibility
- Store and access medical reports securely
- Get AI-powered interpretation of medical reports
- View access logs for their reports

### Hospital Staff
- Upload medical reports for patients
- Verify patient identity before upload
- View upload history
- Must be verified by admin before gaining access

## 9. Revenue Model (Developer Earnings)

To ensure sustainability while keeping the solution accessible, only one simple monetization layer is used:

### Premium Subscription — ₹49/month

| Feature | Free Tier | Premium Tier |
|---------|-----------|--------------|
| Reports Upload | 5 reports | Unlimited |
| AI Analysis | 3/month | Unlimited |
| Scheme Checker | ✓ | ✓ (Priority) |
| Storage | Basic | Lifetime Premium |
| Ads | Yes | No |
| Support | Standard | Priority 24/7 |

Even with 2,000 paying users → ₹98,000 per month recurring, directly beneficial to the developer.

## 10. Future Expansion & Scalability

The platform can expand to:

📍 Other Indian States
📍 Multi-language + Pan-India hospital integration
🌍 Global healthcare + insurance mapping
📱 Android/iOS App Deployment
🧬 AI-based health prediction analytics

This makes it not just a project, but a scalable health-tech product.

## 11. Implementation Details

### Scheme Eligibility Checker
- AI analyzes patient profile (age, district, economic status, disease type)
- Returns structured JSON with scheme name, eligibility score, required documents
- Provides step-by-step application guidance

### Medical Report Vault
- Hospital staff upload reports mapped to patient phone numbers
- Reports encrypted before storage using Fernet encryption
- Patients access via OTP verification
- Complete audit trail of all access attempts

### AI Report Interpreter
- Extracts text from PDF using multiple approaches (PyPDF2, PyMuPDF, OCR)
- Sends to Gemini AI for analysis
- Returns structured results with:
  - Patient summary
  - Abnormal findings (color-coded by severity)
  - Lifestyle recommendations
  - Doctor visit suggestions

## 12. Conclusion

Swasthya Sakhi bridges one of the most critical healthcare gaps — information accessibility.

By simplifying scheme eligibility, centralizing medical reports, and using AI to translate medical jargon into human-friendly language, this system improves treatment clarity, reduces physical effort, and empowers millions of government hospital patients.

With a simple ₹49 subscription model, the platform is financially sustainable while remaining affordable and inclusive.

This project holds real-world implementation potential at district, state and national scales.
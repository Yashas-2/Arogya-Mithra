import requests
import json
from django.conf import settings

GEMINI_API_KEY = settings.GEMINI_API_KEY
BASE_URL = 'https://generativelanguage.googleapis.com/v1beta/models'

class GeminiAIService:
    def __init__(self):
        self.model = 'gemini-3.6-flash'  # Updated: only model working with AQ auth keys

    def _generate(self, prompt, max_output_tokens=2048, temperature=0.2, response_mime_type=None):
        url = f'{BASE_URL}/{self.model}:generateContent?key={GEMINI_API_KEY}'
        payload = {
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': {
                'maxOutputTokens': max_output_tokens,
                'temperature': temperature,
            }
        }
        if response_mime_type:
            payload['generationConfig']['responseMimeType'] = response_mime_type

        print(f"[SWASTHYA-GEMINI] POST to model={self.model}")
        resp = requests.post(url, json=payload, timeout=60)
        print(f"[SWASTHYA-GEMINI] Response status: {resp.status_code}")
        if resp.status_code != 200:
            error_body = resp.text[:500]
            print(f"[SWASTHYA-GEMINI] FAILED — {resp.status_code}: {error_body}")
            resp.raise_for_status()
        data = resp.json()

        if 'candidates' not in data or not data['candidates']:
            error_msg = data.get('error', {}).get('message', 'No candidates in response')
            raise Exception(f'Gemini API error: {error_msg}')

        text = data['candidates'][0]['content']['parts'][0]['text']
        return text.strip()

    def _clean_json(self, text):
        if text.startswith('```json'):
            text = text[7:]
        if text.startswith('```'):
            text = text[3:]
        if text.endswith('```'):
            text = text[:-3]
        return text.strip()

    def check_scheme_eligibility(self, patient_data):
        prompt = f"""
You are a Government Healthcare Scheme Eligibility Expert for Karnataka and Central Government schemes.

Patient Details:
- Age: {patient_data.get('age')} years
- District: {patient_data.get('district')}, Karnataka
- Economic Status: {patient_data.get('economic_status')}
- Ration Card: {'Available' if patient_data.get('has_ration_card') else 'Not Available'}
- Aadhaar: {'Available' if patient_data.get('has_aadhaar') else 'Not Available'}
- Disease Type: {patient_data.get('disease_type')}
- Language Preference: {patient_data.get('language', 'English')}

Identify the MOST SUITABLE health scheme. Consider these schemes:
1. Pradhan Mantri Jan Arogya Yojana (PMJAY) - Central, BPL, 5 lakhs/year
2. Vajpayee Arogyashree - Karnataka, BPL, critical illnesses
3. Suvarna Arogya Suraksha - Karnataka, APL families
4. Jyothi Sanjeevini Yojana - Karnataka, women and children
5. Yashasvini Health Scheme - Karnataka, cooperative members
6. Karnataka Arogya Raksha Scheme (KARS) - state employees
7. Ayushman Bharat - Central, cashless for poor families

Return ONLY valid JSON:
{{
  "scheme_name": "Name",
  "scheme_type": "Karnataka or Central",
  "eligibility_score": "XX%",
  "why_eligible": "Explanation",
  "required_documents": ["Doc 1", "Doc 2", "Doc 3"],
  "apply_steps": ["Step 1", "Step 2", "Step 3"],
  "language_output": "{patient_data.get('language', 'English')}"
}}
"""
        try:
            result_text = self._generate(prompt, max_output_tokens=1500, temperature=0.2, response_mime_type='application/json')
            result_text = self._clean_json(result_text)
            result = json.loads(result_text)
            for key in ['scheme_name', 'scheme_type', 'eligibility_score', 'why_eligible', 'required_documents', 'apply_steps']:
                if key not in result:
                    raise ValueError(f'Missing key: {key}')
            return result
        except json.JSONDecodeError:
            raise Exception('AI generated invalid response. Please try again.')
        except Exception as e:
            raise Exception(f'Scheme prediction failed: {str(e)}')

    def analyze_medical_report(self, report_text, language='English'):
        truncated_text = report_text[:4000] + '...' if len(report_text) > 4000 else report_text

        prompt = f"""
You are a qualified medical AI assistant. Analyze this medical report and respond ONLY with valid JSON.

Language: {language}

MEDICAL REPORT:
{truncated_text}

REQUIRED JSON:
{{
  "patient_summary": "Brief summary in {language}",
  "abnormal_findings": [
    {{
      "parameter": "Test name",
      "value": "Recorded value",
      "normal_range": "Normal range",
      "severity": "mild/moderate/severe/critical",
      "simple_explanation": "Simple explanation in {language}"
    }}
  ],
  "risk_level": "Low/Medium/High",
  "lifestyle_recommendations": ["Recommendation in {language}"],
  "doctor_visit_suggestion": "When to see doctor in {language}"
}}

Return ONLY the JSON object.
"""
        try:
            result_text = self._generate(prompt, max_output_tokens=2048, temperature=0.2, response_mime_type='application/json')
            result_text = self._clean_json(result_text)
            result = json.loads(result_text)
            for key in ['patient_summary', 'abnormal_findings', 'risk_level', 'lifestyle_recommendations', 'doctor_visit_suggestion']:
                if key not in result:
                    raise ValueError(f'Missing key: {key}')
            return result
        except json.JSONDecodeError:
            raise Exception('AI generated invalid response format. Please try again.')
        except Exception as e:
            raise Exception(f'Failed to analyze report: {str(e)}')

    def recommend_best_doctor(self, report_analysis, doctors):
        if not doctors:
            return None

        doctor_list = "\n".join([
            f"ID: {d.get('id')} | Name: {d.get('full_name')} | Specialty: {d.get('specialization')} | Exp: {d.get('experience_years')} yrs"
            for d in doctors
        ])

        prompt = f"""
Based on this patient report analysis, recommend the MOST appropriate doctor.

ANALYSIS:
{json.dumps(report_analysis, indent=2)}

DOCTORS:
{doctor_list}

Return ONLY JSON: {{"recommended_doctor_id": 123, "reason": "Why this doctor"}}
"""
        try:
            text = self._generate(prompt, max_output_tokens=100, temperature=0.1)
            text = self._clean_json(text)
            if not text.startswith('{'):
                text = '{"recommended_doctor_id": ' + text
            if '}' not in text:
                text += '}'
            result = json.loads(text)
            return result.get('recommended_doctor_id')
        except Exception:
            return doctors[0].get('id') if doctors else None

    def get_chat_response(self, user_message, chat_history=[], doctor_context=None):
        system_prompt = "You are a helpful medical assistant. Provide accurate, empathetic, and professional health advice."
        if doctor_context:
            system_prompt += f" You represent Dr. {doctor_context.get('full_name')}, a {doctor_context.get('specialization')}."

        history_str = ""
        for msg in chat_history[-6:]:
            role = "Patient" if msg.get('from') == 'patient' else "Assistant"
            history_str += f"{role}: {msg.get('text')}\n"

        prompt = f"""
{system_prompt}

Chat Context:
{history_str}
Patient: {user_message}

Rules:
1. Be concise and helpful.
2. Redirect non-medical questions politely.
3. Always include a disclaimer to consult a real doctor.
4. Plain text response.
"""
        try:
            return self._generate(prompt, max_output_tokens=500, temperature=0.7)
        except Exception as e:
            return "I apologize, but I'm having trouble connecting. Please try again in a moment."


gemini_service = GeminiAIService()

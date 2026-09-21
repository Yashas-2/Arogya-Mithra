from google import genai
from google.genai import types
from django.conf import settings
import json

# Initialize client with new SDK
client = genai.Client(api_key=settings.GEMINI_API_KEY)

class GeminiAIService:
    def __init__(self):
        self.model = 'gemini-2.0-flash'

    def check_scheme_eligibility(self, patient_data):
        """
        Check health scheme eligibility using Gemini AI
        Returns structured JSON response
        """
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

Based on this information, identify the MOST SUITABLE health scheme from Karnataka or Central Government.

Consider these major schemes:
1. Pradhan Mantri Jan Arogya Yojana (PMJAY) - Central, for BPL families, covers 5 lakhs/year
2. Vajpayee Arogyashree - Karnataka, for BPL families, covers critical illnesses
3. Suvarna Arogya Suraksha - Karnataka, for APL families
4. Jyothi Sanjeevini Yojana - Karnataka, for women and children
5. Yashasvini Health Scheme - Karnataka, for cooperative members
6. Karnataka Arogya Raksha Scheme (KARS) - Karnataka state employees
7. Ayushman Bharat - Central, cashless treatment for poor families

YOU MUST RETURN VALID JSON in this EXACT structure:
{{
  "scheme_name": "Name of the most suitable scheme",
  "scheme_type": "Karnataka or Central",
  "eligibility_score": "XX% (your confidence in eligibility)",
  "why_eligible": "Clear explanation why patient qualifies",
  "required_documents": ["Document 1", "Document 2", "Document 3"],
  "apply_steps": [
    "Step 1: Detailed instruction",
    "Step 2: Detailed instruction",
    "Step 3: Detailed instruction",
    "Step 4: Final verification"
  ],
  "language_output": "{patient_data.get('language', 'English')}"
}}

CRITICAL: Return ONLY the JSON object, no extra text before or after.
"""

        try:
            response = client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=1500,
                    temperature=0.2,
                    top_p=0.8,
                    top_k=40,
                    response_mime_type="application/json"
                )
            )
            result_text = response.text.strip() if response.text else ""

            # Clean response
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.startswith('```'):
                result_text = result_text[3:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]
            result_text = result_text.strip()
            print(f"DEBUG - Full AI Response: {result_text}")

            if not result_text:
                raise Exception("Empty response from AI")

            result = json.loads(result_text)

            required_keys = ['scheme_name', 'scheme_type', 'eligibility_score', 'why_eligible', 'required_documents', 'apply_steps']
            for key in required_keys:
                if key not in result:
                    raise ValueError(f"Missing required key from AI response: {key}")

            return result

        except json.JSONDecodeError:
            print(f"Failed to parse Gemini JSON output for scheme prediction: {result_text}")
            raise Exception("AI generated an invalid response. Please try again.")
        except Exception as e:
            print(f"Gemini API Error for scheme prediction: {str(e)}")
            raise Exception(f"Scheme prediction failed using Gemini API: {str(e)}")

    def analyze_medical_report(self, report_text, language='English'):
        """
        Analyze medical report using Gemini AI
        Returns structured JSON with findings
        """
        truncated_text = report_text[:4000] + "..." if len(report_text) > 4000 else report_text

        prompt = f"""
You are a highly qualified medical AI assistant. Analyze the following medical report and respond ONLY with a valid JSON object. Do not include any markdown formatting, conversational text, or explanations outside the JSON structure.

Language for analysis output: {language}

MEDICAL REPORT CONTENT:
{truncated_text}

REQUIRED JSON STRUCTURE:
{{
  "patient_summary": "A brief, easy-to-understand summary of the patient's overall health based on the report (in {language}).",
  "abnormal_findings": [
    {{
      "parameter": "Name of the test/parameter that is abnormal",
      "value": "The recorded value",
      "normal_range": "The expected normal range",
      "severity": "mild, moderate, severe, or critical",
      "simple_explanation": "A simple explanation of what this abnormality means (in {language})"
    }}
  ],
  "risk_level": "Low, Medium, or High",
  "lifestyle_recommendations": [
    "Specific lifestyle or dietary recommendation (in {language})"
  ],
  "doctor_visit_suggestion": "Recommendation on when/if to see a doctor based on these results (in {language})"
}}

CRITICAL INSTRUCTION: Return ONLY the raw JSON object. Do not use ```json blocks.
"""

        try:
            response = client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=2048,
                    temperature=0.2,
                    top_p=0.8,
                    top_k=40,
                    response_mime_type="application/json"
                )
            )
            result_text = response.text.strip() if response.text else ""

            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.startswith('```'):
                result_text = result_text[3:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]
            result_text = result_text.strip()

            if not result_text:
                raise Exception("Empty response from AI")

            result = json.loads(result_text)

            required_keys = ['patient_summary', 'abnormal_findings', 'risk_level', 'lifestyle_recommendations', 'doctor_visit_suggestion']
            for key in required_keys:
                if key not in result:
                    raise ValueError(f"Missing required key in Gemini response: {key}")

            return result

        except json.JSONDecodeError as e:
            print(f"Failed to parse Gemini JSON output: {result_text}")
            raise Exception("The AI generated an invalid response format. Please try again.")
        except Exception as e:
            print(f"Gemini API Error: {str(e)}")
            raise Exception(f"Failed to analyze report using Gemini AI: {str(e)}")

    def recommend_best_doctor(self, report_analysis, doctors):
        """
        Analyze report findings and recommend the best doctor from the list.
        """
        if not doctors:
            return None

        doctor_list_str = "\n".join([
            f"ID: {d.get('id')} | Name: {d.get('full_name')} | Specialty: {d.get('specialization')} | Exp: {d.get('experience_years')} yrs"
            for d in doctors
        ])

        prompt = f"""
You are a medical triage expert. Based on the following AI analysis of a patient's medical report, recommend the MOST appropriate doctor from the provided list.

PATIENT REPORT ANALYSIS:
{json.dumps(report_analysis, indent=2)}

AVAILABLE DOCTORS:
{doctor_list_str}

Return ONLY a JSON object with the recommended doctor ID and a brief reason.
Example: {{"recommended_doctor_id": 123, "reason": "Appropriate specialty for findings"}}

{{"recommended_doctor_id":
"""
        try:
            response = client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=100,
                    temperature=0.1
                )
            )
            text = response.text.strip() if response.text else ""
            if not text.startswith('{'):
                text = '{"recommended_doctor_id": ' + text
            if '}' not in text:
                text += '}'

            result = json.loads(text)
            return result.get('recommended_doctor_id')
        except Exception as e:
            print(f"Recommendation Error: {e}")
            return doctors[0].get('id') if doctors else None

    def get_chat_response(self, user_message, chat_history=[], doctor_context=None):
        """
        Generate a medical AI chat response for patients.
        Incorporates doctor specialization context if available.
        """
        system_prompt = "You are a helpful medical assistant. Provide accurate, empathetic, and professional health advice."
        if doctor_context:
            system_prompt += f" You are currently representing Dr. {doctor_context.get('full_name')} who is a {doctor_context.get('specialization')}. Keep your advice within this specialization but remain general if needed."

        history_str = ""
        for msg in chat_history[-6:]:
            role = "Patient" if msg.get('from') == 'patient' else "Assistant"
            history_str += f"{role}: {msg.get('text')}\n"

        prompt = f"""
{system_prompt}

Recent Chat Context:
{history_str}
Patient: {user_message}

Rules:
1. Be concise and helpful.
2. If the user asks for things outside medical advice, politely redirect them.
3. ALWAYS include a disclaimer that this is AI advice and they should consult a real doctor for serious issues.
4. Response should be plain text.
"""
        try:
            response = client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=500,
                    temperature=0.7,
                    top_p=0.9
                )
            )
            if response.text:
                return response.text.strip()
            return "I apologize, but I'm having trouble generating a response. Please try again."
        except Exception as e:
            print(f"DEBUG GEMINI SERVICE ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            return "I apologize, but I'm having trouble connecting to my knowledge base right now. Please try again in a moment."

# Initialize service
gemini_service = GeminiAIService()

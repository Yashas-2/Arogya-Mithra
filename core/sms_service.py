"""
core/sms_service.py
Twilio SMS helper — sends OTP to patients.
Falls back gracefully when Twilio is not installed or credentials are missing.
"""
import logging

logger = logging.getLogger(__name__)


def _normalize_phone(phone: str) -> str:
    """
    Ensure the number is in E.164 format.
    If the number doesn't start with '+', assume India (+91).
    Examples:
        '9876543210'    → '+919876543210'
        '+919876543210' → '+919876543210'
    """
    phone = phone.strip()
    if not phone.startswith('+'):
        phone = '+91' + phone.lstrip('0')
    return phone


def send_otp_sms(phone_number: str, otp: str) -> bool:
    """
    Send an OTP via Twilio SMS.
    Returns True on success, False on failure.
    Falls back gracefully if Twilio is not installed or credentials are missing.
    """
    # Lazy import — avoids ImportError crashing the whole module if Twilio
    # is not installed. Also logs the OTP to console for development use.
    try:
        from twilio.rest import Client
        twilio_available = True
    except ImportError:
        twilio_available = False
        logger.warning(
            "twilio package is not installed. "
            "Run: pip install twilio\n"
            f"[DEV] OTP for {phone_number}: {otp}"
        )

    try:
        from django.conf import settings
    except Exception:
        settings = None

    sid   = getattr(settings, 'TWILIO_ACCOUNT_SID',  '') if settings else ''
    token = getattr(settings, 'TWILIO_AUTH_TOKEN',   '') if settings else ''
    from_ = getattr(settings, 'TWILIO_PHONE_NUMBER', '') if settings else ''

    # Log OTP to console always (helps in development)
    logger.info(f"[OTP] {_normalize_phone(phone_number)} → {otp}")

    if not twilio_available:
        # Return False so the view returns 500, but at least doesn't crash
        return False

    if not all([sid, token, from_]):
        logger.error(
            "Twilio credentials missing. "
            "Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER in .env"
        )
        return False

    to = _normalize_phone(phone_number)

    try:
        client  = Client(sid, token)
        message = client.messages.create(
            body=f"Your Swasthya Sakhi OTP is: {otp}\nValid for 5 minutes. Do not share this code.",
            from_=from_,
            to=to,
        )
        logger.info(f"OTP SMS sent to {to} | SID: {message.sid}")
        return True
    except Exception as exc:
        logger.error(f"Twilio SMS failed for {to}: {exc}")
        print(f"DEBUG: Twilio SMS failed for {to}: {exc}")
        import traceback
        traceback.print_exc()
        return False

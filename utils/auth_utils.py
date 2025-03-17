from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
from config import TICKET_EMAIL_ID, TICKET_EMAIL_PASSWORD

def hash_password(password):
    """Hashes a password using bcrypt."""
    return generate_password_hash(password)

def verify_password(stored_password, provided_password):
    """Verifies a password against a stored hash."""
    return check_password_hash(stored_password, provided_password)

def send_otp_via_email(email, otp):
    """Sends OTP to emailID."""
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    s.login(TICKET_EMAIL_ID, TICKET_EMAIL_PASSWORD)

    message = f'''\nOTP: {otp}'''
    print(message)
    
    s.sendmail(TICKET_EMAIL_ID, email, message)
    s.quit()
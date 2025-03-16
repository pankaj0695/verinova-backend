from flask import Blueprint, request, jsonify
from models.user_model import find_user_by_mobile, find_user_by_email_id, create_user, update_otp
from utils.auth_utils import hash_password, verify_password, send_otp_via_email
import string, random

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/signup", methods=["POST"])
def signup():
    """Registers a new user."""
    data = request.get_json()

    # Required fields
    required_fields = ["mobile","name", "address", "dob", "aadharUrl", "panUrl", "selfieUrl", "mpin", "fingerprint"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    # Check if user exists
    if find_user_by_mobile(data["mobile"]):
        return jsonify({"error": "User already exists"}), 400

    # Hash mpin before storing
    data["mpin"] = hash_password(data["mpin"])

    # Store user data
    create_user(data)
    return jsonify({"message": "User registered successfully"}), 200

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticates a user."""
    data = request.get_json()
    mobile_no = data.get("mobile")
    mpin = data.get("mpin")

    if not mobile_no or not mpin:
        return jsonify({"error": "Mobile number and mpin are required"}), 400

    user = find_user_by_mobile(mobile_no)
    if not user or not verify_password(user["mpin"], mpin):
        return jsonify({"error": "Invalid credentials"}), 401

    return jsonify({"message": "Login successful", "user": user}), 200

@auth_bp.route('/generate-otp', methods=['POST'])
def generate_otp():
    """Generates new OTP and sends its to the user's emailID."""
    data = request.json
    if not ('email' in data):
        return jsonify({"error": "Missing required fields"}), 400
    
    email = data['email']

    user = find_user_by_email_id(email)
    if not user:
        return jsonify({"error": "Email doesn't exist"}), 401
    
    otp = int(''.join([random.choice(string.digits) for _ in range(6)]))
    
    update_otp(user, otp)
    send_otp_via_email(email, otp)

    return jsonify({"message": "OTP sent successfully"})

@auth_bp.route('/generate-otp', methods=['POST'])
def verify_otp():
    """Verifies OTP."""
    data = request.json
    if not all(field in data for field in ['email', 'otp']):
        return jsonify({"error": "Missing required fields"}), 400
    
    email = data['email']
    otp = data['otp']

    user = find_user_by_email_id(email)
    if not user:
        return jsonify({"error": "Email doesn't exist"}), 401
    
    if 'otp' in user and otp == user['otp']:
        return jsonify({"verified": True}), 200

    return jsonify({"verified": False, "message": "OTP does not match"}), 400


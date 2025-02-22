from flask import Blueprint, request, jsonify
from models.user_model import find_user_by_mobile, create_user
from utils.auth_utils import hash_password, verify_password

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

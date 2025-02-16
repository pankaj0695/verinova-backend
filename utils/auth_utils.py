from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password):
    """Hashes a password using bcrypt."""
    return generate_password_hash(password)

def verify_password(stored_password, provided_password):
    """Verifies a password against a stored hash."""
    return check_password_hash(stored_password, provided_password)

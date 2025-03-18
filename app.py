# from flask import Flask
# from routes.auth import auth_bp
# from routes.verification import verification_bp
# from routes.s3_upload import s3_upload_bp  # Import S3 Upload Route
# from routes.ticketing import ticketing

# app = Flask(__name__)
# app.register_blueprint(auth_bp)
# app.register_blueprint(verification_bp)
# app.register_blueprint(s3_upload_bp)  # Register S3 Upload Blueprint
# app.register_blueprint(ticketing, url_prefix="/support")

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=4000, debug=True)


from flask import Flask
from flask_cors import CORS
from routes.auth import auth_bp
from routes.verification import verification_bp
from routes.s3_upload import s3_upload_bp  # Import S3 Upload Route
from routes.ticketing import ticketing

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for all origins
CORS(app, resources={r"/*": {
    "origins": ["http://localhost:5173", "http://192.168.137.1:5173"],  # Replace with your frontend IP
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"],
    "supports_credentials": True
}})

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(verification_bp)
app.register_blueprint(s3_upload_bp)  # Register S3 Upload Blueprint
app.register_blueprint(ticketing, url_prefix="/support")

# Start Server
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000, debug=True)
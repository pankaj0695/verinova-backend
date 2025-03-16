from flask import Flask
from routes.auth import auth_bp
from routes.verification import verification_bp
from routes.s3_upload import s3_upload_bp  # Import S3 Upload Route
from routes.ticketing import ticketing

app = Flask(__name__)
app.register_blueprint(auth_bp)
app.register_blueprint(verification_bp)
app.register_blueprint(s3_upload_bp)  # Register S3 Upload Blueprint
app.register_blueprint(ticketing, url_prefix="/support")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000, debug=True)
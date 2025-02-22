from flask import Flask
from routes.auth import auth_bp
from routes.verification import verification_bp
from routes.s3_upload import s3_upload_bp  # Import S3 Upload Route

app = Flask(__name__)
app.register_blueprint(auth_bp)
app.register_blueprint(verification_bp)
app.register_blueprint(s3_upload_bp)  # Register S3 Upload Blueprint

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000, debug=True)
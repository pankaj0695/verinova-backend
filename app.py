from flask import Flask, request, jsonify
from transformers import pipeline
from deepface import DeepFace
from PIL import Image
import cv2
import os
import requests
from io import BytesIO
import boto3
import json
import random
import string
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Load Deepfake Detection Model
deepfake_detector = pipeline("image-classification", model="prithivMLmods/Deep-Fake-Detector-Model")

# AWS S3 Configuration
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")

# Initialize S3 client
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)

def extract_frames(video_path, frame_interval=10):
    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    extracted_frames = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % frame_interval == 0:
            frame_path = f"frame_{frame_count}.jpg"
            cv2.imwrite(frame_path, frame)
            extracted_frames.append(frame_path)

        frame_count += 1

    cap.release()
    return extracted_frames

def predict_deepfake(image_path):
    image = Image.open(image_path).convert('RGB')
    results = deepfake_detector(image)

    fake_prob = next((r['score'] for r in results if r['label'].lower() == 'fake'), 0)
    return fake_prob

def detect_deepfake_in_video(frame_paths, threshold=0.45):
    fake_frames = 0
    total_frames = len(frame_paths)

    for frame in frame_paths:
        fake_prob = predict_deepfake(frame)
        if fake_prob >= threshold:
            fake_frames += 1

    fake_ratio = fake_frames / total_frames
    return fake_ratio > 0.5

def authenticate_user(uploaded_image_path, existing_user_image_path, threshold=0.75):
    try:
        result = DeepFace.verify(img1_path=uploaded_image_path, img2_path=existing_user_image_path, model_name='Facenet', distance_metric="euclidean_l2")
        distance = result["distance"]
        return distance < threshold
    except Exception as e:
        print(f"Error during authentication: {e}")
        return False

@app.route('/verify', methods=['POST'])
def verify():
    data = request.get_json()
    existing_user_image_url = data.get('existing_user_image')
    user_query_video_url = data.get('user_query_video')

    if not existing_user_image_url or not user_query_video_url:
        return jsonify({'error': 'Both existing_user_image and user_query_video URLs are required.'}), 400

    # Define temporary file paths
    existing_user_image_path = "existing_user_image.jpg"
    user_query_video_path = "user_query_video.mp4"
    extracted_frames = []

    try:
        # Download the existing user image
        existing_user_image_response = requests.get(existing_user_image_url)
        existing_user_image = Image.open(BytesIO(existing_user_image_response.content)).convert('RGB')
        existing_user_image.save(existing_user_image_path)

        # Download the user query video
        user_query_video_response = requests.get(user_query_video_url)
        with open(user_query_video_path, 'wb') as f:
            f.write(user_query_video_response.content)

        # Extract frames from the video
        extracted_frames = extract_frames(user_query_video_path)

        # Check for deepfake
        if detect_deepfake_in_video(extracted_frames):
            return jsonify({'result': 'Fake Video - AI generated'}), 401

        # Authenticate user
        for frame in extracted_frames:
            if authenticate_user(frame, existing_user_image_path):
                return jsonify({'result': 'User Authenticated'})

        return jsonify({'result': 'Authentication failed'}), 401

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        # Cleanup: Delete video, frames, and image after execution
        try:
            if os.path.exists(existing_user_image_path):
                os.remove(existing_user_image_path)
            if os.path.exists(user_query_video_path):
                os.remove(user_query_video_path)
            for frame in extracted_frames:
                if os.path.exists(frame):
                    os.remove(frame)
        except Exception as cleanup_error:
            print(f"Error during cleanup: {cleanup_error}")
  

def generate_file_name(extension):
    """Generates a random filename with a given extension."""
    random_string = "".join(random.choices(string.ascii_letters + string.digits, k=16))
    return f"{random_string}.{extension}"

@app.route('/generate-upload-url', methods=['POST'])
def generate_upload_url():
    """Generates a pre-signed URL for uploading files to AWS S3."""
    try:
        # Parse JSON body
        data = request.get_json()
        img_extension = data.get("imgExtension")
        
        if not img_extension:
            return jsonify({"error": "Image extension is required"}), 400

        # Generate a unique file name
        file_name = generate_file_name(img_extension)

        # Define S3 parameters
        params = {
            "Bucket": AWS_BUCKET_NAME,
            "Key": file_name,
        }

        # Generate pre-signed URL
        upload_url = s3_client.generate_presigned_url(
            ClientMethod="put_object",
            Params=params,
            ExpiresIn=60  # URL expires in 60 seconds
        )

        return jsonify({"url": upload_url}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

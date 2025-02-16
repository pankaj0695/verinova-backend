import cv2
from transformers import pipeline
from deepface import DeepFace
from PIL import Image
import os

# Load Deepfake Detection Model
deepfake_detector = pipeline("image-classification", model="prithivMLmods/Deep-Fake-Detector-Model")

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
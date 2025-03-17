from flask import Blueprint, jsonify
import requests
import subprocess
import torch
import os
import json
import torchvision.transforms as transforms
import cv2
import tempfile
from PIL import Image
import timm
from moviepy import VideoFileClip
import assemblyai as aai
from together import Together

aai.settings.api_key = "555614b07a4042b5bbd3f224ceae0b54"
transcriber = aai.Transcriber()

# Create Flask Blueprint
verification_bp = Blueprint('verification', __name__)

# Load Models
deepfake_model = timm.create_model('xception', pretrained=True, num_classes=2)
deepfake_model.eval()
client = Together(api_key=os.getenv("TOGETHER_API_KEY"))

def download_from_s3(url, file_type="mp4"):
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_type}")
    response = requests.get(url, stream=True)
    
    with open(temp_file.name, 'wb') as f:
        for chunk in response.iter_content(chunk_size=1024):
            f.write(chunk)
    
    return temp_file.name

def detect_deepfake(video_path):
    cap = cv2.VideoCapture(video_path)
    fake_frames = 0
    total_frames = 0
    frame_interval = 10

    transform = transforms.Compose([
        transforms.Resize((299, 299)),
        transforms.ToTensor(),
        transforms.Normalize([0.5], [0.5])
    ])

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if total_frames % frame_interval == 0:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(frame)
            image = transform(image).unsqueeze(0)

            with torch.no_grad():
                output = deepfake_model(image)
                probabilities = torch.nn.functional.softmax(output[0], dim=0)
                fake_prob = probabilities[1].item()

            if fake_prob > 0.6:
                fake_frames += 1

        total_frames += 1

    cap.release()
    return fake_frames / total_frames > 0.5

def extract_audio(video_path, output_audio="output_audio.wav"):
    clip = VideoFileClip(video_path)
    clip.audio.write_audiofile(output_audio, codec='pcm_s16le', fps=16000)
    return output_audio

def convert_mp3_to_wav(mp3_path, wav_path):
    command = f"ffmpeg -i {mp3_path} -ar 16000 -ac 1 {wav_path}"
    subprocess.run(command, shell=True, check=True)

def transcribe_audio(audio_url=None, video_url=None):
    try:
        transcript=None
        if audio_url:
            transcript = transcriber.transcribe(audio_url)
        elif video_url:
            transcript = transcriber.transcribe(video_url)
        else:
            return jsonify({"error": "No valid audio source provided."}), 400

        
        print(f"Transcription Result: {transcript.text}")  # Debugging print

        return transcript.text

    except Exception as e:
        return jsonify({"error": f"Error during transcription: {str(e)}"}), 500

def classify_user_query(query):
    # Define keywords for each category
    loan_keywords = {
        "Home Loan": ["home loan"],
        "Car Loan": ["car loan"],
        "Personal Loan": ["personal loan"],
        "Business Loan": ["business loan"],
        "Educational Loan": ["educational loan", "study loan", "student loan"]
    }

    policy_keywords = {
        "Privacy Policy": ["privacy policy"],
        "Grievance Redressal Policy": ["grievance redressal"],
        "Terms and Conditions for Internet Banking": ["terms and conditions"],
        "Anti-Money Laundering Policy": ["anti-money laundering"],
        "Deposit Policy": ["deposit policy"],
        "Compensation Policy": ["compensation policy"],
        "Customer Rights Policy": ["customer rights policy"]
    }

    query_lower = query.lower()  # Convert query to lowercase for case-insensitive matching

    # Check for loan keywords
    for loan_type, keywords in loan_keywords.items():
        if any(keyword in query_lower for keyword in keywords):
            return {
                "category": "Loan",
                "matched_name": loan_type
            }

    # Check for policy keywords
    for policy_type, keywords in policy_keywords.items():
        if any(keyword in query_lower for keyword in keywords):
            return {
                "category": "Policy",
                "matched_name": policy_type
            }

    # Default to FAQ if no keywords match
    return {
        "category": "FAQ",
        "matched_name": "FAQ"
    }

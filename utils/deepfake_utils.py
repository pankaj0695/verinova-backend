import cv2
from transformers import pipeline
import requests
from deepface import DeepFace
import whisper
from moviepy import VideoFileClip
from PIL import Image
import os
import tempfile
import timm
import ffmpeg
import torch
import torchaudio
import torchvision.transforms as transforms

# Load Deepfake Detection Model
# deepfake_detector = pipeline("image-classification", model="prithivMLmods/Deep-Fake-Detector-Model")
# deepfake_model = timm.create_model("xception", pretrained=True, num_classes=2)
# deepfake_model.eval()
# whisper_model = whisper.load_model("base")

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

def detect_deepfake_in_video(video_url):
    """Detect deepfake in a video by extracting frames and using a classification model."""
    video_path = download_from_s3(video_url, "mp4")
    if not video_path:
        return False  # Fail gracefully if video cannot be downloaded

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

def authenticate_user(uploaded_image_path, existing_user_image_path, threshold=0.75):
    try:
        # Ensure both image files exist
        if not os.path.exists(uploaded_image_path):
            print(f"Error: Uploaded image not found: {uploaded_image_path}")
            return False
        if not os.path.exists(existing_user_image_path):
            print(f"Error: Existing user image not found: {existing_user_image_path}")
            return False

        # Perform face verification
        result = DeepFace.verify(
            img1_path=uploaded_image_path,
            img2_path=existing_user_image_path,
            model_name='Facenet',
            distance_metric="euclidean_l2"
        )

        distance = result.get("distance", 1)  # Default to high distance if result is invalid
        return distance < threshold

    except Exception as e:
        print(f"DeepFace Authentication Error: {e}")
        return False

def download_from_s3(url, file_type="mp4"):
    """Download a file from S3 and return the local file path."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_type}")
    response = requests.get(url, stream=True)

    if response.status_code == 200:
        with open(temp_file.name, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                f.write(chunk)
        return temp_file.name
    else:
        print(f"❌ Failed to download from S3: {url}")
        return None

def extract_audio(video_path, output_audio="output_audio.wav"):
    """Extracts audio from a video file and saves it as a WAV file."""
    try:
        clip = VideoFileClip(video_path)
        clip.audio.write_audiofile(output_audio, codec="pcm_s16le", fps=16000)
        return output_audio
    except Exception as e:
        print(f"🚨 Error extracting audio: {e}")
        return None

# ✅ Convert .m4a to .wav
def convert_m4a_to_wav(m4a_path, wav_path="converted_audio.wav"):
    """Converts an .m4a audio file to .wav using FFmpeg."""
    try:
        print(f"🔄 Converting {m4a_path} to {wav_path} using FFmpeg...")
        (
            ffmpeg
            .input(m4a_path)
            .output(wav_path, format="wav", acodec="pcm_s16le", ar="16000")
            .run(quiet=True, overwrite_output=True)
        )
        print(f"✅ Conversion successful: {wav_path}")
        return wav_path
    except Exception as e:
        print(f"🚨 Error converting .m4a to .wav: {e}")
        return None

# ✅ Transcribe Audio
def transcribe_audio(audio_url=None, video_path=None):
    """Transcribes audio from either a direct audio file (.m4a) or extracted from a video."""
    if audio_url:
        audio_path = download_from_s3(audio_url, "m4a")
        if not audio_path:
            return "Error: Failed to download audio file."
        audio_path = convert_m4a_to_wav(audio_path)  # Convert to WAV
    elif video_path:
        audio_path = extract_audio(video_path)
        if not audio_path:
            return "Error: Audio extraction failed."
    else:
        return "Error: No valid audio source provided."

    try:
        print(f"🔍 Transcribing audio file: {audio_path}")
        result = whisper_model.transcribe(audio_path)
        return result["text"]
    except Exception as e:
        print(f"🚨 Whisper Transcription Error: {e}")
        return "Error: Transcription failed."

def detect_query_type(file_url):
    if file_url.endswith('.mp4'):
        return "video"
    elif file_url.endswith('.m4a'):
        return "audio"
    else:
        return "unknown"

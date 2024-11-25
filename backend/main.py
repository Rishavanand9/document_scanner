from typing import Union, List

from fastapi import FastAPI, UploadFile, HTTPException # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
import cv2 # type: ignore
# import torch # type: ignore
from PIL import Image # type: ignore
import tempfile
import os
# from transformers import BlipProcessor, BlipForConditionalGeneration, TrOCRProcessor, VisionEncoderDecoderModel # type: ignore
import base64
import io
import easyocr # type: ignore
import numpy as np # type: ignore
import ollama # type: ignore
from ocr import perform_ocr # type: ignore
from detect_text import detect_text  # Add this import

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize BLIP model and processor
# processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
# model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

# # Initialize TrOCR model and processor
# ocr_processor = TrOCRProcessor.from_pretrained('microsoft/trocr-base-handwritten')
# ocr_model = VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-base-handwritten')

reader = easyocr.Reader(['en'])  # for English only

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

@app.post("/api/analyze-image")
async def analyze_image(file: UploadFile):
    # Image processing logic here
    pass

@app.post("/api/authenticate-product")
async def authenticate_product(product_data: dict):
    # Authentication logic here
    pass

# Initialize the reader once (supports multiple languages if needed)
reader = easyocr.Reader(['en'])  # for English only

@app.post("/api/authenticate")
async def authenticate_video(file: UploadFile) -> List[dict]:
    video = None
    temp_path = None
    
    try:
        # Validate file extension
        if not file.filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            raise HTTPException(status_code=400, detail="Unsupported video format. Please upload MP4, AVI, MOV, or MKV files.")

        # Save uploaded video to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            content = await file.read()
            if len(content) == 0:
                raise HTTPException(status_code=400, detail="Empty file uploaded")
            temp_file.write(content)
            temp_path = temp_file.name
        
        # Open video after the file is completely written and closed
        video = cv2.VideoCapture(temp_path)
        
        # More thorough video validation
        if not video.isOpened():
            raise HTTPException(status_code=400, detail="Could not open video file")
            
        fps = video.get(cv2.CAP_PROP_FPS)
        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"Debug - Video properties:")
        print(f"Debug - Path: {temp_path}")
        print(f"Debug - Total frames: {total_frames}")
        print(f"Debug - FPS: {fps}")
        print(f"Debug - File size: {os.path.getsize(temp_path)} bytes")
        
        # More comprehensive validation
        if total_frames <= 0 or fps <= 0:
            raise HTTPException(
                status_code=400, 
                detail="Invalid video file. Please ensure the video is properly encoded and not corrupted."
            )
        
        # Process frames
        frames_to_process = [0, max(0, total_frames-1)]
        print(f"Debug - Frames to process: {frames_to_process}")
        
        results = []
        for frame_idx in frames_to_process:
            print(f"Debug - Processing frame {frame_idx}")
            
            # Set video to specific frame
            video.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = video.read()
            
            if not ret:
                print(f"Debug - Failed to read frame {frame_idx}")
                continue
                
            print(f"Debug - Successfully read frame {frame_idx}")
            
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_frame)
            
            temp_frame_path = f"temp_frame_{frame_idx}.jpg"
            pil_image.save(temp_frame_path, quality=65, optimize=True)
            
            try:
                task_prompt = '<OCR>'
                response = detect_text(task_prompt=task_prompt, image=pil_image)
                print(f"Debug - Labels detected for frame {frame_idx}: {response}")
                    
            except Exception as e:
                response = ''
                print(f"Debug - Exception during text detection for frame {frame_idx}: {e}")
            
            # Remove temporary frame file
            if os.path.exists(temp_frame_path):
                os.remove(temp_frame_path)
            
            # Convert frame to base64
            buffered = io.BytesIO()
            pil_image.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            results.append({
                "frame_number": frame_idx,
                "frame_image": img_str,
                "timestamp": frame_idx/fps,
                "message": response  # Changed from caption to labels
            })
        
        print(f"Debug - Total results processed: {len(results)}")
        return results
    
    except Exception as e:
        print(f"Debug - Main function exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up resources
        if video is not None:
            video.release()
        # Wait a brief moment before trying to delete the file
        import time
        time.sleep(0.1)
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except PermissionError:
                print(f"Warning: Could not delete temporary file: {temp_path}")
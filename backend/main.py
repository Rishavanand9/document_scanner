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
    # Save uploaded video to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_path = temp_file.name
    
    try:
        results = []
        video = cv2.VideoCapture(temp_path)
        
        # Check if video opened successfully
        if not video.isOpened():
            raise HTTPException(status_code=400, detail="Could not open video file")
            
        fps = video.get(cv2.CAP_PROP_FPS)
        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"Debug - Total frames: {total_frames}, FPS: {fps}")
        
        # Ensure we have at least 2 frames
        if total_frames < 2:
            raise HTTPException(status_code=400, detail="Video must have at least 4 frames")
        
        # Frames to process: first and last
        frames_to_process = [0,  max(0, total_frames-1)]
        print(f"Debug - Frames to process: {frames_to_process}")
        
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
                caption = perform_ocr(temp_frame_path)
                if not caption:
                    caption = "Error: No valid response from image analysis"
                print(f"Debug - OCR response for frame {frame_idx}: {caption}")
                    
            except Exception as e:
                caption = f"Error analyzing image: {str(e)}"
                print(f"Debug - Exception during OCR processing for frame {frame_idx}: {e}")
            
            # Remove temporary frame file
            if os.path.exists(temp_frame_path):
                os.remove(temp_frame_path)
            
            # Convert frame to base64
            buffered = io.BytesIO()
            pil_image.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            results.append({
                "frame_number": frame_idx,
                "timestamp": frame_idx/fps,
                "caption": caption,
                "frame_image": img_str
            })
        
        video.release()
        
        print(f"Debug - Total results processed: {len(results)}")
        return results
    
    except Exception as e:
        print(f"Debug - Main function exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)
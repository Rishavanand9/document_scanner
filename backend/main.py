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
        fps = video.get(cv2.CAP_PROP_FPS)
        frame_count = 0
        
        while True:
            ret, frame = video.read()
            if not ret:
                break
            
            frame_count += 1
            if frame_count % int(fps * 5) == 0:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(rgb_frame)
                
                temp_frame_path = f"temp_frame_{frame_count}.jpg"
                pil_image.save(temp_frame_path, quality=65, optimize=True)
                
                try:
                    # Use the perform_ocr function
                    caption = perform_ocr(temp_frame_path)
                    
                    # Add response validation
                    if not caption:
                        caption = "Error: No valid response from image analysis"
                        print(f"Debug - OCR response: {caption}")  # Debug print
                        
                except Exception as e:
                    caption = f"Error analyzing image: {str(e)}"
                    print(f"Debug - Exception during OCR processing: {e}")  # Debug print
                
                # Remove temporary frame file
                if os.path.exists(temp_frame_path):
                    os.remove(temp_frame_path)
                
                # Convert frame to base64
                buffered = io.BytesIO()
                pil_image.save(buffered, format="JPEG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
                
                results.append({
                    "frame_number": frame_count,
                    "timestamp": frame_count/fps,
                    "caption": caption,
                    "frame_image": img_str
                })
                
                print(f"Debug - Processed frame {frame_count} with caption: {caption}")  # Debug print
        
        video.release()
        return results
    
    except Exception as e:
        print(f"Debug - Main function exception: {e}")  # Debug print
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)
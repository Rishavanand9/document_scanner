from typing import Union, List

from fastapi import FastAPI, UploadFile # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
import cv2 # type: ignore
import torch # type: ignore
from PIL import Image # type: ignore
import tempfile
import os
from transformers import BlipProcessor, BlipForConditionalGeneration, TrOCRProcessor, VisionEncoderDecoderModel # type: ignore
import base64
import io

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
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

# Initialize TrOCR model and processor
ocr_processor = TrOCRProcessor.from_pretrained('microsoft/trocr-base-handwritten')
ocr_model = VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-base-handwritten')

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

@app.post("/api/authenticate")
async def authenticate_video(file: UploadFile) -> List[dict]:
    # Save uploaded video to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_path = temp_file.name
    
    try:
        # Process video and collect frame data
        results = []
        video = cv2.VideoCapture(temp_path)
        fps = video.get(cv2.CAP_PROP_FPS)
        frame_count = 0
        
        while True:
            ret, frame = video.read()
            if not ret:
                break
            
            frame_count += 1
            # Process every 2 seconds
            if frame_count % int(fps * 2) == 0:
                # Convert BGR to RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # Convert to PIL Image
                pil_image = Image.fromarray(rgb_frame)
                
                # Generate caption using BLIP
                blip_inputs = processor(pil_image, return_tensors="pt")
                out = model.generate(**blip_inputs)
                caption = processor.decode(out[0], skip_special_tokens=True)
                
                # Perform OCR on the image
                ocr_inputs = ocr_processor(images=pil_image, return_tensors="pt")
                ocr_outputs = ocr_model.generate(**ocr_inputs)
                # detected_text = ocr_processor.batch_decode(ocr_outputs, skip_special_tokens=True)[0]
                
                # Convert frame to base64
                buffered = io.BytesIO()
                pil_image.save(buffered, format="JPEG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
                
                results.append({
                    "frame_number": frame_count,
                    "timestamp": frame_count/fps,
                    "caption": caption,
                    # "detected_text": detected_text,
                    "frame_image": img_str
                })
        
        video.release()
        return results
        
    finally:
        # Clean up temporary file
        os.unlink(temp_path)
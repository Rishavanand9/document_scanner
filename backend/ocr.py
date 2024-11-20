import base64
import requests
from PIL import Image
import ollama

SYSTEM_PROMPT = """Act as an OCR assistant. Analyze the provided image and:
1. Recognize all visible text in the image as accurately as possible.
2. Maintain the original structure and formatting of the text.
3. If any words or phrases are unclear, indicate this with [unclear] in your transcription.
Provide only the transcription without any additional comments."""
def encode_image_to_base64(image_path):
    """Convert an image file to a base64 encoded string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')
def perform_ocr(image_path):
    """Perform OCR on the given image using Llama 3.2-Vision."""
    base64_image = encode_image_to_base64(image_path)
    response = ollama.chat(
        model='llama3.2-vision:11b',
            messages=[{
                'role': 'user',
                'content': SYSTEM_PROMPT,
                'images': [base64_image]
            }],
    )
    return response

if __name__ == "__main__":
    image_path = "/home/vipul/projects/document_scanner/backend/temp_frame_120.jpg"  # Replace with your image path
    result = perform_ocr(image_path)
    if result:
        print("OCR Recognition Result:")
        print(result)
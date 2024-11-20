import base64
from PIL import Image # type: ignore
import ollama # type: ignore

SYSTEM_PROMPT = """Act as an OCR assistant specialized in analyzing video images. Your tasks are:
1. Identify and extract the name of any medicine visible in the image.
2. Count and report the number of medicine products present in the image.
3. Maintain the original structure and formatting of any text.
4. If any words, phrases, or product counts are unclear, indicate this with [unclear] in your transcription.
5. Consider various packaging types, angles, and lighting conditions to ensure accuracy.
6. Count the number of medicine strips/Bottles/Capsules/Containers present in the image.
7. Get the Color of the Medicine Package and the Shape of the Medicine Package.
8. If there are no medicines visible, say "No medicines visible".
Provide only the transcription and count without any additional comments."""

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

# if __name__ == "__main__":
#     image_path = "/home/vipul/projects/document_scanner/backend/temp_frame_120.jpg"  # Replace with your image path
#     result = perform_ocr(image_path)
#     if result:
#         print("OCR Recognition Result:")
#         print(result)
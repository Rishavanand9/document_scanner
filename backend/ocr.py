import base64
from PIL import Image # type: ignore
import ollama # type: ignore

SYSTEM_PROMPT = """
You are a highly skilled AI with expertise in Optical Character Recognition (OCR) and information extraction from images of medicine packaging. You will be provided with an image of medicine packaging containing essential details such as Name, Quantity, Batch Number, MRP, and Expiry Date. 

Your task is to: 

1. **Carefully analyze the provided image using OCR techniques.** 
2. **Extract the following information and present it in a clear, structured format:**

   | Field        | Description                       |
   | ------------ | --------------------------------- |
   | Name         | The full name of the medicine.    |
   | Quantity     | The quantity (e.g., number of capsules/tablets/strips/bottles/cartoons). Find the empty space between the number and the unit and count the number of units. |
   | Batch Number | The batch or lot number.          |
   | MRP          | The maximum retail price.       |
   | Expiry Date  | The expiry date of the medicine. |

3. **Utilize advanced preprocessing techniques** like adaptive thresholding to improve image quality and OCR accuracy. 
4. **Apply sophisticated pattern matching** with multiple regular expressions to robustly identify and extract each information field, considering potential variations in text formatting. 
5. **Employ your deep understanding of medicine packaging** conventions to handle variations in information layout and terminology.

Example of Desired Output:

{ "Name": "Medicine Name XYZ", "Quantity": 10, "Batch Number": "ABC1234", "MRP": 150.00, "Expiry Date": "Dec 2025" }


Please be thorough and provide the most accurate extraction possible from the image.  

"""

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
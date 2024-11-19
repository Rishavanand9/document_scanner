import ollama # type: ignore

def test_read_image(image_path: str = "@temp_frame_120.jpg") -> dict:
    try:
        response = ollama.chat(
            model='llava',
            messages=[{
                'role': 'user',
                'content': 'Extract and describe the text content from this image.',
                'images': [image_path]
            }],
            timeout=30
        )
        
        return response
        
    except Exception as e:
        return {"error": str(e)}

# You can test it like this:
result = test_read_image("path/to/your/image.jpg")
print(result)


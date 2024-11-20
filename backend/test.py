import ollama # type: ignore

def test_read_image() -> dict:
    try:
        response = ollama.chat(
            model='llama3.2-vision:90b',
            messages=[{
                'role': 'user',
                'content': 'Extract and describe the text content from this image.',
                'images': ["/home/vipul/projects/document_scanner/backend/temp_frame_120.jpg"]
            }],
        )
        
        return response
        
    except Exception as e:
        return {"error": str(e)}

# You can test it like this:
result = test_read_image()
print(result)


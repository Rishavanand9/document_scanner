from transformers import AutoProcessor, AutoModelForCausalLM   # type: ignore
from PIL import Image # type: ignore
import requests # type: ignore
import copy
import supervision as sv # type: ignore
from typing import Dict

model_id = 'microsoft/Florence-2-large'
model = AutoModelForCausalLM.from_pretrained(model_id, trust_remote_code=True).eval()
processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)

def detect_text(task_prompt: str, text_input: str = "", image=None) -> Dict:
	prompt = task_prompt + text_input
	inputs = processor(text=prompt, images=image, return_tensors="pt")
	generated_ids = model.generate(
  	input_ids=inputs["input_ids"],
  	pixel_values=inputs["pixel_values"],
  	max_new_tokens=1024,
  	early_stopping=False,
  	do_sample=False,
  	num_beams=3,
	)
	generated_text = processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
	parsed_answer = processor.post_process_generation(
    	generated_text,
    	task=task_prompt,
    	image_size=(image.width, image.height)
	)

	return parsed_answer

# Example usage for basic OCR
"""
image = Image.open("tire.jpg")
task_prompt = '<OCR>'
result = detect_text(task_prompt, image=image)
print(result["text"].strip())
"""

# Example usage for OCR with regions
"""
image = Image.open("image.jpeg").convert("RGB")
task_prompt = "<OCR_WITH_REGION>"
answer = detect_text(task_prompt=task_prompt, image=image)

# Visualize results
bounding_box_annotator = sv.BoundingBoxAnnotator(color_lookup=sv.ColorLookup.INDEX)
label_annotator = sv.LabelAnnotator(color_lookup=sv.ColorLookup.INDEX)

detections = sv.Detections.from_lmm(sv.LMM.FLORENCE_2, answer, resolution_wh=image.size)
annotated = bounding_box_annotator.annotate(image, detections=detections)
annotated = label_annotator.annotate(annotated, detections=detections)
sv.plot_image(annotated)
"""


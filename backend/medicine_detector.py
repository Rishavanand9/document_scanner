import cv2  # type: ignore
from PIL import Image  # type: ignore
import json
from typing import Dict, List
from detect_text import detect_text

class MedicineDetector:
    """
    A class for detecting and extracting text information from medicine packaging
    using Florence-2 model.
    """
    def process_video(self, video_path: str) -> List[Dict]:
        """
        Process only first and last frames of a video and extract medicine information
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Error opening video file: {video_path}")

        results = []
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Process first and last frames
        frames_to_process = [0, total_frames - 1]
        
        for frame_num in frames_to_process:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = cap.read()
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(frame_rgb)
                try:
                    medicine_info = self._analyze_frame(pil_image)
                    medicine_info['frame_number'] = frame_num
                    results.append(medicine_info)
                except Exception as e:
                    print(f"Error processing frame {frame_num}: {str(e)}")

        cap.release()
        return results

    def _analyze_frame(self, image) -> Dict:
        """
        Analyzes a single frame to get all visible text and a summary
        """
        result = {
            "full_text": "",
            "summary": "",
            "frame_number": 0
        }

        # Get all text using OCR - simplified prompt
        full_text_prompt = "<OCR>"
        ocr_result = detect_text(full_text_prompt, image=image)
        result["full_text"] = ocr_result.get("<OCR>", "")

        # Get a structured summary - simplified prompt
        summary_prompt = "<OCR_WITH_REGION>"
        summary_result = detect_text(summary_prompt, image=image)
        result["summary"] = summary_result.get("<OCR_WITH_REGION>", "")

        return result

def main():
    """Example usage"""
    detector = MedicineDetector()
    video_path = "medicine_video.mp4"
    results = detector.process_video(video_path)
    
    with open("medicine_detection_results.json", 'w') as f:
        json.dump(results, f, indent=4)

if __name__ == "__main__":
    main()
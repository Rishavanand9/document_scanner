# Import necessary libraries for image processing, ML models, and visualization
import matplotlib.pyplot as plt # type: ignore
import matplotlib.patches as patches # type: ignore
from pathlib import Path
from PIL import Image # type: ignore
import cv2 # type: ignore
import torch # type: ignore
import base64
import numpy as np # type: ignore
import supervision as sv # type: ignore
# Import ML model components
from transformers import AutoModelForCausalLM, AutoProcessor # type: ignore
from sam2.build_sam import build_sam2 # type: ignore
from sam2.sam2_image_predictor import SAM2ImagePredictor # type: ignore
from sam2.automatic_mask_generator import SAM2AutomaticMaskGenerator # type: ignore

class FacePixelator:
    """
    A class for detecting and pixelating faces in images and videos using Florence-2 and SAM2 models.
    """
    def __init__(self, florence_cache_dir="./models/Florence_2",
                 sam_checkpoint="./models/sam2/sam2_hiera_large.pt",
                 sam_config="./models/sam2/sam2_hiera_l.yaml"):
        # Initialize Florence model for face detection
        self.model = AutoModelForCausalLM.from_pretrained(
            "microsoft/Florence-2-large-ft",
            cache_dir=florence_cache_dir,
            device_map="cuda",
            trust_remote_code=True
        )
        
        self.processor = AutoProcessor.from_pretrained(
            "microsoft/Florence-2-large-ft",
            cache_dir=florence_cache_dir,
            trust_remote_code=True
        )
        
        # Initialize SAM2 model
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.sam_checkpoint = sam_checkpoint
        self.sam_config = sam_config

    def find_all_faces(self, image):
        """
        Detects all faces in an image using Florence model.
        Returns: List of bounding boxes for all detected faces
        """
        PROMPT = "<OD>"
        task_type = "<OD>"
        
        inputs = self.processor(text=PROMPT, images=image, return_tensors="pt").to("cuda")
        generated_ids = self.model.generate(
            input_ids=inputs["input_ids"],
            pixel_values=inputs["pixel_values"],
            max_new_tokens=2048,
            do_sample=False,
        )
        text_generations = self.processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
        results = self.processor.post_process_generation(text_generations, task=task_type, 
                                                       image_size=(image.width, image.height))
        
        raw_lists = []
        for bbox, label in zip(results[task_type]['bboxes'], results[task_type]['labels']):
            if label == "human face":
                raw_lists.append(bbox)
        
        self._display_boxes(image, results[task_type]['bboxes'], results[task_type]['labels'])
        return raw_lists

    def find_main_speakers(self, image):
        """
        Detects main speaking faces in an image.
        Returns: List of bounding boxes for detected main speakers
        """
        PROMPT = "<CAPTION_TO_PHRASE_GROUNDING> human face (main speaker)"
        task_type = "<CAPTION_TO_PHRASE_GROUNDING>"
        
        inputs = self.processor(text=PROMPT, images=image, return_tensors="pt").to("cuda")
        generated_ids = self.model.generate(
            input_ids=inputs["input_ids"],
            pixel_values=inputs["pixel_values"],
            max_new_tokens=2048,
            do_sample=False,
        )
        text_generations = self.processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
        results = self.processor.post_process_generation(text_generations, task=task_type, 
                                                       image_size=(image.width, image.height))
        
        speaker_face_list = []
        for bbox, label in zip(results[task_type]['bboxes'], results[task_type]['labels']):
            if label == "human face":
                speaker_face_list.append(bbox)
        
        self._display_boxes(image, results[task_type]['bboxes'], results[task_type]['labels'])
        return speaker_face_list

    def _display_boxes(self, image, bboxes, labels):
        """
        Helper method to visualize detected faces with bounding boxes
        Args:
            image: Input image
            bboxes: List of bounding boxes
            labels: List of corresponding labels
        """
        fig, ax = plt.subplots()
        ax.imshow(image)
        for bbox, label in zip(bboxes, labels):
            if label == "human face":
                x1, y1, x2, y2 = bbox
                rect_box = patches.Rectangle((x1, y1), x2-x1, y2-y1, linewidth=1,
                                          edgecolor='r', facecolor='none')
                ax.add_patch(rect_box)
                plt.text(x1, y1, label, color='white', fontsize=8,
                        bbox=dict(facecolor='red', alpha=0.5))
        ax.axis('off')
        plt.show()

    def _is_overlapping(self, box1, box2, threshold=0.7):
        """
        Checks if two bounding boxes overlap beyond a certain threshold
        Returns: Boolean indicating if boxes overlap significantly
        """
        x1_min, y1_min, x1_max, y1_max = box1
        x2_min, y2_min, x2_max, y2_max = box2
        
        x_overlap = max(0, min(x1_max, x2_max) - max(x1_min, x2_min))
        y_overlap = max(0, min(y1_max, y2_max) - max(y1_min, y2_min))
        overlap_area = x_overlap * y_overlap
        
        area1 = (x1_max - x1_min) * (y1_max - y1_min)
        area2 = (x2_max - x2_min) * (y2_max - y2_min)
        min_area = min(area1, area2)
        
        return overlap_area >= threshold * min_area

    def _filter_boxes(self, initial_boxes, new_boxes):
        filtered_boxes = []
        for box in initial_boxes:
            if not any(self._is_overlapping(box, new_box) for new_box in new_boxes):
                filtered_boxes.append(box)
        return filtered_boxes

    def find_all_passerbys(self, image):
        raw_lists = self.find_all_faces(image)
        speaker_face_list = self.find_main_speakers(image)
        filtered_faces = self._filter_boxes(raw_lists, speaker_face_list)
        return filtered_faces

    def pixelate_region(self, image, masks, pixelation_size=10):
        """
        Applies pixelation effect to specified regions in the image
        Args:
            image: Input image
            masks: Binary masks indicating regions to pixelate
            pixelation_size: Size of pixelation blocks
        Returns: Image with pixelated regions
        """
        masks = masks.astype(bool)
        height, width = image.shape[:2]
        pixelated_image = image.copy()
        
        for y in range(0, height, pixelation_size):
            for x in range(0, width, pixelation_size):
                block_y_end = min(y + pixelation_size, height)
                block_x_end = min(x + pixelation_size, width)
                block = image[y:block_y_end, x:block_x_end]
                
                combined_block_mask = np.zeros(block.shape[:2], dtype=bool)
                for mask in masks:
                    block_mask = mask[y:block_y_end, x:block_x_end]
                    combined_block_mask = np.logical_or(combined_block_mask, block_mask)
                
                if combined_block_mask.any():
                    average_color = [int(np.mean(channel[combined_block_mask])) 
                                   for channel in cv2.split(block)]
                    for c in range(3):
                        block[:, :, c][combined_block_mask] = average_color[c]
                    pixelated_image[y:block_y_end, x:block_x_end] = block
        
        return pixelated_image

    def process_video(self, input_video, output_video, scale_factor=1, frame_rate=30):
        """
        Processes a video file by pixelating faces in each frame
        Args:
            input_video: Path to input video
            output_video: Path for processed video
            scale_factor: Factor to resize frames
            frame_rate: Output video frame rate
        """
        # Create output directory
        source_frames = Path(Path(input_video).stem)
        source_frames.mkdir(parents=True, exist_ok=True)
        
        # Extract frames
        cap = cv2.VideoCapture(input_video)
        if not cap.isOpened():
            raise ValueError(f"Error: Could not open video {input_video}")
        
        frame_count = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            frame = cv2.resize(frame, (0, 0), fx=scale_factor, fy=scale_factor)
            frame_path = source_frames / f"{frame_count:05d}.jpeg"
            cv2.imwrite(frame_path.as_posix(), frame)
            print(f"Saved frame {frame_count} to {frame_path}")
            frame_count += 1
        
        cap.release()
        
        # Process frames
        self.process_images_in_folder(source_frames)
        
        # Combine frames
        self.combine_frames_to_video(f"{source_frames}/pixelated", output_video, frame_rate)

    def process_images_in_folder(self, folder_path):
        """
        Batch processes all images in a folder, applying face pixelation
        Args:
            folder_path: Directory containing input images
        """
        folder_path = Path(folder_path)
        output_folder = folder_path / "pixelated"
        output_folder.mkdir(parents=True, exist_ok=True)
        
        image_paths = sorted(folder_path.glob("*.jpeg"))
        for image_path in image_paths:
            print(f"Processing {image_path}")
            pixelated_image = self.pixelate_all_faces(image_path)
            
            pil_image = Image.fromarray(pixelated_image)
            output_path = output_folder / image_path.name
            pil_image.save(output_path.as_posix())
            print(f"Saved pixelated image to {output_path}")

    def combine_frames_to_video(self, source_frames_dir, target_video, frame_rate=30):
        """
        Combines processed frames back into a video
        Args:
            source_frames_dir: Directory containing processed frames
            target_video: Output video path
            frame_rate: Frame rate for output video
        """
        source_frames_dir = Path(source_frames_dir)
        frame_files = sorted(source_frames_dir.glob("*.jpeg"))
        
        first_frame = cv2.imread(str(frame_files[0]))
        height, width, layers = first_frame.shape
        frame_size = (width, height)
        
        out = cv2.VideoWriter(str(target_video), cv2.VideoWriter_fourcc(*'mp4v'), 
                             frame_rate, frame_size)
        
        for frame_file in frame_files:
            frame = cv2.imread(str(frame_file))
            out.write(frame)
            print(f"Added frame {frame_file.name} to video.")
        
        out.release()
        print(f"Video saved as {target_video}")

def main():
    """
    Example usage of the FacePixelator class
    """
    # Initialize the FacePixelator
    pixelator = FacePixelator(
        florence_cache_dir="./models/Florence_2",
        sam_checkpoint="./models/sam2/sam2_hiera_large.pt",
        sam_config="./models/sam2/sam2_hiera_l.yaml"
    )
    
    # Process video
    pixelator.process_video(
        input_video="test2.mp4",
        output_video="blur_video.mp4",
        scale_factor=1,
        frame_rate=30
    )

if __name__ == "__main__":
    main()
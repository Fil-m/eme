import os
import uuid
from PIL import Image
from django.conf import settings

def generate_preview(media_file):
    """
    Generates a preview for an image or video file.
    Saves the preview to MEDIA_ROOT/temp/.
    """
    temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
    os.makedirs(temp_dir, exist_ok=True)

    preview_filename = f"prev_{uuid.uuid4().hex}.jpg"
    preview_path = os.path.join(temp_dir, preview_filename)

    # Determine source path
    source_path = None
    if media_file.file:
        source_path = media_file.file.path
    elif media_file.file_path and os.path.exists(media_file.file_path):
        source_path = media_file.file_path

    if not source_path or not os.path.exists(source_path):
        print(f"Source file not found for preview: {source_path}")
        return False

    try:
        if media_file.is_image:
            with Image.open(source_path) as img:
                img.thumbnail((300, 300))
                img.save(preview_path, "JPEG", quality=85)
            
            media_file.preview_path = os.path.join('temp', preview_filename)
            media_file.save()
            return True

        elif media_file.is_video:
            try:
                from moviepy.editor import VideoFileClip
                clip = VideoFileClip(source_path)
                # Save first frame at 1 second mark (or 0 if short)
                duration = clip.duration
                t = 1.0 if duration > 1.0 else 0.0
                clip.save_frame(preview_path, t=t) 
                clip.close()
                media_file.preview_path = os.path.join('temp', preview_filename)
                media_file.save()
                return True
            except (ImportError, Exception) as e:
                print(f"Video preview failed: {e}")
                return False

    except Exception as e:
        print(f"Error generating preview: {e}")
        return False

    return False

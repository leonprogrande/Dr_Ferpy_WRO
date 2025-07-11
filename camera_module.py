import cv2
from picamera2 import Picamera2
import time
from contextlib import contextmanager

@contextmanager
def camera_session():
    """
    Context manager to handle camera initialization and cleanup.
    """
    picam2 = Picamera2()
    try:
        camera_config = picam2.create_still_configuration(
            main={"format": 'RGB888', "size": (640, 360)}
        )
        picam2.configure(camera_config)
        picam2.start()
        time.sleep(1)  # Allow the camera to warm up
        yield picam2
    finally:
        picam2.stop()
        picam2.close()

def capture_image():
    """
    Captures an image using the camera and returns the image array.
    """
    with camera_session() as picam2:
        # Since we configured RGB888, the captured array is already in RGB.
        image_rgb = picam2.capture_array("main")
    return image_rgb

def capture_and_save_image(filename="captured_image.jpg"):
    """
    Captures an image and saves it as a JPEG file.
    """
    image = capture_image()
    # Convert RGB image to BGR for cv2.imwrite.
    image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    cv2.imwrite(filename, image_bgr)
    return filename
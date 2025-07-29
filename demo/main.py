#!.venv/bin/python
from pycam_module import *
import time

def main():
    # Creates new camera with resolution 640x480px,framerate 30 fps and enables mirroring [for selfie webcam]
    # Index: 0 - usually system's default camera
    camera = cam_stream(0,(640,480),30,True)

    camera.start_stream() # Opens device now camera.frame will be updated with new images
    time.sleep(3) # Waits 3s
    camera.take_image("camera_shot.png") # Saves image
    
    # Don't forget to close the camera otherwise errors will be raised and on unix default cam index may shift eg. 0 --> 1 ...
    camera.stop_stream()


if __name__ == "__main__":
    main()

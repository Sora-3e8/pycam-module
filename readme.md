# pycam-module

- Simple python module for camera access.
- Simplicity is the primary target here.
- Module is to be used as simple way to access camera for more complex projects.

## Features:
 - Outputs image in form of np.ndrarray
 - Live feed [No gui method provided by this module]
 - Image mirroring
 - HSV adjustment
 - Gamma adjustment
 - Image saving

## cam_stream methods:
 - Constructor: cam_stream()
 - start_stream(device_index<Int>,resolution<tuple(width,height)>,framerate<Int>,mirror<bool>) - Opens device and starts loop updating the image output frequency dependent<br>
 frequency dependent on framerate
 - stop_stream() - Stops the updating loop and closes the camera device
 - set_mirror(mirror<bool>) - Enables/disables cam mirroring [Live adjustment]
 - take_image(path<string>) - Saves image into path # PNG only
 - set_framerate(framerate<int>) - Changes framerate of the capture and restarts the stream
 - set_resolution(resolution<tuple(width,height)>) - Changes resolution and restarts the stream
 - adjust_gamma(hsv<tuple(hue,saturation,value)>) - Sets HSV adjustment [Live adjustment]
 - adjust_hsv(hsv<tuple(hue,saturation,value)>) - Sets HSV adjustment [Live adjustment]

## Dependencies:
 - Numpy
 - opencv-python

# Supported platforms:
 - Unix
 - Linux
 - Windows [Will come in future]
# Example Usage
- main.py:
 ```
 import pycam_module
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
 ```


    

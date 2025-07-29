import asyncio
import cv2
import numpy as np
import os
import sys
import time
import threading

__AUTOSTART__ = False
DEFAULT_WIDTH = 640
DEFAULT_HEIGHT = 480
DEFAULT_FRAMERATE = 30

# This function digs camera name from udevadm info
# Takes no arguments and returns list in format: 
#
#     camera_list 
#     [
#        cam1 ["/dev/video0","001:001","camera1"]
#        cam2 ["/dev/video1","001:002","camera2"]
#        cam3 ["/dev/video2","001:003","camera3"]
#        camX ["device_path","bus_addr","dev_name"]
#        ...
#    ]
#

def __list_devs_linux__():
    devices = []
    cameras=os.popen("ls /dev/ | grep 'video'| sort -V").read().split("\n")[:-1]
    for index,cam in enumerate(cameras):
        index_out = index+1
        if os.path.exists("/dev/{cam}".format(cam=cam)):
            vendor_id = os.popen(f"udevadm info --query=property --property='ID_VENDOR_ID' --value /dev/{cam}").read().strip()
            product_id = os.popen(f"udevadm info --query=property --property='ID_MODEL_ID' --value /dev/{cam}").read().strip()
            dev_line = os.popen(f"lsusb -d {vendor_id}:{product_id}").read().strip().split("\n")[index]
            dev_name = ""
            dev_pam_list = dev_line.split(f" ID {vendor_id}:{product_id} ") 
            dev_bus_addr = dev_pam_list[0]
            if len(dev_pam_list)>1: dev_name=dev_pam_list[1]
            bus=dev_bus_addr.replace("Bus ","").replace(" Device ",":")[:-1]
            devices.append([f"/dev/{cam}",bus,dev_name])
    return devices


# Adjusts gamma of the image in np.ndarray format 
# Takes image in format of np.ndarray and return image format nd.array [BGR|RGB]
def adjust_gamma(image, gamma=1):
    invGamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** invGamma) * 255
        for i in np.arange(0, 256)]).astype("uint8")
    return cv2.LUT(image, table)

# Adjusts Hue Saturation Value of image in format of np.ndarray [RGB]
# Takes image np.ndarray [RGB] returns back image np.ndarray [RGB]
def adjust_hsv(image,hsv=(1,1,1)):
    hsv_image = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    hsv_modified = hsv_image[:,:,:] * hsv
    hsv_modified = np.clip(hsv_modified,0,255).astype("uint8")
    return cv2.cvtColor(hsv_modified,cv2.COLOR_HSV2RGB)

# Creates new instance of cam_stream
class cam_stream():
    __video_stream__ = None
    __keep_stream__ = True
    __resolution__ = None
    __device_index__ = 0
    __framerate__ = None
    __cam_thread__ = None 
    __mirror__ = False
    __frame__ = None
    __hsv_adj__ = None
    __gamma_adj__ = None
    frame = None
    
    # Initialization binds a single camera "dev" to stream (Every stream has to have one bound camera)
    # Other arguments are self descriptive
    def __init__(self,device_index,res=(DEFAULT_WIDTH,DEFAULT_HEIGHT),framerate=DEFAULT_FRAMERATE,mirror=False):
        self.__device_index__ = device_index
        self.__framerate__ = framerate
        self.__resolution__  = res
        self.__mirror__ = mirror
        self.__cam_thread__ = threading.Thread(target=lambda:asyncio.run(self.__frame_loop__())) 
        self.__cam_thread__.daemon = True
        if __AUTOSTART__ == True: self.start_stream()
    
    # Initializes VideoCapture which is bound to device_path set in cam_stream.__init__
    # The same applies for other variables
    def __init_stream__(self):
        self.__keep_stream__ = True
        self.__video_stream__ = cv2.VideoCapture()
        self.__video_stream__.setExceptionMode(True)
        self.__video_stream__.open(self.__device_index__,apiPreference = getattr(cv2,{"windows":"CAP_MSMF","linux":"CAP_V4L"}[sys.platform]))
        self.__video_stream__.set(cv2.CAP_PROP_FPS, self.__framerate__)
        #self.__vide_stream__.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        self.__video_stream__.set(cv2.CAP_PROP_FRAME_WIDTH,self.__resolution__[0])
        self.__video_stream__.set(cv2.CAP_PROP_FRAME_HEIGHT,self.__resolution__[1])
        
    # This loop retrieves new frames, the loop is running as long as __keep_stream__ = True
    # This is required to make stream live reconfigurable and restartable => cam_stream.__restart_stream__()
    async def __frame_loop__(self):
        while True:
            print("Trying to access camera...")
            try: 
                self.__init_stream__()
            except Exception as e:
                pass
            while self.__keep_stream__:
                if self.__video_stream__.isOpened() == False:
                    break
                try:
                    if self.__video_stream__.grab():
                        __ret__,__frame__ = self.__video_stream__.retrieve()

                        if __ret__:
                            # Mirrors feed if enabled
                            if self.__mirror__: 
                                __frame__ = cv2.flip(__frame__,1)
                            # Adusts gamma if adjustment set
                            if self.__gamma_adj__ != None:
                                __frame__ = adjust_gamma(__frame__,self.__gamma_adj__)
                            # Adusts HSV if HSV adusjtment set
                            if self.__hsv_adj__ != None:
                                __frame__ = adjust_hsv(__frame__,self.__hsv_adj__)

                            self.__frame__ = __frame__
                            self.frame = cv2.cvtColor(self.__frame__.copy(),cv2.COLOR_BGR2RGB)
                        else:
                            break
                except Exception as e :
                    break

            print("Camera connection closed.")
            self.__video_stream__.release() 
            self.__video_stream__ = None
            self.frame = None
            await asyncio.sleep(1)

    # Breaks __frame_loop__ if running
    # Re-initializes VideoCapture with cam_stream variables and restarts the stream capture
    def __restart_stream__(self):
        self.__keep_stream__ = False
        self.__init_stream__()
        self.__frame_loop__()
   
    # Changes device_path bound to cam_stream and restarts it
    def set_device(self,dev_identifier):
        self.__device_path__ = dev_identifier
        self.__restart_stream__()

    # Changes framerate of cam_stream and restarts it
    def set_framerate(self,framerate):
        self.__framerate__ = framerate
        self.__restart_stream__()

    # Changes resolution of cam_stream and restarts it
    def set_resolution(self,res,framerate=None):
        if framerate != None:
            self.__framerate__ = framerate
        self.__resolution__ = res
        self.__restart_stream__()

    # Changes if the image is mirrored or not [Restart of cam_stream not required]
    def set_mirror(self,mirror):
        self.__mirror__ = mirror

    def adjust_hsv(self,hsv):
        self.__hsv_adj__ = hsv

    def adjust_gamma(self,gamma):
        self.__gamma_adj__ = gamma

    def reset_gamma(self):
        self.__gamma_adj__ = None

    def reset_hsv(self):
        self.__hsv_adj__ = None

    # Start cam_stream frame retrieving
    def start_stream(self):
        self.__keep_stream__ = True
        self.__init_stream__()
        self.__cam_thread__.start()

    # Breaks frame retrieving loop [Stops it]
    def stop_stream(self):
        self.__keep_stream__ = False

    # Saves current image and returns the current image in format np.ndarray colorspace [RGB]
    def take_image(self,save_path):
        print("Saving image ...")
        print(f"Save path: {save_path}")
        self.frame = cv2.cvtColor(self.__frame__.copy(),cv2.COLOR_BGR2RGB)
        cv2.imwrite( save_path,self.__frame__,[cv2.IMWRITE_PNG_COMPRESSION,0])
        return self.frame

# Bounds list_devices function for current platform
if os.name in ["linux","posix"]:
    list_devices = __list_devs_linux__
else:
    print(f"Unsupported platform: {os.name}")
    exit()

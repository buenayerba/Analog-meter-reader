'''
Python version: 2.7
OpenCV version: 3.4.0
'''

# ======================================================
# Import necessary libraries and helper functions
# ======================================================

import numpy as np
import cv2
import random
import sys
import math

# Helper function to find angle between vectors v1 and v2
def get_angle(v1, v2):
    v1 = v1 / np.linalg.norm(v1) # unit vector v1
    v2 = v2 / np.linalg.norm(v2) # unit vector v2
    cos_theta = np.dot(v1, v2)
    return np.arccos(cos_theta)*(180/np.pi)

def returnBaseAngle():
    gray = cv2.cvtColor(image_orig, cv2.COLOR_BGR2GRAY)
    retval, mask = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY_INV)
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    contours = sorted(contours, key = cv2.contourArea, reverse = True)
    index = 1 # alternatively can use a range of reasonable areas
    cnt = contours[index]

    # Find Tilt Angle of the Meter
    rect = cv2.minAreaRect(cnt)
    box = cv2.boxPoints(rect)
    box = np.int0(box)
    image_copy = np.copy(image_orig)
    image_copy = cv2.drawContours(image_copy,[box],0,(0,0,255),6)
    base_angle = get_angle([100, 0],  box[0] - box[1])
    base_angle = round(base_angle, 1)
    print(base_angle)


# ======================================================
# ======================================================
# MAIN
# ======================================================
# ======================================================

# IMG_PATH_ORIGINAL = "/Users/ivyliu/Desktop/W20-URA/code/original-images/image1_original.jpeg"
IMG_PATH_ORIGINAL = sys.argv[1]
image_orig = cv2.imread(IMG_PATH_ORIGINAL)
returnBaseAngle()

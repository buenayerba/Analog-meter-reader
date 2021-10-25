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
from helpers import imshow
import sys
import math
import xml.etree.ElementTree as ET
from datetime import datetime
import os.path

# ======================================================
# ======================================================
# HELPER METHODS
# ======================================================
# ======================================================

def apply_mask(image, mask):
    h = image.shape[0]
    w = image.shape[1]
    image_with_mask = np.copy(image)
    for y in range(h):
        for x in range(w):
            r, g, b = mask[y, x]
            if r == 0 and g == 0 and b == 0:
                continue
            else:
                image_with_mask[y, x] = (r, g, b)
    return image_with_mask

def resize_image(image, width = None, height = None, inter = cv2.INTER_AREA):
    dimimension = None
    (h, w) = image.shape[:2]

    if width is None and height is None:
        return image
    if width is None:
        ratio = height / float(h)
        dimimension = (int(w * ratio), height)
    else:
        ratio = width / float(w)
        dimimension = (width, int(h * ratio))

    resized = cv2.resize(image, dimimension, interpolation = inter)
    return resized

# generate a set of matrices A_x, of size (m,n), 
# where the xth matrix represents a vector drawn 
# from the origin making an angle x with the X axis
# x ranges from 0 to 360 in step of 5
def create_matrices(m, n):
    A = []
    origin_x = math.floor(n / 2)
    origin_y = math.floor(m / 2)
    max_r = max(origin_x, origin_y)

    for x in range(0, 360, 5):
        A_x = np.zeros((m, n, 3), np.uint8)
        A_x.fill(50)
        sinx = math.sin(x/180*3.14)
        cosx = math.cos(x/180*3.14)
        for r in range(max_r):
            if origin_x + math.floor(r * cosx) < m and origin_x + math.floor(r * cosx) >= 0 and origin_y + math.floor(r * sinx) < n and origin_y + math.floor(r * sinx) >= 0:
                A_x[origin_x + math.floor(r * cosx)][origin_y + math.floor(r * sinx)][:] = 0
            if origin_x + math.floor(r * cosx) < m and origin_x + math.floor(r * cosx) >= 0 and origin_y + math.ceil(r * sinx) < n and origin_y + math.ceil(r * sinx) >= 0:
                A_x[origin_x + math.floor(r * cosx)][origin_y + math.ceil(r * sinx)][:] = 0
            if origin_x + math.ceil(r * cosx) < m and origin_x + math.ceil(r * cosx) >= 0 and origin_y + math.floor(r * sinx) < n and origin_y + math.floor(r * sinx) >= 0:
                A_x[origin_x + math.ceil(r * cosx)][origin_y + math.floor(r * sinx)][:] = 0
            if origin_x + math.ceil(r * cosx) < m and origin_x + math.ceil(r * cosx) >= 0 and origin_y + math.ceil(r * sinx) < n and origin_y + math.ceil(r * sinx) >= 0:
                A_x[origin_x + math.ceil(r * cosx)][origin_y + math.ceil(r * sinx)][:] = 0
        A.append(A_x)
    return A

# perform dot product of two 3D-matrices A_x and B.
# i.e return the sum of each of the corresponding element
# Note: A_x and B have to have the same dimension
def matrix_dot_product(A_x, B):
    sum = 0
    # print("A lens: " + str(len(A_x)) + ", "+ str(len(A_x[0])) + ", "+ str(len(A_x[1])) + ", ")
    # print("B lens: " + str(len(B)) + ", "+ str(len(B[0])) + ", "+ str(len(B[1])) + ", ")
    for i in range(len(A_x)):
        for j in range(len(A_x[0])):
            #for k in range(len(A_x[1])):
                #print("i, j, k "+str(i) + ", "+ str(j) + ", "+ str(k) + ", ")
            sum += int(A_x[i][j][0]) * int(B[i][j][0])
            # if i < 60 and i > 55 and j < 60 and j > 55:
            #     print("i, j, k, A: " +str(i) + ", "+ str(j) + ", " + str(A_x[i][j][0]))
            #     print(B[i][j][0])
    return sum

# Parse arguments (string -> list)
# Require: s has to be in the format: 1,2,3,4...
def arg_parser(s):
    l = [] # returned list of points
    count = 1
    li = s.split(",")
    for i in li:
        if count == 1:
            p = [] # a point (x, y)
            p.append(int(float(i)))
        elif count == 0:
            p.append(int(float(i)))
            l.append(p)
        count = 1 - count
    return l
    
# Helper function to find angle between vectors v1 and v2
def get_angle(v1, v2):
    v1 = v1 / np.linalg.norm(v1) # unit vector v1
    v2 = v2 / np.linalg.norm(v2) # unit vector v2
    cos_theta = np.dot(v1, v2)
    return np.arccos(cos_theta)*(180/np.pi)

# return list1 - list2
# require: list1 and list2 have 2 elements
def subtract_vectors(l1, l2):
   l = []
   l.append(l1[0] - l2[0])
   l.append(l1[1] - l2[1])
   return l
    
# Method that calculates the reading based on the angle of a top dial
# angle is with respect to the positive x-axis
def get_reading_top(angle, type):
    # convert angle to be with respect to the positive y-axis
    if angle - 90 >= 0:
        angle = angle - 90
    else:
        angle = angle + 270

    if type == 0:
        return 10 - angle / 36
    else:
        return angle / 36

# Method that calculates the reading based on the boundary points and boundary readings of a bottom dial
def get_reading_bottom(angle, bottom_dial_bound, BOTTOM_READING_LEFT, BOTTOM_READING_RIGHT, dial_type):
    count = 1
    BOTTOM_DIAL_BASE_ANGLE_LEFT = 0
    BOTTOM_DIAL_BASE_ANGLE_RIGHT = 0
    
    for point in bottom_dial_bound:
        # Get the boundary readings of the bottom dial
        if count == 1:
            tip = point
        elif count == 2:
            base = point
            BOTTOM_DIAL_BASE_ANGLE_LEFT = get_angle([100, 0], subtract_vectors(base, tip))
        elif count == 3:
            tip = point
        elif count == 4:
            base = point
            BOTTOM_DIAL_BASE_ANGLE_RIGHT = get_angle([100, 0], subtract_vectors(base, tip))
        count = count + 1
        
    if dial_type == 1: # linear scale
        reading_per_degree = (BOTTOM_READING_RIGHT - BOTTOM_READING_LEFT) / (BOTTOM_DIAL_BASE_ANGLE_RIGHT - BOTTOM_DIAL_BASE_ANGLE_LEFT)
        return(angle - BOTTOM_DIAL_BASE_ANGLE_LEFT) * reading_per_degree
        
    if dial_type == 2: # log scale
        #    print("angles of bottom left, right: ", BOTTOM_DIAL_BASE_ANGLE_LEFT, ", ", BOTTOM_DIAL_BASE_ANGLE_RIGHT)
        #    print("boundary readings: ", BOTTOM_READING_RIGHT, ", ", BOTTOM_READING_LEFT)
        BOTTOM_READING_RIGHT = math.log(BOTTOM_READING_RIGHT, 10)
        if BOTTOM_READING_LEFT != 0:
            BOTTOM_READING_LEFT = math.log(BOTTOM_READING_LEFT, 10)
        reading_per_degree = (BOTTOM_READING_RIGHT - BOTTOM_READING_LEFT) / (BOTTOM_DIAL_BASE_ANGLE_RIGHT - BOTTOM_DIAL_BASE_ANGLE_LEFT)
        x = (angle - BOTTOM_DIAL_BASE_ANGLE_LEFT) * reading_per_degree
        return 10**x


# Method that generates a binary mask (using upper and lower boundaries in HSV color space)
def segment_image_hsv(image, min_HSV, max_HSV):
    # Convert image to HSV
    hsv = cv2.cvtColor(image,cv2.COLOR_BGR2HSV)

    # create a mask and clean it up
    mask = cv2.inRange(hsv, min_HSV, max_HSV)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, None, iterations = 1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, None, iterations = 5)
    mask = cv2.medianBlur(mask, 5)
    return cv2.bitwise_not(mask)
   
    
# Helper function to find angle between vectors v1 and v2
def get_angle(v1, v2):
    v1 = v1 / np.linalg.norm(v1) # unit vector v1
    v2 = v2 / np.linalg.norm(v2) # unit vector v2
    cos_theta = np.dot(v1, v2)
    return np.arccos(cos_theta)*(180/np.pi)
    

# Get sharpest peak in the contour whose k-curvature angle is smaller than thresh_angle.
def get_tip_index(samplePoints, thresh_angle, k):
    min_curv_angle = float('inf')
    tip_index = -1
    for j in range(len(samplePoints)):
        # determine points corresponding to indices j-k, j and j+k
        jCoord = samplePoints[j][0]
        minusK = samplePoints[(j-k)%len(samplePoints)][0]
        plusK = samplePoints[(j+k)%len(samplePoints)][0]
        kCurvAngle = get_angle(minusK - jCoord, plusK - jCoord)
        if kCurvAngle <= thresh_angle and kCurvAngle < min_curv_angle:
            min_curv_angle = kCurvAngle
            orientation = np.cross(minusK - jCoord, plusK - jCoord)
            if orientation >= 0:
                tip_index = j
    return tip_index


# Calculate angle between an arrow and the negative horizontal axis.
# Idea: find a midpoint between C[tip_index-step] and C[tip_index+step] (where C is an array of
# evenly spaced contour points). Next, find an angle between the midpoint-to-the-tip vector
# and the negative horizontal axis.
# For robustness, we do it for several different steps, and take median.
def get_arrow_angle(samplePoints, tip_index):
    angles = []
    # step is number of points away from the tip.
    for step in range(14, 22):
        tip_coord = samplePoints[tip_index][0]
        plusK = samplePoints[(tip_index + step)%len(samplePoints)][0]
        minusK = samplePoints[(tip_index - step)%len(samplePoints)][0]
        mid_point = np.mean([minusK, plusK], axis=0).astype(int)

        orientation = np.cross([100, 0], mid_point - tip_coord) # whether cross product points up or down
        angle = np.sign(orientation) * get_angle([100, 0],  mid_point - tip_coord)*3.14/180.0
        angles.append(angle)
    median_angle = sorted(angles)[int(len(angles) / 2)]
    return median_angle # angle in radians


# Draw orientation of the arrow on the image.
# Note: This method modifies image.
def draw_arrow_orientation(image, samplePoints, tip_index, angle, length):
    
    # Point 1
    x1 = samplePoints[tip_index%len(samplePoints)][0][0] + 1* length * np.cos(angle)
    y1 = samplePoints[tip_index%len(samplePoints)][0][1] + 1* length * np.sin(angle)
    point1 = [int(x1), int(y1)]

    # Point 2
    x2 = samplePoints[tip_index%len(samplePoints)][0][0] - 3*length * np.cos(angle)
    y2 = samplePoints[tip_index%len(samplePoints)][0][1] - 3*length * np.sin(angle)
    point2 = [int(x2), int(y2)]
    
    cv2.line(image, tuple(point1), tuple(point2), (0, 0, 255), 4)
    

# This method processes the contour of an arrow, and returns its angle with respect to the negative horizontal axis.
def from_arrow_cnt_to_angle(image, contour, thresh_angle, k, num_sample_poits):
    interval = len(contour)/num_sample_poits
    samplePoints = contour[0:len(contour):int(interval)]

    # Draw a contour
    for index in range(len(samplePoints)):
        cv2.circle(image, tuple(samplePoints[index][0]), 3, (255, 255, 255), 2)
    
    tip_index = get_tip_index(samplePoints, thresh_angle, k)
    if tip_index!=-1:
        angle = get_arrow_angle(samplePoints, tip_index)
        angle_degrees = angle*180.0/3.14
        draw_arrow_orientation(image, samplePoints, tip_index, angle, 50)
        jCoord = samplePoints[tip_index][0] # Draw arrow tip as blue circles
        cv2.circle(image, tuple(jCoord), 3, (255, 0, 0), 3)
        cv2.putText(image, str("%.1f"%angle_degrees), (jCoord[0], jCoord[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 3, (0,0,255), 2)
        #imshow(image, "temp image")
        return angle_degrees
    else:
        return float('inf')
        
'''
Method for processing the top dials for a given segmentation threshold.
This method returns:
    "high" - if segmentation threshold is too high
    "low" - if segmentation threshold is too low
    Array of four angles (for four arrows) - if segmentation threshold is good enough
'''
def process_top_dials(seg_threshold, min_area, max_area,
                      thresh_angle, k, num_sample_points, color_range):
    global top_dials
    global top_dials_original
    angles = [] # angles of arrows with positive x-axis

    # Get a binary mask and clean it up.
    retval, mask = cv2.threshold(top_dials_gray, seg_threshold, 255, cv2.THRESH_BINARY_INV )
    median = cv2.medianBlur(mask, 21)
    mask = cv2.morphologyEx(median, cv2.MORPH_CLOSE, None, iterations = 6)
    mask = cv2.morphologyEx(median, cv2.MORPH_OPEN, None, iterations = 3)
    ##imshow(mask, "MASK")

    num_pixels = mask.size
    num_nonzero_pixels = cv2.countNonZero(mask)
    ratio = float(num_nonzero_pixels)/num_pixels
    print ("Fraction of nonzero pixels:", ratio)
    
    # Case 1: If ratio of nonzero pixels is too high, the threshold is too high.
    if ratio > 0.15:
        print ("   threshold is too high")
        return "high"
    if ratio < 0.05:
        print ("   threshold is too low")
        return "low"
    
    # ========================= Get contour of each "inner circle" ========================
    lower = np.array(color_range[0])
    upper = np.array(color_range[1])
    mask = cv2.inRange(top_dials, lower, upper)
    #imshow(mask, "Region of top dials")
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=lambda ctr: cv2.boundingRect(ctr)[0]) # Sort left to right
    
    a = 0
    for contour in contours:
        # a += 1
        # if a != 1:
        #      continue
        center, radius = cv2.minEnclosingCircle(contour)

        # ================== cast values of center and radius to integer ===================
        c = list(center)
        c[0] = int(c[0])
        c[1] = int(c[1])
        center = tuple(c)
        radius *= 0.75
        radius = int(radius)

        # ======================= draw the contour and crop the image =======================
        top_dials_copy = np.copy(top_dials_original)
        cv2.circle(top_dials_copy, center, radius, (255, 0, 255), 2)
        #imshow(top_dials_copy, "Region of one top dial")
        one_top_dial = top_dials_original[center[1]-radius:center[1]+radius, center[0]-radius:center[0]+radius]
        one_top_dial_gray = cv2.cvtColor(one_top_dial, cv2.COLOR_BGR2GRAY)
        #imshow(one_top_dial_gray, "One top dial gray")
        rows,cols = one_top_dial_gray.shape

        # ====================== find Convex Hull of one_top_dial_gray ======================
        # Get a binary mask and clean it up.
        retval, mask = cv2.threshold(one_top_dial_gray, seg_threshold, 180, cv2.THRESH_BINARY_INV)
        median = cv2.medianBlur(mask, 21)
        #imshow(mask, "MASK")
        mask = cv2.morphologyEx(median, cv2.MORPH_CLOSE, None, iterations = 6)
        mask = cv2.morphologyEx(median, cv2.MORPH_OPEN, None, iterations = 3)
        contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # create hull array for convex hull points
        hull = [] 
        for i in range(len(contours)):
            hull.append(cv2.convexHull(contours[i], False))
        # draw contours and hull points
        drawing = np.zeros((rows, cols, 3), np.uint8)
        drawing.fill(50)
        for i in range(len(contours)):
            color_contours = (0, 0, 0)
            color = (0, 0, 0)
            cv2.drawContours(drawing, contours, i, color_contours, 1, 8, hierarchy)
            cv2.drawContours(drawing, hull, i, color, 1, 8)
            cv2.fillPoly(drawing, hull, color)

        #imshow(drawing, "Identified Convex Hull")

        # ======= find the maximum dot product between the processed image and A_x's ========
        A = create_matrices(rows, cols)
        i = 0
        prod = 0
        angle = 0
        angle1 = 0
        angle2 = 0
        for x in range(0, 360, 5):
            temp = matrix_dot_product(A[i], drawing)
            if x == 0:
                prod = temp
            if temp > prod:
                prod = temp
                angle1 = x
            # if x > 0 and x < 20:
            #     #imshow(A[i], "A[i]")
            #     print("temp, prod: " + str(x) + ", " + str(temp), ", " + str(prod))
            # if x > 180 and x < 200:
            #     #imshow(A[i], "A[i]")
            #     print("temp, prod: " + str(x) + ", " + str(temp), ", " + str(prod))
            i += 1
        i = 0
        for x in range(0, 360, 5):
            temp = matrix_dot_product(A[i], drawing)
            if x == 0:
                prod = temp
            if temp >= prod:
                prod = temp
                angle2 = x
            i += 1
        if abs(angle1 - angle2) > 35:
            angle = angle1
        else:
            angle = (angle1 + angle2) / 2
        # print("old angle: " + str(angle), ", " + str(angle1) + ", " + str(angle2))
        
        # convert angle wrt negative y-axis to positve x-axis
        if angle - 90 >= 0:
            angle -= 90
        else:
            angle += 270
        
        # ======= draw the line indicating the angle ========
        origin_x = math.floor(cols / 2)
        origin_y = math.floor(rows / 2)
        sinx = math.sin(angle/180*3.14)
        cosx = math.cos(angle/180*3.14)
        r = min(cols, rows) / 2
        cv2.line(drawing,(origin_x, origin_y),(origin_x + math.floor(r * cosx), origin_y - math.floor(r * sinx)),(0,0,255),3)
        #imshow(drawing, "Found Angle")
        angles.append(angle)
    return angles

def displayError(i):
    if i == 1:
        print("Integer required. Please try again.")
    else:
        print("Number required. Please try again.")
    exit()


# ======================================================
# ======================================================
# MAIN
# ======================================================
# ======================================================

IMG_PATH = ""
IMG_PATH_ORIGINAL = ""

# CONSTANTS:
K = 10
THRESH_ANGLE = 60
NUM_SAMPLE_POINTS_SMALL_ARROW = 50
NUM_SAMPLE_POINTS_LONG_ARROW = 250
SMALL_ARROW_MIN_AREA = 3000
SMALL_ARROW_MAX_AREA = 6000
IMAGE_WIDTH = 960
IMAGE_HEIGHT = 720

# FOR GENERAL METER
BOTTOM_DIAL_BASE_ANGLE_LEFT = 48
BOTTOM_DIAL_BASE_ANGLE_RIGHT = 33.75
BOTTOM_READING_LEFT = 0
BOTTOM_READING_RIGHT = 0
GET_BASE_ANGLE_ONLY = 0
DIAL_TYPE = 0 # 1 - CIRCULAR_DIAL_ONLY, 2 - SCALE_ONLY, 3 - BOTH
NUM_OF_CIRCULAR_DIALS = 0
ORIENTATION_OF_FIRST_DIAL = 0
BOTTOM_DIAL_BOUNDARY_POINTS = []
base_angle = 0
SCALE_TYPE = 1
LOG_FILENAME = ""

# Color HSV
boundaries = [
    ([220, 220, 220], [256, 256, 256]), # white
    ([17, 15, 130], [50, 56, 260]),     # red
    ([86, 31, 4], [220, 88, 50]),       # blue
    ([0, 200, 220], [150, 260, 260]),   # yellow
    ([36,0,0], [86,255,255]),           # green
    ([180,0,100], [200,100,170])        # purple
]

# Parse meter_property.xml
tree = ET.parse('meter_property.xml')
root = tree.getroot()
for child in root:
    tag = child.tag
    attrib = child.attrib
    # if tag == "image_unedited":
    #     IMG_PATH_ORIGINAL = child.text
    if tag == "meter_type":
        try:
            DIAL_TYPE = int(child.text)
        except:
            displayError(1)
    elif tag == "base_angle":
        try:
            base_angle = float(child.text)
        except:
            displayError(2)
    elif tag == "number_of_dial":
        try:
            NUM_OF_CIRCULAR_DIALS = int(child.text)
        except:
            displayError(1)
    elif tag == "orientation":
        try:
            ORIENTATION_OF_FIRST_DIAL = int(child.text)
        except:
            displayError(1)
    elif tag == "coordinates":
        s = ""
        for val in child:
            s += val.text
            s += ","
        s = s[:-1]
        bottom_dial_bound = arg_parser(s)
    elif tag == "boundary_reading":
        s = ""
        for val in child:
            s += val.text
            s += ","
        s = s[:-1]
        l = arg_parser(s)
        BOTTOM_READING_LEFT = l[0][0]
        BOTTOM_READING_RIGHT = l[0][1]
    elif tag == "log_or_linear":
        try:
            SCALE_TYPE = int(child.text)
        except:
            displayError(1)
    elif tag == "filename_to_save":
        LOG_FILENAME = child.text

# get the original image and resize
IMG_PATH_ORIGINAL = sys.argv[1]
image_orig = cv2.imread(IMG_PATH_ORIGINAL)
image_orig = resize_image(image_orig, height = 720)
# image_orig = cv2.resize(image_orig, (IMAGE_WIDTH, IMAGE_HEIGHT))

# get the edited image from mask
mask = cv2.imread("mask.jpeg")
image_temp = apply_mask(image_orig, mask)
cv2.imwrite("image_with_mask.jpeg",image_temp) # save the image in current directory
image = cv2.imread("image_with_mask.jpeg") # get this image

# =============================================================================
# STEP 0: Get the General Region of Interest (ROI) and Find Tilt Angle of the Meter
## =============================================================================

print ("*"*30, "\nSTEP 1: LOOKING FOR THE GENERAL AREA OF INTEREST ...")
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
#imshow(gray)

# find the color within the specified boundaries (white) and apply mask
ran = boundaries[0]
lower = np.array(ran[0])
upper = np.array(ran[1])
mask = cv2.inRange(image, lower,  upper)

#imshow(mask)
contours, hierarchy = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
contours = sorted(contours, key = cv2.contourArea, reverse = True)
index = 1 # alternatively can use a range of reasonable areas
cnt = contours[index]
rect = cv2.minAreaRect(cnt)
box = cv2.boxPoints(rect)
box = np.int0(box)
image = cv2.drawContours(image,[box],0,(0,0,255),6)
#imshow(image, "General area bounding rectangle")

# General ROI of the meter
x_min = min([pair[0][0] for pair in cnt]) + 5
x_max = max([pair[0][0] for pair in cnt]) - 5
y_min = min([pair[0][1] for pair in cnt]) + 5
y_max = max([pair[0][1] for pair in cnt]) - 5

#meter_ROI = image[y_min:y_max, x_min:x_max] # Meter's ROI
image = image[y_min:y_max, x_min:x_max] # Meter's ROI
#imshow(image, "General region of interest: Meter")

REF_METER_HEIGHT = 2100.0
scale = REF_METER_HEIGHT / len(image)
image = cv2.resize(image, None, fx=scale, fy=scale, interpolation = cv2.INTER_CUBIC)

# =============================================================================
# STEP 1: Find Tilt Angle of the Meter (use the original image)
# =============================================================================
if DIAL_TYPE == 0:

    print ("*"*30, "\nSTEP 1: LOOKING FOR THE METER ...")
    gray = cv2.cvtColor(image_orig, cv2.COLOR_BGR2GRAY)
    #imshow(gray)
    retval, mask = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY_INV)
    #imshow(mask)
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
    print ("Tilt (base) angle of the meter:", "%.1f"%base_angle)
    #imshow(image_copy, "Minimum area bounding rectangle\nBase angle: {0:.1f} degrees".format(base_angle))

# for getting rid of the rectangles drawn on the image
meter_ROI = image_orig[y_min:y_max, x_min:x_max] # Meter's ROI
REF_METER_HEIGHT = 2100.0
scale = REF_METER_HEIGHT / len(meter_ROI)
meter_ROI = cv2.resize(meter_ROI, None, fx=scale, fy=scale, interpolation = cv2.INTER_CUBIC)

# =============================================================================
# STEP 2: Get angles of small arrows
# =============================================================================

if DIAL_TYPE == 1 or DIAL_TYPE == 3:

    print ("*"*30, "\nSTEP 2: LOOKING FOR ANGLES OF THE SHORT ARROWS ...")
    final_top_reading = ""

    # find contour of top dials
    ran = boundaries[1]
    lower = np.array(ran[0])
    upper = np.array(ran[1])
    mask = cv2.inRange(image, lower, upper)
    #imshow(mask)
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key = cv2.contourArea, reverse = True)

    k = 1
    for contour in contours:
        [x, y, w, h] = cv2.boundingRect(contour)
        if k == 1:
            x_min = x
            x_max = x + w
            y_min = y
            y_max = y + h
        else:
            if x < x_min:
                x_min = x
            if y < y_min:
                y_min = y
            if x + w > x_max:
                x_max = x + w
            if y + h > y_max:
                y_max = y + h
        k = k + 1
    image_copy = np.copy(image)
    cv2.rectangle(image_copy, (x_min, y_min), (x_max, y_max), (255, 0, 255), 2)
    #imshow(image_copy, "Contour for top dials")

    top_dials = image[y_min-10:y_max, x_min-5:x_max] # with inner circles drawn 
    top_dials_original = meter_ROI[y_min-10:y_max, x_min-5:x_max] # without inner circles
    #imshow(top_dials_original, "Top dials")
    top_dials_gray = cv2.cvtColor(top_dials_original, cv2.COLOR_BGR2GRAY)

    # Binary search to find a good segmentaiton threshold.
    l, r = 0, 255
    while r - l >= 0:
        mid = (l+r) / 2
        print ("*"*30, "\n", "TRY THRESHOLD {}".format(mid))
        angles = process_top_dials(mid, SMALL_ARROW_MIN_AREA, SMALL_ARROW_MAX_AREA,
                            THRESH_ANGLE, K, NUM_SAMPLE_POINTS_SMALL_ARROW, boundaries[3])
        if angles == "low":
            l = mid+1
        elif angles == "high":
            r = mid-1
        else:
            break

    # print out result
    print ("\n\n", "#"*30, "\n", "#"*30)
    print ("GOOD ANGLES FOUND!")
    print ("ANGLES OF THE SHORT ARROWS (FROM LEFT TO RIGHT):")
    i = 0
    for angle in angles:
        i += 1
        print ("   Angle {}: {}".format(i, "%.1f"%angle))
        
    print ("\n\nANGLES ADJUSTED W.R.T. THE BASE ANGLE (FROM LEFT TO RIGHT):")
    i = 0
    for angle in angles:
        i += 1
        print ("   Angle {}: {}".format(i, "%.1f"%(angle - base_angle)))
    
    print ("\n\nREADINGS W.R.T TO THE ANGLE (FROM LEFT TO RIGHT):")
    i = 0
    total_reading = 0
    for angle in angles:
        i += 1
        if ORIENTATION_OF_FIRST_DIAL == 1:
            top_reading_temp = get_reading_top(angle - base_angle, (i+1) % 2)
            print ("   Reading {}: {}".format(i, "%.1f"%(top_reading_temp)))
        else:
            top_reading_temp = get_reading_top(angle - base_angle, i % 2)
            print ("   Reading {}: {}".format(i, "%.1f"%(top_reading_temp)))
        total_reading += top_reading_temp * pow(10, NUM_OF_CIRCULAR_DIALS - i)
    print ("#"*30, "\n", "#"*30, "\n\n")
    total_reading = round(total_reading, 1)
    final_top_reading += str(total_reading)

    f = open(LOG_FILENAME, "a")
    f.write(datetime.now().strftime("%m-%d-%Y,%H:%M:%S"))
    f.write(",")
    f.write(final_top_reading)
    f.write(",")
    

# =============================================================================
# STEP 3: Get angles of the long arrow
# =============================================================================

if DIAL_TYPE == 2 or DIAL_TYPE == 3:

    print ("*"*30, "\nSTEP 3: LOOKING FOR ANGLES OF THE LONG ARROW ...")
    final_main_reading = ""

    if DIAL_TYPE == 2:
        ran = boundaries[1]
    else:
        ran = boundaries[2]
    lower = np.array(ran[0])
    upper = np.array(ran[1])
    mask = cv2.inRange(image, lower, upper)

    #imshow(mask)
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key = cv2.contourArea, reverse = True)

    k = 1
    for contour in contours:
        [x, y, w, h] = cv2.boundingRect(contour)
        if k == 1:
            x_min = x
            x_max = x + w
            y_min = y
            y_max = y + h
        else:
            if x < x_min:
                x_min = x
            if y < y_min:
                y_min = y
            if x + w > x_max:
                x_max = x + w
            if y + h > y_max:
                y_max = y + h
        k = k + 1
    image_copy = np.copy(image)
    cv2.rectangle(image_copy, (x_min, y_min), (x_max, y_max), (255, 0, 255), 2)
    #imshow(image_copy, "Contour for main dial")
    bottom_dial = meter_ROI[y_min-10:y_max, x_min-5:x_max]
    #imshow(bottom_dial, "Bottom dial")

    bottom_dial_gray = cv2.cvtColor(bottom_dial, cv2.COLOR_BGR2GRAY)
    retval, mask = cv2.threshold(bottom_dial_gray, 75, 255, cv2.THRESH_BINARY_INV )
    median = cv2.medianBlur(mask, 21)
    mask = cv2.morphologyEx(median, cv2.MORPH_CLOSE, None, iterations = 6)
    mask = cv2.morphologyEx(median, cv2.MORPH_OPEN, None, iterations = 3)
    #imshow(mask, "MASK")

    contours, hierarchy = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    contours.sort(key = cv2.contourArea, reverse = True) # Sort by area
    large_arrow_cnt = contours[0]
    angle = from_arrow_cnt_to_angle(bottom_dial, large_arrow_cnt, THRESH_ANGLE, K, NUM_SAMPLE_POINTS_LONG_ARROW)
    bottom_reading_temp = get_reading_bottom(angle, bottom_dial_bound, BOTTOM_READING_LEFT, BOTTOM_READING_RIGHT, SCALE_TYPE)
    print ("\n\n", "#"*30, "\n", "#"*30)
    print ("ANGLE OF THE LOGN ARROW: {}".format("%.1f"%angle))
    print ("ANGLE OF THE LOGN ARROW ADJUSTED W.R.T. THE BASE ANGLE: {}".format("%.1f"%(angle-base_angle)))
    print ("READING OF THE BOTTOM DIAL: {}".format("%.1f"%(bottom_reading_temp)))
    print ("#"*30, "\n", "#"*30, "\n\n")
    #imshow(bottom_dial, "Long arrow detected!")
    bottom_reading_temp = round(bottom_reading_temp, 1)
    final_main_reading += str(bottom_reading_temp)
    f.write(final_main_reading)
    f.write("\n")

f.close()

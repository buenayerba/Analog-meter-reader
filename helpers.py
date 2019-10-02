import numpy as np
import matplotlib.pyplot as plt
import cv2

# helper functions

# convienient way to display inline images
def imshow(img, title = ''):
    # hide the x and y axis for images
    plt.axis('off')
    # RGB images are actually BGR in OpenCV, so convert before displaying
    if len(img.shape) == 3: 
        plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    # otherwise, assume it's grayscale and just display it
    else:
        plt.imshow(img)
    # add a title if specified
    plt.title(title)
    plt.show()


if __name__ == '__main__':
    pass
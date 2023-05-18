import cv2
import numpy as np
import pandas as pd
import os
import pytesseract as pt
import easyocr
import matplotlib.pyplot as plt
import xml.etree.ElementTree as xet
from shutil import copy
import tensorflow as tf
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from tensorflow.keras.models import Model
import tensorflow as tf
from tensorflow.keras.callbacks import TensorBoard


# settings
INPUT_WIDTH =  640
INPUT_HEIGHT = 640

# LOAD THE IMAGE
#img = cv2.imread('./test_images/getty_sample.jpg')

#cv2.namedWindow('test image',cv2.WINDOW_KEEPRATIO)


# LOAD YOLO MODEL
net = cv2.dnn.readNetFromONNX('https://drive.google.com/file/d/1tIGKrHYwKB8vnbBwtIES_J-EZNHEVKBF/view?usp=share_link')
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

def get_detections(img,net):
    # CONVERT IMAGE TO YOLO FORMAT
    image = img.copy()
    row, col, d = image.shape

    max_rc = max(row,col)
    input_image = np.zeros((max_rc,max_rc,3),dtype=np.uint8)
    input_image[0:row,0:col] = image

    # GET PREDICTION FROM YOLO MODEL
    blob = cv2.dnn.blobFromImage(input_image,1/255,(INPUT_WIDTH,INPUT_HEIGHT),swapRB=True,crop=False)
    net.setInput(blob)
    preds = net.forward()
    detections = preds[0]
    
    return input_image, detections

def non_maximum_supression(input_image,detections):
    # FILTER DETECTIONS BASED ON CONFIDENCE AND PROBABILIY SCORE
    # center x, center y, w , h, conf, proba
    boxes = []
    confidences = []

    image_w, image_h = input_image.shape[:2]
    x_factor = image_w/INPUT_WIDTH
    y_factor = image_h/INPUT_HEIGHT

    for i in range(len(detections)):
        row = detections[i]
        confidence = row[4] # confidence of detecting license plate
        if confidence > 0.4:
            class_score = row[5] # probability score of license plate
            if class_score > 0.25:
                cx, cy , w, h = row[0:4]

                left = int((cx - 0.5*w)*x_factor)
                top = int((cy-0.5*h)*y_factor)
                width = int(w*x_factor)
                height = int(h*y_factor)
                box = np.array([left,top,width,height])

                confidences.append(confidence)
                boxes.append(box)

    # clean
    boxes_np = np.array(boxes).tolist()
    confidences_np = np.array(confidences).tolist()
    # NMS
    index = cv2.dnn.NMSBoxes(boxes_np,confidences_np,0.25,0.45).flatten()
    
    return boxes_np, confidences_np, index

def drawings(image,boxes_np,confidences_np,index):
    # drawings
    global x,y,w,h
    for ind in index:
        x,y,w,h,=  boxes_np[ind]
        
        bb_conf = confidences_np[ind]
        conf_text = 'plate: {:.0f}%'.format(bb_conf*100)
        license_text = extract_text(image,boxes_np[ind])


        cv2.rectangle(image,(x,y),(x+w,y+h),(255,0,255),2)
        cv2.rectangle(image,(x,y-30),(x+w,y),(255,0,255),-1)
        cv2.rectangle(image,(x,y+h),(x+w,y+h+30),(0,0,0),-1)


        cv2.putText(image,conf_text,(x,y-10),cv2.FONT_HERSHEY_SIMPLEX,0.7,(255,255,255),1)
        cv2.putText(image,license_text,(x,y+h+27),cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,255,0),1)

    return image

# predictions
def yolo_predictions(img,net):
    ## step-1: detections
    input_image, detections = get_detections(img,net)
    ## step-2: NMS
    boxes_np, confidences_np, index = non_maximum_supression(input_image, detections)
    ## step-3: Drawings
    result_img = drawings(img,boxes_np,confidences_np,index)
    return result_img

def extract_text(image,bbox):
    x,y,w,h = bbox
    roi = image[y:y+h, x:x+w]
    coords=roi
    if 0 in roi.shape:
        return ''
    
    else:
        reader=easyocr.Reader(['en'])
        results=reader.readtext(roi)
        text=''
        for result in results:
            text+=result[1]+''
        print(text)
        return text
    
# test
img = cv2.imread("./Images/N (3).jpeg")
#cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

results = yolo_predictions(img,net)




x1,y1,x2,y2=x,y,w,h
cropped=img[y:y+h,x:x+w]
image_rgb = cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB)
plt.imshow(image_rgb)
plt.show()
plt.imshow(results)
plt.show()
results = yolo_predictions(img,net)
cv2.namedWindow("results",cv2.WINDOW_KEEPRATIO)
cv2.imshow('cropped',cropped)
cv2.waitKey(0)
cv2.destroyAllWindows()
cv2.namedWindow("results",cv2.WINDOW_KEEPRATIO)
cv2.imshow('cropped',results)
cv2.waitKey(0)
cv2.destroyAllWindows()
# =============================================================================
cap = cv2.VideoCapture()
 
 
while True:
     ret, frame = cap.read()
     
     if ret == False:
         print('unable to read video')
         break
         
     results = yolo_predictions(frame,net)
     
     cv2.namedWindow('YOLO',cv2.WINDOW_KEEPRATIO)
     cv2.imshow('YOLO',results)
     if cv2.waitKey(1) == 27:
         break
     

#=============================================================================
        
cv2.destroyAllWindows()
cap.release()
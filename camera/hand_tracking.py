import cv2

def iniciar_camera():
    cap = cv2.VideoCapture(0)
    return cap
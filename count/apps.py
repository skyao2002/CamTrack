from django.apps import AppConfig
from django.conf import settings
import os
import cv2

class ModelConfig(AppConfig):
    # create path to models
    prototxt_path = os.path.join(settings.MODELS, 'MobileNetSSD_deploy.prototxt')
    model_path = os.path.join(settings.MODELS, 'MobileNetSSD_deploy.caffemodel')

    # load models
    # these will be accessible via this class
    print("[INFO] loading model...")
    net = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)

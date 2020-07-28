from celery import shared_task
from django.conf import settings
import os

from .people_tracking.pyimagesearch.centroidtracker import CentroidTracker
from .people_tracking.pyimagesearch.trackableobject import TrackableObject
from imutils.video import VideoStream
from imutils.video import FPS
from .models import Count
import numpy as np
import argparse
import imutils
import time
import dlib
import cv2

@shared_task
def sleepy(duration):
    time.sleep(duration)
    return None

@shared_task
def track(name, **args):
    # create path to models
    prototxt_path = os.path.join(settings.MODELS, 'MobileNetSSD_deploy.prototxt')
    model_path = os.path.join(settings.MODELS, 'MobileNetSSD_deploy.caffemodel')

    # load models
    # these will be accessible via this class
    print("[INFO] loading model...")
    net = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)

    CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
		"bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
		"dog", "horse", "motorbike", "person", "pottedplant", "sheep",
		"sofa", "train", "tvmonitor"]
    
    client = Count.objects.get(name=name)

    # if a video path was not supplied, grab a reference to the webcam
    if args["input"] == None:
        print("[INFO] starting video stream...")
        vs = VideoStream(src=0).start()
        time.sleep(2.0)

    # otherwise, grab a reference to the ip camera
    else:
        print("[INFO] opening ip camera feed...")
        vs = VideoStream(args["input"]).start()
        time.sleep(2.0)

    if vs.read() is None:
        return "The video stream is offline or invalid"
    
    client.tracking = True
    print('started tracking')
    client.save()

    W = None
    H = None

    ct = CentroidTracker(maxDisappeared=40, maxDistance=100)
    trackers = []
    trackableObjects = {}

    totalFrames = 0

    fps = FPS().start()
    while client.tracking:
        client.refresh_from_db()
        frame = vs.read()
        
        frame = imutils.resize(frame, width=500)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        if W is None or H is None:
            (H, W) = frame.shape[:2]

        # initialize the current status along with our list of bounding
        # box rectangles returned by either (1) our client detector or
        # (2) the correlation trackers
        status = "Waiting"
        rects = []

        # check to see if we should run a more computationally expensive
        # client detection method to aid our tracker
        if totalFrames % args["skip_frames"] == 0:
            # set the status and initialize our new set of object trackers
            status = "Detecting"
            trackers = []

            # convert the frame to a blob and pass the blob through the
            # network and obtain the detections
            blob = cv2.dnn.blobFromImage(frame, 0.007843, (W, H), 127.5)
            net.setInput(blob)
            detections = net.forward()

            # loop over the detections
            for i in np.arange(0, detections.shape[2]):
                # extract the confidence (i.e., probability) associated
                # with the prediction
                confidence = detections[0, 0, i, 2]

                # filter out weak detections by requiring a minimum
                # confidence
                if confidence > args["confidence"]:
                    # extract the index of the class label from the
                    # detections list
                    idx = int(detections[0, 0, i, 1])

                    # if the class label is not a person, ignore it
                    if CLASSES[idx] != "person":
                        continue

                    # compute the (x, y)-coordinates of the bounding box
                    # for the object
                    box = detections[0, 0, i, 3:7] * np.array([W, H, W, H])
                    (startX, startY, endX, endY) = box.astype("int")

                    # construct a dlib rectangle object from the bounding
                    # box coordinates and then start the dlib correlation
                    # tracker
                    tracker = dlib.correlation_tracker()
                    rect = dlib.rectangle(startX, startY, endX, endY)
                    tracker.start_track(rgb, rect)

                    # add the tracker to our list of trackers so we can
                    # utilize it during skip frames
                    trackers.append(tracker)

        # otherwise, we should utilize our object *trackers* rather than
        # object *detectors* to obtain a higher frame processing throughput
        else:
            # loop over the trackers
            for tracker in trackers:
                # set the status of our system to be 'tracking' rather
                # than 'waiting' or 'detecting'
                status = "Tracking"

                # update the tracker and grab the updated position
                tracker.update(rgb)
                pos = tracker.get_position()

                # unpack the position object
                startX = int(pos.left())
                startY = int(pos.top())
                endX = int(pos.right())
                endY = int(pos.bottom())

                # add the bounding box coordinates to the rectangles list
                rects.append((startX, startY, endX, endY))

        # use the centroid tracker to associate the (1) old object
        # centroids with (2) the newly computed object centroids
        objects = ct.update(rects)

        # loop over the tracked objects
        for (objectID, centroid) in objects.items():
            # check to see if a trackable object exists for the current
            # object ID
            to = trackableObjects.get(objectID, None)				

            if to is None:
                if args["enter_direction"] == "R" or args["enter_direction"] == "L":
                    if centroid[0] > W//2:
                        to = TrackableObject(objectID, centroid, "R")
                    else:
                        to = TrackableObject(objectID, centroid, "L")
                else:
                    if centroid[1] > H//2:
                        to = TrackableObject(objectID, centroid, "D")
                    else:
                        to = TrackableObject(objectID, centroid, "U")

            else:
                if to.side == "R" and centroid[0] < W//2:
                    to.side = "L"
                    to.counted = True
                    if args["enter_direction"] == "L": 
                        client.count += 1  
                        print('person entered')
                        client.save()
                        
                    elif client.count > 0:
                        print('person exit')
                        client.count -= 1
                        client.save()
                elif to.side == "L" and centroid[0] > W//2:
                    to.side = "R"
                    to.counted = True
                    if args["enter_direction"] == "R": 
                        client.count += 1
                        print('person entered')
                        client.save()
                    elif client.count > 0:
                        print('person exit')
                        client.count -= 1
                        client.save()

                # elif args["enter_direction"] == "up" or args["enter_direction"] == "down" and not to.counted:
                # 	#print("current: {} side: {}".format(str(centroid[0]), to.side))
                # 	if to.side == "up" and centroid[1] > H//2:
                # 		to.side = "down"
                # 		to.counted = True
                # 		totalDown += 1
                # 	elif to.side == "down" and centroid[1] < H//2:
                # 		to.side = "up"
                # 		to.counted = True
                # 		totalUp += 1

            # store the trackable object in our dictionary
            trackableObjects[objectID] = to
        totalFrames += 1
        fps.update()
        time.sleep(0.025)

    # stop the timer and display FPS information
    fps.stop()
    print("[INFO] elapsed time: {:.2f}".format(fps.elapsed()))
    print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))

    vs.stop()
    print('Stopped tracking')
    client.tracking = False
    client.save()

    # close any open windows
    cv2.destroyAllWindows()
    return "[INFO] elapsed time: {:.2f}/n[INFO] approx. FPS: {:.2f}".format(fps.elapsed(), fps.fps())

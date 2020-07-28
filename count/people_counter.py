# USAGE
# To read and write back out to video:
# python people_counter.py --prototxt mobilenet_ssd/MobileNetSSD_deploy.prototxt \
#	--model mobilenet_ssd/MobileNetSSD_deploy.caffemodel --input videos/example_01.mp4 \
#	--output output/output_01.avi
#
# To read from webcam and write back out to disk:
# python people_counter.py --prototxt mobilenet_ssd/MobileNetSSD_deploy.prototxt \
#	--model mobilenet_ssd/MobileNetSSD_deploy.caffemodel \
#	--output output/webcam_output.avi

# import the necessary packages
from .people_tracking.pyimagesearch.centroidtracker import CentroidTracker
from .people_tracking.pyimagesearch.trackableobject import TrackableObject
from imutils.video import VideoStream
from imutils.video import FPS
from .models import Count
from .apps import ModelConfig
import numpy as np
import argparse
import imutils
import time
import dlib
import cv2
import threading

class PeopleCounter(threading.Thread):
	CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
		"bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
		"dog", "horse", "motorbike", "person", "pottedplant", "sheep",
		"sofa", "train", "tvmonitor"]
	def __init__(self, threadID, name, **args):
		threading.Thread.__init__(self)
		self.object = Count.objects.get(name=name)
		self.threadID = threadID
		self.name = name
		self.args = args
		# load our serialized model from disk
		print("[INFO] loading model into class...")
		self.net = ModelConfig.net

		# if a video path was not supplied, grab a reference to the webcam
		if self.args["input"] == None:
			print("[INFO] starting video stream...")
			self.vs = VideoStream(src=0).start()
			time.sleep(2.0)

		# otherwise, grab a reference to the ip camera
		else:
			print("[INFO] opening ip camera feed...")
			self.vs = VideoStream(self.args["input"]).start()
			time.sleep(2.0)

		if self.vs.read() is None:
			raise ValueError("The video stream is offline or invalid")
		
		self.object.tracking = True
		print('started tracking')
		self.object.save()

	def run(self):
		# writer = None
		W = None
		H = None

		ct = CentroidTracker(maxDisappeared=40, maxDistance=100)
		trackers = []
		trackableObjects = {}

		totalFrames = 0

		fps = FPS().start()
		while True:
			self.object.refresh_from_db()
			if not self.object.tracking:
				time.sleep(5)
				continue
			frame = self.vs.read()
			
			frame = imutils.resize(frame, width=500)
			rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

			if W is None or H is None:
				(H, W) = frame.shape[:2]

			# initialize the current status along with our list of bounding
			# box rectangles returned by either (1) our object detector or
			# (2) the correlation trackers
			status = "Waiting"
			rects = []

			# check to see if we should run a more computationally expensive
			# object detection method to aid our tracker
			if totalFrames % self.args["skip_frames"] == 0:
				# set the status and initialize our new set of object trackers
				status = "Detecting"
				trackers = []

				# convert the frame to a blob and pass the blob through the
				# network and obtain the detections
				blob = cv2.dnn.blobFromImage(frame, 0.007843, (W, H), 127.5)
				self.net.setInput(blob)
				detections = self.net.forward()

				# loop over the detections
				for i in np.arange(0, detections.shape[2]):
					# extract the confidence (i.e., probability) associated
					# with the prediction
					confidence = detections[0, 0, i, 2]

					# filter out weak detections by requiring a minimum
					# confidence
					if confidence > self.args["confidence"]:
						# extract the index of the class label from the
						# detections list
						idx = int(detections[0, 0, i, 1])

						# if the class label is not a person, ignore it
						if self.CLASSES[idx] != "person":
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
					if self.args["enter_direction"] == "R" or self.args["enter_direction"] == "L":
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
						if self.args["enter_direction"] == "L": 
							self.object.count += 1  
							print('person entered')
							self.object.save()
							
						elif self.object.count > 0:
							print('person exit')
							self.object.count -= 1
							self.object.save()
					elif to.side == "L" and centroid[0] > W//2:
						to.side = "R"
						to.counted = True
						if self.args["enter_direction"] == "R": 
							self.object.count += 1
							print('person entered')
							self.object.save()
						elif self.object.count > 0:
							print('person exit')
							self.object.count -= 1
							self.object.save()

					# elif self.args["enter_direction"] == "up" or self.args["enter_direction"] == "down" and not to.counted:
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

		self.vs.stop()
		print('Stopped tracking')
		self.object.tracking = False
		self.object.save()

		# close any open windows
		cv2.destroyAllWindows()

if __name__=="__main__":

	try:
		home_counter = PeopleCounter(threadID=1, name="home",prototxt='mobilenet_ssd/MobileNetSSD_deploy.prototxt', 
			model='mobilenet_ssd/MobileNetSSD_deploy.caffemodel', 
			input='http://admin:750801@98.199.131.202/videostream.cgi?rate=0', 
			output=None,
			confidence=0.4, 
			skip_frames=30, 
			direction="rightleft",
			enter_direction="R"
		)

		home_counter.start()
		# beach_counter.start()
	except AttributeError as e:
		print("Video stream is invalid or offline. ")
	except Exception as e:
		print("An unknown error occurred opening the video streams. ")
		print(e)

	while home_counter.is_alive():
		if home_counter.countChanged:
			print(home_counter.count)
			home_counter.countChanged = False
	
	print("Exiting main thread")
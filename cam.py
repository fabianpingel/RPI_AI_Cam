import cv2

cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
#cap.set(cv2.CAP_PROP_FRAME_WIDTH, 224)
#cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 224)
cap.set(cv2.CAP_PROP_FPS, 36)

# read frame
while True:
	ret, image = cap.read()
	if not ret:
		raise RuntimeError("failed to read frame")

	# convert opencv output from BGR to RGB
	image = image[:, :, [2, 1, 0]]
	
	# show the frame
	cv2.imshow("Frame", image)
	key = cv2.waitKey(1) & 0xFF
	
	# if the `q` key was pressed, break from the loop
	if key == ord("q"):
		break

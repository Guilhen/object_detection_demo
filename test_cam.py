import time
import cv2
#
camera = cv2.VideoCapture()
camera.open(0)
opened = camera.isOpened()
if not opened:
    print("Camera not open")
    exit

camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

while True:
    ret, frame = camera.read()
    print(frame)
    cv2.imshow("Camera", frame)

    if not ret:
        break

    k = cv2.waitKey(1)
    if k%256 == 27:
        print ("Done")
        break

camera.release()
cv2.destroyAllWindows()

# image = cv2.imread('test.jpg')
# while True:
#     cv2.imshow("Camera", image)
#     k = cv2.waitKey(1)
#     if k%256 == 27:
#         print ("Done")
#         break
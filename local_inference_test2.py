# -*- coding: utf-8 -*-
"""local_inference_test.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1DoufA_ZZTQ4Cbkrwxll2eoD-ek4rkO7B

## Run inference test
Test with images in repository `object_detection_demo/test` directory.
"""

import os
import glob

# Path to frozen detection graph. This is the actual model that is used for the object detection.
PATH_TO_CKPT = './models/frozen_inference_graph.pb'

# List of the strings that is used to add correct label for each box.
PATH_TO_LABELS = './models/label_map.pbtxt'

# If you want to test the code with your images, just add images files to the PATH_TO_TEST_IMAGES_DIR (./test).
PATH_TO_TEST_IMAGES_DIR = './test'

assert os.path.isfile(PATH_TO_CKPT)
assert os.path.isfile(PATH_TO_LABELS)
TEST_IMAGE_PATHS = glob.glob(os.path.join(PATH_TO_TEST_IMAGES_DIR, "*.*"))
assert len(TEST_IMAGE_PATHS) > 0, 'No image found in `{}`.'.format(PATH_TO_TEST_IMAGES_DIR)
print(TEST_IMAGE_PATHS)

# %cd /content/models/research/object_detection

import numpy as np
import os
import six.moves.urllib as urllib
import sys
import tarfile
import tensorflow as tf
import zipfile

from collections import defaultdict
from io import StringIO
from matplotlib import pyplot as plt
from PIL import Image

# This is needed since the notebook is stored in the object_detection folder.
sys.path.append("..")
from object_detection.utils import ops as utils_ops


# This is needed to display the images.
# %matplotlib inline


from object_detection.utils import label_map_util

from object_detection.utils import visualization_utils as vis_util

import visualization_utils as local_vis_util

NUM_CLASSES = 2

detection_graph = tf.Graph()
with detection_graph.as_default():
    od_graph_def = tf.GraphDef()
    with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
        serialized_graph = fid.read()
        od_graph_def.ParseFromString(serialized_graph)
        tf.import_graph_def(od_graph_def, name='')


label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
categories = label_map_util.convert_label_map_to_categories(
    label_map, max_num_classes=NUM_CLASSES, use_display_name=True)
category_index = label_map_util.create_category_index(categories)


def load_image_into_numpy_array(image):
    (im_width, im_height) = image.size
    return np.array(image.getdata()).reshape(
        (im_height, im_width, 3)).astype(np.uint8)


# Size, in inches, of the output images.
IMAGE_SIZE = (12, 8)


def run_inference_for_single_image(image, graph):
    with graph.as_default():
        with tf.Session() as sess:
            # Get handles to input and output tensors
            ops = tf.get_default_graph().get_operations()
            all_tensor_names = {
                output.name for op in ops for output in op.outputs}
            tensor_dict = {}
            for key in [
                'num_detections', 'detection_boxes', 'detection_scores',
                'detection_classes', 'detection_masks'
            ]:
                tensor_name = key + ':0'
                if tensor_name in all_tensor_names:
                    tensor_dict[key] = tf.get_default_graph().get_tensor_by_name(
                        tensor_name)
            if 'detection_masks' in tensor_dict:
                # The following processing is only for single image
                detection_boxes = tf.squeeze(
                    tensor_dict['detection_boxes'], [0])
                detection_masks = tf.squeeze(
                    tensor_dict['detection_masks'], [0])
                # Reframe is required to translate mask from box coordinates to image coordinates and fit the image size.
                real_num_detection = tf.cast(
                    tensor_dict['num_detections'][0], tf.int32)
                detection_boxes = tf.slice(detection_boxes, [0, 0], [
                                           real_num_detection, -1])
                detection_masks = tf.slice(detection_masks, [0, 0, 0], [
                                           real_num_detection, -1, -1])
                detection_masks_reframed = utils_ops.reframe_box_masks_to_image_masks(
                    detection_masks, detection_boxes, image.shape[0], image.shape[1])
                detection_masks_reframed = tf.cast(
                    tf.greater(detection_masks_reframed, 0.5), tf.uint8)
                # Follow the convention by adding back the batch dimension
                tensor_dict['detection_masks'] = tf.expand_dims(
                    detection_masks_reframed, 0)
            image_tensor = tf.get_default_graph().get_tensor_by_name('image_tensor:0')

            # Run inference
            output_dict = sess.run(tensor_dict,
                                   feed_dict={image_tensor: np.expand_dims(image, 0)})

            # all outputs are float32 numpy arrays, so convert types as appropriate
            output_dict['num_detections'] = int(
                output_dict['num_detections'][0])
            output_dict['detection_classes'] = output_dict[
                'detection_classes'][0].astype(np.uint8)
            output_dict['detection_boxes'] = output_dict['detection_boxes'][0]
            output_dict['detection_scores'] = output_dict['detection_scores'][0]
            if 'detection_masks' in output_dict:
                output_dict['detection_masks'] = output_dict['detection_masks'][0]
    return output_dict


i=1
import time

for image_path in TEST_IMAGE_PATHS:
    image = Image.open(image_path)
    # the array based representation of the image will be used later in order to prepare the
    # result image with boxes and labels on it.
    print('###############')

    image_np = load_image_into_numpy_array(image)


    # Expand dimensions since the model expects images to have shape: [1, None, None, 3]
    image_np_expanded = np.expand_dims(image_np, axis=0)

    print('the type should be:' + str(type(image_np)))
    print('the shape should be ' + str(image_np.shape))

    # Actual detection.
    start = time.time()
    output_dict = run_inference_for_single_image(image_np, detection_graph)
    end = time.time()
    print('the time is: ' +str(end - start))
    # Visualization of the results of a detection.

    print('the type should be:' + str(type(image_np)))
    print('the shape should be ' + str(image_np.shape))
    print(output_dict)

    vis_util.visualize_boxes_and_labels_on_image_array(
        image_np,
        output_dict['detection_boxes'],
        output_dict['detection_classes'],
        output_dict['detection_scores'],
        category_index,
        instance_masks=output_dict.get('detection_masks'),
        use_normalized_coordinates=True,
        line_thickness=8)

    plt.figure(figsize=IMAGE_SIZE)
    plt.imshow(image_np)
    plt.savefig('test' +str(i) +'.jpg')
    i+=1

"""### Benchmark TensorFlow inference speed"""

import time


def run_inference_benchmark(image, graph, trial=20, gpu=True):
    """Run TensorFlow inference benchmark.

    Arguments:
        image {np.array} -- Input image as an Numpy array.
        graph {tf.Graph} -- TensorFlow graph object.

    Keyword Arguments:
        trial {int} -- Number of inference to run for averaging. (default: {20})
        gpu {bool} -- Use Nvidia GPU when available. (default: {True})

    Returns:
        int -- Frame per seconds benchmark result.
    """

    with graph.as_default():
        if gpu:
            config = tf.ConfigProto()
        else:
            config = tf.ConfigProto(device_count={"GPU": 0})
        with tf.Session(config=config) as sess:
            # Get handles to input and output tensors
            ops = tf.get_default_graph().get_operations()
            all_tensor_names = {output.name for op in ops for output in op.outputs}
            tensor_dict = {}
            for key in [
                "num_detections",
                "detection_boxes",
                "detection_scores",
                "detection_classes",
                "detection_masks",
            ]:
                tensor_name = key + ":0"
                if tensor_name in all_tensor_names:
                    tensor_dict[key] = tf.get_default_graph().get_tensor_by_name(
                        tensor_name
                    )
            if "detection_masks" in tensor_dict:
                # The following processing is only for single image
                detection_boxes = tf.squeeze(tensor_dict["detection_boxes"], [0])
                detection_masks = tf.squeeze(tensor_dict["detection_masks"], [0])
                # Reframe is required to translate mask from box coordinates to image coordinates and fit the image size.
                real_num_detection = tf.cast(
                    tensor_dict["num_detections"][0], tf.int32
                )
                detection_boxes = tf.slice(
                    detection_boxes, [0, 0], [real_num_detection, -1]
                )
                detection_masks = tf.slice(
                    detection_masks, [0, 0, 0], [real_num_detection, -1, -1]
                )
                detection_masks_reframed = utils_ops.reframe_box_masks_to_image_masks(
                    detection_masks, detection_boxes, image.shape[0], image.shape[1]
                )
                detection_masks_reframed = tf.cast(
                    tf.greater(detection_masks_reframed, 0.5), tf.uint8
                )
                # Follow the convention by adding back the batch dimension
                tensor_dict["detection_masks"] = tf.expand_dims(
                    detection_masks_reframed, 0
                )
            image_tensor = tf.get_default_graph().get_tensor_by_name(
                "image_tensor:0"
            )

            # Run inference
            times = []
            # Kick start the first inference which takes longer and followings.
            output_dict = sess.run(
                tensor_dict, feed_dict={image_tensor: np.expand_dims(image, 0)}
            )

            # for i in range(trial):
            #     start_time = time.time()
            #     output_dict = sess.run(tensor_dict, feed_dict={image_tensor: np.expand_dims(image, 0)})

                # vis_util.visualize_boxes_and_labels_on_image_array(
                #     image,
                #     output_dict['detection_boxes'],
                #     output_dict['detection_classes'],
                #     output_dict['detection_scores'],
                #     category_index,
                #     instance_masks=output_dict.get('detection_masks'),
                #     use_normalized_coordinates=True,
                #     line_thickness=8)


                #print(output_dict['detection_boxes'][0])
                # delta = time.time() - start_time
                # times.append(delta)
            #mean_delta = np.array(times).mean()
            #fps = 1 / mean_delta
            #print("average(sec):{:.3f},fps:{:.2f}".format(mean_delta, fps))

    return(0, image)


def test():
    image = Image.open(TEST_IMAGE_PATHS[-1])
    # the array based representation of the image will be used later in order to prepare the
    # result image with boxes and labels on it.
    image_np = load_image_into_numpy_array(image)
    # Expand dimensions since the model expects images to have shape: [1, None, None, 3]
    image_np_expanded = np.expand_dims(image_np, axis=0)
    # Actual detection benchmark.
    fps = run_inference_benchmark(image_np, detection_graph, trial201, gpu=False)

def camera_test():

    import time
    import cv2

    camera = cv2.VideoCapture()
    time.sleep(1)
    camera.open(0)
    time.sleep(1)
    opened = camera.isOpened()
    time.sleep(1)

    if not opened:
        print("Camera not open")
        exit

    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920/4)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080/4)

    while True:
        ret, frame = camera.read()
        reduction = 2.5
        frame = cv2.resize(frame, (int(320/reduction), int(240/reduction)))

        print(type(frame))
        print(frame.shape)

        #
        # frame = frame.astype(np.uint8)
        #
        # print(type(frame))
        # print('shape test ')
        # print((frame.shape))
        # #print(frame)
        #
        # #(im_width, im_height) = frame.size
        #
        # #frame = np.array(frame.getdata()).reshape((im_height, im_width, 3)).astype(np.uint8)
        #
        #
        # # the array based representation of the image will be used later in order to prepare the
        # # result image with boxes and labels on it.
        # #image_np = load_image_into_numpy_array(frame)
        # image_np = frame
        # # Expand dimensions since the model expects images to have shape: [1, None, None, 3]
        # image_np_expanded = np.expand_dims(image_np, axis=0)
        # # Actual detection benchmark.
        fps,image_np = run_inference_benchmark(frame, detection_graph, trial=1, gpu=True)

        cv2.imshow("Camera", frame)

        if not ret:
            break

        k = cv2.waitKey(1)
        if k % 256 == 27:
            print("Done")
            break

    camera.release()
    cv2.destroyAllWindows()


def camera_test_speed():

    graph = detection_graph
    gpu = True

    with graph.as_default():
        if gpu:
            config = tf.ConfigProto()
        else:
            config = tf.ConfigProto(device_count={"GPU": 0})
        with tf.Session(config=config) as sess:
            # Get handles to input and output tensors
            ops = tf.get_default_graph().get_operations()
            all_tensor_names = {output.name for op in ops for output in op.outputs}
            tensor_dict = {}
            for key in [
                "num_detections",
                "detection_boxes",
                "detection_scores",
                "detection_classes",
                "detection_masks",
            ]:
                tensor_name = key + ":0"
                if tensor_name in all_tensor_names:
                    tensor_dict[key] = tf.get_default_graph().get_tensor_by_name(
                        tensor_name
                    )
            if "detection_masks" in tensor_dict:
                # The following processing is only for single image
                detection_boxes = tf.squeeze(tensor_dict["detection_boxes"], [0])
                detection_masks = tf.squeeze(tensor_dict["detection_masks"], [0])
                # Reframe is required to translate mask from box coordinates to image coordinates and fit the image size.
                real_num_detection = tf.cast(
                    tensor_dict["num_detections"][0], tf.int32
                )
                detection_boxes = tf.slice(
                    detection_boxes, [0, 0], [real_num_detection, -1]
                )
                detection_masks = tf.slice(
                    detection_masks, [0, 0, 0], [real_num_detection, -1, -1]
                )
                detection_masks_reframed = utils_ops.reframe_box_masks_to_image_masks(
                    detection_masks, detection_boxes, image.shape[0], image.shape[1]
                )
                detection_masks_reframed = tf.cast(
                    tf.greater(detection_masks_reframed, 0.5), tf.uint8
                )
                # Follow the convention by adding back the batch dimension
                tensor_dict["detection_masks"] = tf.expand_dims(
                    detection_masks_reframed, 0
                )
            image_tensor = tf.get_default_graph().get_tensor_by_name(
                "image_tensor:0"
            )

            import time
            import cv2

            cv2.namedWindow("preview")
            vc = cv2.VideoCapture(1)

            ret, frame = vc.read()

            while True:


                ret, frame = vc.read()


                reduction = 1.5
                frame = cv2.resize(frame, (int(320/reduction), int(240/reduction)))

                #print(type(frame))
                #print(frame.shape)

                output_dict = sess.run(tensor_dict, feed_dict={image_tensor: np.expand_dims(frame, 0)})

                # all outputs are float32 numpy arrays, so convert types as appropriate
                output_dict['num_detections'] = int(
                    output_dict['num_detections'][0])
                output_dict['detection_classes'] = output_dict[
                    'detection_classes'][0].astype(np.uint8)
                output_dict['detection_boxes'] = output_dict['detection_boxes'][0]
                output_dict['detection_scores'] = output_dict['detection_scores'][0]
                if 'detection_masks' in output_dict:
                    output_dict['detection_masks'] = output_dict['detection_masks'][0]





                # try:
                #
                image,dictionnary_of_label_and_coordinates = local_vis_util.visualize_boxes_and_labels_on_image_array(
                    frame,
                    output_dict['detection_boxes'],
                    output_dict['detection_classes'],
                    output_dict['detection_scores'],
                    category_index,
                    instance_masks=output_dict.get('detection_masks'),
                    min_score_thresh=.1,
                    use_normalized_coordinates=True,
                    max_boxes_to_draw=40,
                    line_thickness=8)
                # except:
                #     print('bite')
                #     pass

                print(dictionnary_of_label_and_coordinates)

                cv2.imshow("Camera", frame)

                if not ret:
                    break

                k = cv2.waitKey(1)
                if k % 256 == 27:
                    print("Done")
                    break

    camera.release()
    cv2.destroyAllWindows()


def test_camera():
    import time
    import cv2

    camera = cv2.VideoCapture()
    time.sleep(1)
    camera.open(0)
    time.sleep(1)
    opened = camera.isOpened()
    time.sleep(1)

    if not opened:
        print("Camera not open")
        exit

    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    while True:
        try:
            ret, frame = camera.read()
            cv2.imshow("Camera", frame)

        except Exception as e:
            print(e)

        if not ret:
            break

        k = cv2.waitKey(1)
        if k % 256 == 27:
            print("Done")
            break

    camera.release()
    cv2.destroyAllWindows()


def test2():
    import cv2

    cv2.namedWindow("preview")
    vc = cv2.VideoCapture(1)

    rval, frame = vc.read()

    while True:

        if frame is not None:
            cv2.imshow("preview", frame)
        rval, frame = vc.read()

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


#test2()
camera_test_speed()
#test_camera()

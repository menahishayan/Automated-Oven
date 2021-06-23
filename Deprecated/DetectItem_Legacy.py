import asyncio
import tensorflow as tf
import numpy as np
from google.protobuf import text_format
from protos import string_int_label_map_pb2
from picamera import PiCamera
from picamera.array import PiRGBArray
import concurrent.futures as cf

__version__ = '0.5.0'

class Detector:
    async def init(self, logging, labelsPath='/home/pi/ssd/saved_model/labels.pbtxt'):
        self.init_success = {
            'model': None,
            'labels': None,
            'camera': None
        }
        self.logging = logging
        await self.load_labels(labelsPath)
        await self.initCamera()
        return self

    async def exit(self):
        try:
            self.camera.stop_preview()
            self.camera.close()
        except Exception as e:
            self.logging.exception(e)

    async def success(self):
        try:
            if not self.init_success['model'] or not self.init_success['labels'] or not self.init_success['camera']:
                return False
            else:
                return True
        except Exception as e:
            self.logging.exception(e)

    async def get_status(self):
        return self.init_success

    async def load_model(self, savedModelDir='/home/pi/ssd/saved_model/saved_model/'):
        try:
            self.saved_model = tf.saved_model.load(savedModelDir)
            self.model = self.saved_model.signatures['serving_default']
            self.logging.info("Model Loaded")
            self.init_success['model'] = True
        except:
            self.init_success['model'] = False

    async def load_labels(self, labelsPath):
        try:
            labels_path = labelsPath
            labels_file = open(labels_path, 'r')
            labels_string = labels_file.read()

            labels_map = string_int_label_map_pb2.StringIntLabelMap()
            try:
                text_format.Merge(labels_string, labels_map)
            except text_format.ParseError:
                labels_map.ParseFromString(labels_string)

            labels_dict = {}
            for item in labels_map.item:
                labels_dict[item.id] = item.name

            self.labels = labels_dict
            self.logging.info("Labels Loaded")
            if self.labels:
                self.init_success['labels'] = True
            else:
                self.init_success['labels'] = False
        except Exception as e:
            self.init_success['labels'] = False
            self.logging.exception(e)

    async def initCamera(self):
        try:
            self.camera = PiCamera()
            self.camera.resolution = (640, 480)
            self.camera.rotation = 180
            self.rawCapture = PiRGBArray(self.camera, size=(640, 480))

            self.logging.info("Camera Loaded")

            self.init_success['camera'] = True
        except Exception as e:
            self.init_success['camera'] = False
            self.logging.exception(e)

    def restartCamera(self):
        self.camera.stop_preview()
        self.camera.close()

        self.camera = PiCamera()
        self.camera.resolution = (640, 480)
        self.camera.rotation = 180
        self.rawCapture = PiRGBArray(self.camera, size=(640, 480))

    def detectionHandler(self, image_arg):
        self.logging.info("DetectionHandler Called")
        image = np.asarray(image_arg)
        input_tensor = tf.convert_to_tensor(image)
        input_tensor = input_tensor[tf.newaxis, ...]

        saved_model = self.saved_model
        model = self.model
        output_dict = model(input_tensor)

        num_detections = int(output_dict['num_detections'])
        output_dict = {
            key: value[0, :num_detections].numpy()
            for key, value in output_dict.items()
            if key != 'num_detections'
        }
        output_dict['num_detections'] = num_detections
        output_dict['detection_classes'] = output_dict['detection_classes'].astype(
            np.int64)

        return output_dict

    async def captureFrames(self, maxFrames=4):
        await asyncio.sleep(3)
        images = []
        for frame in self.camera.capture_continuous(self.rawCapture, format="rgb",
                                                        use_video_port=True):

            self.rawCapture.truncate(0)
            await asyncio.sleep(0.15)
            images.append(frame.array)
            if len(images) == maxFrames:
                break
        self.logging.info("{} Images captured".format(len(images)))
        return await self.detectionDispatcher(images)

    def detectionWorker(self,image):
        detections = self.detectionHandler(image)
        num_detections = detections['num_detections']
        if num_detections > 0:
            for detection_index in range(num_detections):
                detection_score = detections['detection_scores'][detection_index]
                detection_class = detections['detection_classes'][detection_index]
                detection_label = self.labels[detection_class]
                if detection_score > 0.6:
                    return {
                        int(detection_score*100): detection_label
                    }
        return {
            0: "None"
        }

    async def detectionDispatcher(self,images):
        res = {}
        arrayOfFutures = []
        with cf.ThreadPoolExecutor(max_workers=2) as executor:
            loop = asyncio.get_running_loop()
            arrayOfFutures = [loop.run_in_executor(executor, self.detectionWorker, i) for i in images]
            # arrayOfFutures.append(loop.run_in_executor(executor, detectionWorker, i))

            await asyncio.gather(*arrayOfFutures)

            for f in arrayOfFutures:
                res.update(f.result())

            maxRes = res[max(res)]
            self.logging.info(maxRes)

            return maxRes
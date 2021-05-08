from os import environ
environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import asyncio
from PIL import Image
from tensorflow.keras.models import model_from_json
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow import expand_dims
from tensorflow.nn import softmax
import numpy as np
from picamera import PiCamera
import concurrent.futures as cf
from io import BytesIO

__version__ = '0.7.0'

class Detector:
    async def init(self, e):
        self.model_loaded = False
        self.e = e
        await self.initCamera()
        return self

    async def exit(self):
        try:
            self.camera.stop_preview()
            self.camera.close()
        except Exception as e:
            self.e.err(e)

    async def get_status(self):
        return self.model_loaded

    async def load_model(self, model_path='/home/pi/keras1/models/v3.6/model-v3.6'):
        try:
            json_file = open('{}.json'.format(model_path), 'r')
            loaded_model_json = json_file.read()
            json_file.close()
            loaded_model = model_from_json(loaded_model_json)
            loaded_model.load_weights("{}.h5".format(model_path))

            self.model = loaded_model
            self.e.log("Model Loaded")
            self.model_loaded = True
        except:
            self.model_loaded = False

    async def initCamera(self):
        try:
            self.camera = PiCamera()
            self.camera.resolution = (640, 480)
            self.camera.rotation = 180
            self.e.log("Camera Loaded")

        except Exception as e:
            self.e.err(e)

    def restartCamera(self):
        self.camera.stop_preview()
        self.camera.close()

        self.camera = PiCamera()
        self.camera.resolution = (640, 480)
        self.camera.rotation = 180

    async def detect(self, maxFrames=4):
        stream = [BytesIO() for i in range(maxFrames)]

        for i in range(maxFrames):
            self.camera.capture(stream[i], format='jpeg', resize=(250,250))
            stream[i].seek(0)
            await asyncio.sleep(0.15)
            
        return await self.detectionDispatcher(stream)

    def detectionWorker(self,image):
        class_names = ['Bread','Burger','Cake', 'Chicken', 'Coffee', 'Cookie', 'Croissant', 'Fish', 'Fries', 'Omelette','Pasta', 'Pie', 'Pizza', 'Rice', 'Sandwiches', 'Toast']
        tf_image = img_to_array(image)
        tf_image = expand_dims(tf_image, 0)
       
        predictions = self.model.predict(tf_image)
        score = softmax(predictions[0])
        detection_score = np.max(score)
        detection_label = class_names[np.argmax(score)]
        
        if detection_label == 'fish' and int(detection_score*10000) < 1550:
            return {
                0: "None"
            }
        return {
                int(detection_score*10000): detection_label
            }

    async def detectionDispatcher(self,streams):
        res = {}
        arrayOfFutures = []
        with cf.ThreadPoolExecutor(max_workers=2) as executor:
            loop = asyncio.get_running_loop()
            arrayOfFutures = [loop.run_in_executor(executor, self.detectionWorker, Image.open(s)) for s in streams]

            await asyncio.gather(*arrayOfFutures)

            for f in arrayOfFutures:
                res.update(f.result())

            maxRes = res[max(res)]
            # self.e.log(res)
            # self.e.log(maxRes)

            return maxRes
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
from json import loads

class Detector:
    async def init(self, e):
        self.model_loaded = False
        self.e = e
        self.labels = []
        await self.initCamera()
        self.modelVersion = await self.e.config.get('modelVersion')
        return self

    async def exit(self):
        try:
            self.camera.stop_preview()
            self.camera.close()
        except Exception as e:
            self.e.err(e)

    async def load_model(self):
        try:
            self.modelVersion = await self.e.config.get('modelVersion')
            model_path = '/home/pi/keras/models/{}/model-{}'.format(self.modelVersion,self.modelVersion)

            model_json = {}
            with open('{}.json'.format(model_path)) as j:
                model_json = j.read()

            with open('{}.txt'.format(model_path)) as l:
                self.labels = l.read().splitlines() 
            
            model = model_from_json(model_json)

            model_json = loads(model_json)

            batch_input_shape = model_json['config']['layers'][0]['config']['batch_input_shape']
            self.input_shape = [batch_input_shape[1],batch_input_shape[2]]

            if model_json['class_name'] == 'Sequential':
                model(np.zeros((1,self.input_shape[0],self.input_shape[1],3)))

            model.load_weights("{}.h5".format(model_path))

            self.model = model
            self.e.log("Boot: Model Loaded")
            self.model_loaded = True
        except Exception as e:
            self.e.err(e)
            self.model_loaded = False

    async def initCamera(self):
        try:
            self.camera = PiCamera()
            self.camera.resolution = (640, 480)
            self.camera.rotation = 180
            self.e.log("Boot: Camera Loaded")

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
            self.camera.capture(stream[i], format='jpeg', resize=(self.input_shape[0],self.input_shape[1]))
            stream[i].seek(0)
            await asyncio.sleep(0.15)
            
        return await self.detectionDispatcher(stream)

    def detectionWorker(self,image):
        tf_image = img_to_array(image)
        tf_image = expand_dims(tf_image, 0)
       
        predictions = self.model.predict(tf_image)
        score = softmax(predictions[0])
        detection_score = np.max(score)
        detection_label = self.labels[np.argmax(score)]
        
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
            self.e.log(res)
            self.e.log(maxRes)

            return maxRes
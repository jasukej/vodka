"""
The `Model` class is an interface between the ML model that you're packaging and the model
server that you're running it on.

The main methods to implement here are:
* `load`: runs exactly once when the model server is spun up or patched and loads the
   model onto the model server. Include any logic for initializing your model, such
   as downloading model weights and loading the model into memory.
* `predict`: runs every time the model server is called. Include any logic for model
  inference and return the model output.

See https://truss.baseten.co/quickstart for more.
"""

from ultralytics import YOLO
import base64
import io
from PIL import Image

class Model:
    def __init__(self, **kwargs):
        self._model = None
    
    def load(self):
        # This path is where Baseten looks for model files
        self._model = YOLO('model/drumsticks/data/best.pt')
        print("Drumstick detector loaded")
    
    def predict(self, model_input):
        """
        Expected input:
        {
            "image": "base64_encoded_image_string",
            "conf": 0.25  # optional confidence threshold
        }
        """
        try:
            # Decode base64 image
            img_data = base64.b64decode(model_input['image'])
            img = Image.open(io.BytesIO(img_data))
            
            # Get confidence threshold
            conf = model_input.get('conf', 0.25)
            
            # Run inference
            results = self._model(img, conf=conf)
            
            # Format detections
            detections = []
            for result in results:
                for box in result.boxes:
                    detections.append({
                        'class': result.names[int(box.cls)],
                        'confidence': float(box.conf),
                        'bbox': box.xyxy[0].tolist(),  # [x1, y1, x2, y2]
                    })
            
            return {
                'detections': detections,
                'count': len(detections),
                'image_size': [img.width, img.height]
            }
            
        except Exception as e:
            return {'error': str(e)}

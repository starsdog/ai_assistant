from openai import OpenAI
import json
from dotenv import load_dotenv 
import os
from base64 import b64decode


class ImageAssistant:
    def __init__(self):
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + os.environ['OPENAI_API_KEY'],
        }
        self.client = OpenAI()
        
    def image_generation(self, instruction, model="dall-e-2", number = 1):
        response = self.client.images.generate(
            prompt=instruction,
            n=1,
            size="256x256",
            response_format="b64_json")
        return response

    def image_variation(self, base_image, model="dall-e-2", number = 1):
        with open(base_image, mode="rb") as file:
            image_data = file.read()
        
        response = self.client.images.create_variation(
            image=image_data,
            n=1,
            size="256x256",
            response_format="b64_json")
        return response

    def similar_image_generation(self, instruction, base_image, mask_image, model="dall-e-3", number = 1):
        with open(base_image, mode="rb") as file:
            image_data = file.read()
        with open(mask_image, mode="rb") as file:
            mask_data = file.read()
        
        response = self.client.images.edit(
            prompt=instruction,
            image=image_data,
            mask=mask_data,
            n=1,
            size="256x256",
            response_format="b64_json")
        
        return response

if __name__ == "__main__":
    project_dir = os.path.dirname(os.path.abspath(__file__))
    assistant = ImageAssistant()
   
    # generate image
    print("generate image...")
    prompt = "a cute cartoon beaver"
    response = assistant.image_generation(prompt)
    image_file = os.path.join(project_dir, "test.png")
    with open(image_file, "wb") as file:
        file.write(b64decode(response.data[0].b64_json))
    
    # generate variation
    print("generate image variation...")
    base_image = os.path.join(project_dir, "test.png")
    response = assistant.image_variation(base_image)
    image_file = os.path.join(project_dir, "test_variation.png")
    with open(image_file, "wb") as file:
        file.write(b64decode(response.data[0].b64_json))

    # generate similar
    print("generate edit image...")
    prompt = "a cute cartoon beaver, wearing coat" 
    base_image = os.path.join(project_dir, "test.png")
    mask_image = os.path.join(project_dir, "test_mask.png")
    response = assistant.similar_image_generation(prompt, base_image, mask_image)
    image_file = os.path.join(project_dir, "test_similar.png")
    with open(image_file, "wb") as file:
        file.write(b64decode(response.data[0].b64_json))

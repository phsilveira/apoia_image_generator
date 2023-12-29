import boto3
from PIL import Image
import os
import requests
import re
import settings
import json
from io import BytesIO
import pickle


def upload_image_in_memory_to_s3(image_bytes_io, object_name):
    bucket_name = 'apoia-cdn'
    BASE_URL = 'https://apoia-cdn.s3.sa-east-1.amazonaws.com/'

    # Initialize S3 client
    s3_client = boto3.client('s3',
        aws_access_key_id = settings.aws_access_key_id,
        aws_secret_access_key = settings.aws_secret_access_key,
    )

    try:
        # Upload image from BytesIO to S3
        image_bytes_io.seek(0)  # Ensure the cursor is at the beginning of the BytesIO object
        s3_client.upload_fileobj(image_bytes_io, bucket_name, object_name)
        print(f"File uploaded successfully to {bucket_name}/{object_name}")
        return f'{BASE_URL}{object_name}'
    except Exception as e:
        print(f"Error uploading file: {e}")
        return None

def fetch_image(task_id):
    endpoint = "https://api.midjourneyapi.xyz/mj/v2/fetch"

    data = {
        "task_id": task_id
    }

    response = requests.post(endpoint, json=data)

    # print(response.status_code)
    # print(json.dumps(response.json(), indent=4))
    return response.json()

def get_imagine_request(prompt):


    X_API_KEY = settings.X_API_KEY
    endpoint = "https://api.midjourneyapi.xyz/mj/v2/imagine"

    headers = {
        "X-API-KEY": X_API_KEY
    }

    data = {
        "process_mode": "fast",
        "prompt": prompt,
        "aspect_ratio": "16:9",
        "process_mode": "mixed",
        "webhook_endpoint": "",
        "webhook_secret": ""
    }

    response = requests.post(endpoint, headers=headers, json=data)

    # print(response.status_code)
    # print(response.json())

    return response.json()


def crop_and_save_quadrants(image_path, output_folder):
    try:
        file_name = image_path.split('/')[-1].split('.png')[0]

        image = Image.open(image_path)
        width, height = image.size
        quadrant_width = width // 2
        quadrant_height = height // 2

        croped_image_list = []
        for i in range(2):
            for j in range(2):
                left = j * quadrant_width
                upper = i * quadrant_height
                right = left + quadrant_width
                lower = upper + quadrant_height

                quadrant = image.crop((left, upper, right, lower))
                quadrant.save(f"{output_folder}/{file_name}_{i+1}_{j+1}.jpg")

                croped_image_list.append(f"{output_folder}/{file_name}_{i+1}_{j+1}.jpg")

        return croped_image_list
        print("Quadrants cropped and saved successfully.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return []

def download_image_in_memory(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            print("Image downloaded successfully.")
            return image
        else:
            print("Failed to download the image.")
            return None
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None

def crop_quadrants_in_memory(image):
    try:
        width, height = image.size
        quadrant_width = width // 2
        quadrant_height = height // 2

        croped_image_list = []
        for i in range(2):
            for j in range(2):
                left = j * quadrant_width
                upper = i * quadrant_height
                right = left + quadrant_width
                lower = upper + quadrant_height

                quadrant = image.crop((left, upper, right, lower))

                # You can store the cropped images in a list of BytesIO objects
                cropped_image_buffer = BytesIO()
                quadrant.save(cropped_image_buffer, format="JPEG")
                cropped_image_buffer.seek(0)
                croped_image_list.append(cropped_image_buffer)

        print("Quadrants cropped successfully.")
        return croped_image_list
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return []

def slugify(text):
    """
    Convert a string to a slug format suitable for URLs.

    Parameters:
    text (str): The input string to slugify.

    Returns:
    str: The slugified string.
    """
    # Convert accented characters to non-accented equivalents
    text = unidecode(text)

    # Convert the string to lowercase and replace spaces with hyphens
    slug = text.lower().replace(" ", "-")

    # Remove special characters and keep only alphanumeric and hyphen
    slug = re.sub(r"[^\w\-]", "", slug)

    # Remove multiple hyphens and trailing hyphens
    slug = re.sub(r"\-+", "-", slug).strip("-")

    return slug
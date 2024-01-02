import streamlit as st
import openai
from PIL import Image
import requests
import time
from io import BytesIO
import promptlayer
import settings
from utils import (get_imagine_request, 
                   fetch_image, 
                   download_image_in_memory,
                   crop_quadrants_in_memory,
                   upload_image_in_memory_to_s3,)

promptlayer.api_key = settings.PROMPTLAYER

def open_image_from_url(url):
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    return img

def generate_image(image_sugestion: str) -> str:
    response = get_imagine_request(image_sugestion)

    fetch_response = fetch_image(response['task_id'])
    print(fetch_response)
    while fetch_response['status'] != 'finished':
        print('waiting 20s...')
        time.sleep(20)
        fetch_response = fetch_image(response['task_id'])
        print(fetch_response)

        if fetch_response['status'] == 'failed':
            print(fetch_response)
            return None

    image_url = fetch_response['task_result']['image_url']
    task_id = response['task_id']
    file_name =  f'{task_id}.png'
    downloaded_image = download_image_in_memory(image_url)
    if downloaded_image:
        cropped_images = crop_quadrants_in_memory(downloaded_image)

    object_name = f'image_generator/{file_name}'
    image_url = upload_image_in_memory_to_s3(cropped_images[0], object_name)
    return image_url

def suggest_course_image(image_suggestion, prompt_for_image_improvement):
    image_scene_prompt = prompt_for_image_improvement.format(**{'image_suggestion': image_suggestion})

    completion = openai.ChatCompletion.create(
      model="gpt-3.5-turbo",
      messages=[
        {"role": "user", "content": image_scene_prompt}
      ]
    )

    print(completion.choices[0].message.content)
    return completion.choices[0].message.content

def get_image_improvement_template():
    template_dict = promptlayer.prompts.get('image_improvement')
    return template_dict['template']

def get_image_improvement_english_template():
    template_dict = promptlayer.prompts.get('image_improvement_english')
    return template_dict['template']

def get_midjourney_template():
    template_dict = promptlayer.prompts.get('midjourney')
    return template_dict['template']

def main():
    st.title("Apoia Image Generator")
    st.write("This app generates images for Apoia's courses using custom prompt and midjourney engine.")

    image_suggestion = st.text_input('Enter Image Suggestion (ex: Course name):', 'Análise de crédito para empresas de médio porte')

    midjourney = st.text_area('Enter Midjourney prompt:', get_midjourney_template())

    prompt_for_image_improvement = st.text_area('Prompt for Image Improvement:', get_image_improvement_template())
    prompt_for_image_improvement_english = st.text_area('(For English) Prompt for Image Improvement:', get_image_improvement_english_template())

    use_english_prompt = st.checkbox('Use English Prompt', value=False)

    if st.button('Generate Image'):
        with st.spinner("Loading..."):
            if use_english_prompt:
                image_suggestion = suggest_course_image(image_suggestion, prompt_for_image_improvement_english)
            else:
                image_suggestion = suggest_course_image(image_suggestion, prompt_for_image_improvement)
            
            image_scene_prompt = midjourney.format(**{'original_prompt': image_suggestion})
            
            image_url = generate_image(image_scene_prompt)
            if image_url:
                st.success(f'Image generated successfully. at {image_url}')
                try:
                    # Open image from URL
                    img = open_image_from_url(image_url)
                    
                    # Display image
                    st.image(img, caption=image_scene_prompt, use_column_width=True)
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.error('Failed to generate image.')


if __name__ == '__main__':
    main()

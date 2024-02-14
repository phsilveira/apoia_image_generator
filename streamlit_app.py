import json
import streamlit as st
import openai
import hmac
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


def open_image_from_url(image_url):
    response = requests.get(image_url, stream=True)
    response.raise_for_status()
    return Image.open(response.raw)

def generate_image(image_sugestion: str, aspect_ratio: str = "16:9") -> str:
    response = get_imagine_request(image_sugestion, aspect_ratio)

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

    object_name = f'text_to_image_generator/{file_name}'
    image_url = upload_image_in_memory_to_s3(cropped_images[0], object_name)
    print(image_url)
    return image_url

def chatgpt_chat_completion_with_prompt(payload, prompt_template, model="gpt-3.5-turbo"):
    prompt = prompt_template.format(**payload)

    completion = openai.ChatCompletion.create(
      model=model,
      messages=[
        {"role": "user", "content": prompt}
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

def get_prompt_template_teacher_introduction_talk_show():
    template_dict = promptlayer.prompts.get('prompt_template_teacher_introduction_talk_show')
    return template_dict['template']

def get_script_template_teacher_introduction_talk_show():
    with open('script_templates/script_template_teacher_introduction_talk_show.txt', 'r') as file:
        script_template = file.read()
    return script_template

def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password.
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False

def text_to_image_generator():
    st.write("Text to Avatar Generator using Heygen API")
    image_suggestion = st.text_input('Enter Image Suggestion (ex: Course name):', 'Análise de crédito para empresas de médio porte')
    # original_image_url = st.text_input('Enter Original Image URL:', )
    # print(original_image_url)
    # if original_image_url:
    #     original_img = open_image_from_url(original_image_url)
        
    #     # Display image
    #     st.image(original_img, caption=original_image_url, use_column_width=True)

    midjourney = st.text_area('Enter Midjourney prompt:', get_midjourney_template())

    prompt_for_image_improvement = st.text_area('Prompt for Image Improvement:', get_image_improvement_template())
    prompt_for_image_improvement_english = st.text_area('(For English) Prompt for Image Improvement:', get_image_improvement_english_template())

    use_english_prompt = st.checkbox('Use English Prompt', value=False)

    if st.button('Generate Image'):
        with st.spinner("Loading..."):
            if use_english_prompt:
                image_suggestion = chatgpt_chat_completion_with_prompt({'image_suggestion': image_suggestion}, prompt_for_image_improvement_english, model=st.session_state.get("model_option", 'gpt-3.5-turbo'))
            else:
                image_suggestion = chatgpt_chat_completion_with_prompt({'image_suggestion': image_suggestion}, prompt_for_image_improvement, model=st.session_state.get("model_option", 'gpt-3.5-turbo'))
            
            image_scene_prompt = midjourney.format(**{'original_prompt': image_suggestion})
            
            image_url = generate_image(image_scene_prompt, aspect_ratio=st.session_state.get("aspect_ratio_option", '16:9'))
            if image_url:
                st.success(f'Image generated successfully. at {image_url}')
                try:
                    img = open_image_from_url(image_url)
                    
                    st.image(img, caption=image_scene_prompt, use_column_width=True)
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.error('Failed to generate image.')
        
        
        # if original_image_url:
        #     if st.button('change original image'):
        #         with st.spinner("Loading..."):
        #             try:
        #                 upload_image_in_memory_to_s3(img, original_image_url.split('amazonaws.com/')[-1])
        #                 # Display image
        #                 st.success('Image changed successfully.')
        #             except Exception as e:
        #                 st.error(f"Error: {e}")

def text_to_speech_generator():
    st.write("Text to Speech Generator using ElevenLabs API")

    CHUNK_SIZE = 1024
    voice_id = '21m00Tcm4TlvDq8ikWAM'
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
      "Accept": "audio/mpeg",
      "Content-Type": "application/json",
      "xi-api-key": st.secrets["xi_api_key"]  # replace with your method to get the API key
    }

    text = st.text_area("Enter text:", """Born and raised in the charming south, I can add a touch of sweet southern hospitality to your audiobooks and podcasts""")
    stability = st.slider("Stability:", min_value=0.0, max_value=1.0, value=0.5)
    similarity_boost = st.slider("Similarity Boost:", min_value=0.0, max_value=1.0, value=0.5)

    data = {
      "text": text,
      "model_id": "eleven_monolingual_v1",
      "voice_settings": {
        "stability": stability,
        "similarity_boost": similarity_boost
      }
    }

    if st.button('Generate Speech'):
        response = requests.post(url, json=data, headers=headers)
        audio_file_path = 'output.mp3'
        with open(audio_file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    f.write(chunk)

        st.audio(audio_file_path, format='audio/mp3')

def send_to_generate_avatar_heygen(text):
    headers = {
        'X-Api-Key': st.secrets["HEYGEN_API_KEY"],  # replace with your method to get the API key
        'Content-Type': 'application/json',
    }

    json_data = {
        'background': '#012A4A',
        'clips': [
            {
                'avatar_id': 'Andrew_public_pro4_20230614',
                'avatar_style': 'normal',
                'input_text': text,
                'offset': {
                    'x': 0,
                    'y': 0,
                },
                'scale': 1,
                'voice_id': 'e9a57ec649c8e7db9d8104529374b2c3',
            },
        ],
        'ratio': '16:9',
        'test': False,
        'version': 'v1alpha',
    }

    result = requests.post('https://api.heygen.com/v1/video.generate', headers=headers, json=json_data)
    return result.status_code, result.json()

def get_generated_avatar_heygen(video_id):
    headers = {
        'X-Api-Key': st.secrets["HEYGEN_API_KEY"],  # replace with your method to get the API key
    }

    params = {
        'video_id': video_id,
    }

    response = requests.get('https://api.heygen.com/v1/video_status.get', params=params, headers=headers)
    return response.status_code, response.json()

def text_to_avatar_generator():
    st.write("Text to Avatar Generator using Heygen API")

    narration = st.text_area("Enter narration:", 'Oi, aqui é o Paulo')

    if st.button('Generate Avatar'):
        with st.spinner("Loading..."):
            result = send_to_generate_avatar_heygen(narration)
            video_id = result[1]['data']['video_id'] # "video_id"

            result = get_generated_avatar_heygen(video_id)

            while result[1]['data']['status'] != 'completed':
                time.sleep(10)
                result = get_generated_avatar_heygen(video_id)

            video_url = result[1]['data']['video_url']
            st.video(video_url)

def script_generator():
    st.write("Script Generator")

    templates = {
        "Template 1.1.4": "This is the text for template 1.",
        "Template 1.2.2": "This is the text for template 2.",
        "Template 1.5.2": "This is the text for template 2."
    }

    selected_template = st.selectbox("Select a template:", list(templates.keys()))
    course_name = st.text_input('Course Name:', 'Gestão de Projetos')
    student_name = st.text_input('Student Name:', 'João')
    professor_name = st.text_input('professor_name', 'Paulo')

    with st.expander("Show/Hide More Options"):
        professor_area = st.text_input('professor_area', 'Tech')
        professor_academic_background = st.text_input('professor_academic_background', 'Master in computer science')
        professor_achievements = st.text_input('professor_achievements', 'Published 3 books, 10 years of experience, 5 years of experience in the industry')
        professor_domain_traits_from_spreadsheet = st.text_input('professor_domain_traits_from_spreadsheet', )
        professor_general_disposition_from_spreadsheet = st.text_input('professor_general_disposition_from_spreadsheet')
        professor_hobbies = st.text_input('professor_hobbies', 'reading, playing guitar')
        professor_personality_type_from_spreadsheet = st.text_input('professor_personality_type_from_spreadsheet', 'Introvert, Intuitive, Thinking, Judging')
        professor_professional_background = st.text_input('professor_professional_background', '10 years of experience in the STARTUP industry')

        script_template = st.text_area('Script template:', get_script_template_teacher_introduction_talk_show())
        prompt_template = st.text_area('Prompt template:', get_prompt_template_teacher_introduction_talk_show())


    if st.button('Generate script'):
        with st.spinner("Loading..."):
            payload = {
                'course_name': course_name,
                'student_name': student_name,
                'professor_name': professor_name,
                'professor_area': professor_area,
                'professor_academic_background': professor_academic_background,
                'professor_achievements': professor_achievements,
                'professor_domain_traits_from_spreadsheet': professor_domain_traits_from_spreadsheet,
                'professor_general_disposition_from_spreadsheet': professor_general_disposition_from_spreadsheet,
                'professor_hobbies': professor_hobbies,
                'professor_personality_type_from_spreadsheet': professor_personality_type_from_spreadsheet,
                'professor_professional_background': professor_professional_background,
            }
            answer = chatgpt_chat_completion_with_prompt(payload, prompt_template, model=st.session_state.get("model_option", 'gpt-3.5-turbo'))

            payload['answer'] = answer

            script = script_template.format(**payload)
            st.success(script)
            # try:
            #     answer_dict = json.loads(answer)
            # except Exception as e:
            #     st.error(f"Error: {e}")


def main():
    st.title("Apoia Video Engine - Toolbox")
    st.write("This app is a toolbox to help the video production.")

    # Sidebar
    if not check_password():
        st.stop()  # Do not continue if check_password is not True.

    st.sidebar.title("Navigation")
    selection = st.sidebar.radio("Go to", [
        "Text to Image Generator (Midjourney non official API)",
        "Text to Speech Generator (ElevenLabs API)",
        "Text to Avatar Generator (Heygen API)",
        "Script Generator",
    ])

    if selection == "Text to Image Generator (Midjourney non official API)":
        text_to_image_generator()
    elif selection == "Text to Speech Generator (ElevenLabs API)":
        text_to_speech_generator()
    elif selection == "Text to Avatar Generator (Heygen API)":
        text_to_avatar_generator()
    elif selection == "Script Generator":
        script_generator()

    st.sidebar.header('Settings')
    st.session_state["model_option"] = st.sidebar.selectbox('LLM Model', ['gpt-3.5-turbo', 'gpt-4',])
    st.session_state["aspect_ratio_option"] = st.sidebar.selectbox('Aspect Ratio', ['16:9', '9:16', ])



if __name__ == '__main__':
    main()

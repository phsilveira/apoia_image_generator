import io
import json
import streamlit as st
import openai
import hmac
from PIL import Image
import requests
import time
from templates import chatgpt_chat_completion_with_prompt, get_image_improvement_english_template, get_image_improvement_template, get_midjourney_template
from utils import (fetch_narration_in_memory, generate_avatar_heygen_with_audio_file, get_generated_avatar_heygen, get_imagine_request, 
                   fetch_image, 
                   download_image_in_memory,
                   crop_quadrants_in_memory, send_to_generate_avatar_heygen,
                   upload_object_in_memory_to_s3,
                   generate_image)


def open_image_from_url(image_url):
    response = requests.get(image_url, stream=True)
    response.raise_for_status()
    return Image.open(response.raw)

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

    aspect_ratio_option = st.selectbox('Aspect Ratio', ['16:9', '9:16', ])

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
            
            image_url = generate_image(image_scene_prompt, aspect_ratio=st.session_state.get(aspect_ratio_option, '16:9'))
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

    voices = {
        'Rachel': {
            'model_id': 'eleven_monolingual_v1',
            'voice_id': '21m00Tcm4TlvDq8ikWAM'
        },
        'Rangel Barbosa 02':{
            "voice_id": "rVYXh5OmQcvchhNYtBWe",
            "model_id": "eleven_multilingual_v2",
        }
    }
    
    selected_voice = st.selectbox("Select a voice:", ['Rangel Barbosa 02', 'Rachel'])
    text = st.text_area("Enter text:", """Alcançe seus objetivos na medida""")
    stability = st.slider("Stability:", min_value=0.0, max_value=1.0, value=0.5)
    similarity_boost = st.slider("Similarity Boost:", min_value=0.0, max_value=1.0, value=0.5)
    style = st.slider("Style:", min_value=0.0, max_value=1.0, value=0.2)

    if st.button('Generate Speech'):
        voice_id = voices[selected_voice]['voice_id']
        model_id = voices[selected_voice]['model_id']

        audio_data = fetch_narration_in_memory(text, voice_id, stability, similarity_boost, style, model_id)
        
        audio_data.seek(0)
        st.audio(audio_data.read(), format='audio/mp3')

        audio_data.seek(0)
        st.download_button(
            label="Download audio file",
            data=audio_data.read(),
            file_name="audio.mp3",
            mime="audio/mpeg"
        )

def text_to_avatar_generator():
    st.write("Text to Avatar Generator using Heygen API")

    selected_avatar = st.selectbox("Select a voice:", ['Rangel Barbosa', ])
    # narration = st.text_area("Enter narration:", 'Oi, aqui é o Paulo')
    uploaded_file = st.file_uploader("Upload MP3 file", type=['mp3'])
    test = st.checkbox('Test', value=False)

    if st.button('Generate Avatar'):
        with st.spinner("Loading..."):
            result = None
            if uploaded_file is not None:
                file_bytes = uploaded_file.read()
                uploaded_file_io = io.BytesIO(file_bytes)
                audio_url = upload_object_in_memory_to_s3(uploaded_file_io, 'audio/narration.mp3')

                if audio_url:
                    result = generate_avatar_heygen_with_audio_file(audio_url=audio_url, is_teste=test)
            
            # else:
            #     result = send_to_generate_avatar_heygen(narration, test=test)

            if not result:
                st.error('Failed to generate avatar.')
                return
            
            video_id = result[1]['data']['video_id']

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



if __name__ == '__main__':
    main()

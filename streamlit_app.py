import datetime
import io
import json
import pandas as pd
import streamlit as st
import openai
import hmac
from PIL import Image
import requests
import time
from scripts import Video
from summary import Summary
from templates import chatgpt_chat_completion_with_prompt, get_image_improvement_english_template, get_image_improvement_template, get_midjourney_template, get_prompt_template_teacher_introduction_talk_show, get_script_template_teacher_introduction_talk_show
from utils import (fetch_narration_in_memory, generate_avatar_heygen_with_audio_file, get_generated_avatar_heygen, get_imagine_request, 
                   fetch_image, 
                   download_image_in_memory,
                   crop_quadrants_in_memory, send_to_generate_avatar_heygen, slugify,
                   upload_object_in_memory_to_s3,
                   generate_image, open_image_from_url)



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
    st.write("Text to Image Generator using Midjourney non official API")
    image_suggestion = st.text_input('Enter Image Suggestion (ex: Course name):', 'Análise de crédito para empresas de médio porte')
    # original_image_url = st.text_input('Enter Original Image URL:', )
    # print(original_image_url)
    # if original_image_url:
    #     original_img = open_image_from_url(original_image_url)
        
    #     # Display image
    #     st.image(original_img, caption=original_image_url, use_column_width=True)

    aspect_ratio_option = st.selectbox('Aspect Ratio', ['16:9', '9:16', ])
    process_mode = st.selectbox('Process Mode', ['relax', 'fast', ])

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
            
            image_url = generate_image(image_scene_prompt, aspect_ratio = aspect_ratio_option, process_mode = process_mode)
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
    stability = st.slider("Stability:", min_value=0.0, max_value=1.0, value=0.48)
    similarity_boost = st.slider("Similarity Boost:", min_value=0.0, max_value=1.0, value=0.55)
    style = st.slider("Style:", min_value=0.0, max_value=1.0, value=0.06)

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
            file_name=f'{voice_id}__{stability}__{similarity_boost}__{style}__{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.mp3',
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
        "Template 1.4.4": "This is the text for template 2.",
        "Template 1.2.1": "This is the text for template 1.",
    }

    template = st.selectbox("Select a template", list(templates.keys()))
    generate_image_assets = st.checkbox('Generate Image Assets', value=False)
    generate_audio_assets = st.checkbox('Generate Audio Assets', value=False)
    generate_avatar_assets = st.checkbox('Generate Avatar Assets', value=False)

    final_course = st.file_uploader('Final Course JSON:', type=['json'])

    if st.button('Generate script'):
        with st.spinner("Loading..."):

            if final_course is None:
                st.error('Please, upload the final_course json file.')
                return
                
            final_course = json.load(final_course)

            if final_course.get('course_summary') is None or final_course.get('final_project') is None:
                st.error('Please, upload a valid final_course JSON file.')

            video = Video(
                onboarding = final_course['onboarding'],
                course_summary = final_course['course_summary'],
            )
            # scenes = video.run()
            scenes = video.run()[:5]

            if generate_image_assets:
                scenes = video.generate_image_files(scenes)
            
            if generate_audio_assets:
                scenes = video.generate_audio_files(scenes)

            if generate_avatar_assets:
                scenes = video.generate_avatar_files(scenes)

            # Display the DataFrame
            scenes_df = pd.DataFrame(scenes)
            st.dataframe(scenes_df)

            # Offer option to download DataFrame as a CSV file
            csv = scenes_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="scenes.csv",
                mime="text/csv"
            )
            
            st.success('Script generated successfully.')

def course_generator():
    st.write("Course Generator")

    course_type = st.selectbox('Course Type', ['professional', 'hobby', 'language',])
    
    student_name = st.text_input('Student Name', 'Marco')
    course_theme = st.text_input('Course Theme', 'Gestão de Projetos')
    student_objective = st.text_input('Student Objective', '')
    student_proficiency = st.selectbox('Student Proficiency', ['Básico', 'Intermediário', 'Avançado'])
  
    student_role_desired = None
    student_industry = None
    if course_type == 'professional':
        student_role_desired = st.selectbox('Student Role Desired', ['Junior', 'Pleno', 'Senior', 'Gestor', 'Especialista', 'Gerencia', 'Diretor'])
        student_industry = st.text_input('Student Industry', 'Bancário')

    course_area = st.text_input('Course Area', 'Finanças')

    if st.button('Generate summary and final project'):
        with st.spinner("Loading..."):
            summary_generator = Summary(
                course_type=course_type, 
                student_name=student_name, 
                course_theme=course_theme, 
                course_area=course_area, 
                student_objective=student_objective, 
                student_role_desired=student_role_desired, 
                student_industry=student_industry, 
                student_proficiency=student_proficiency
            )
            final_course = summary_generator.generate_complete_course()

            st.json(final_course)

            summary_df = summary_generator.convert_dict_summary_to_df(final_course['course_summary'])

            st.dataframe(summary_df)

            st.text_area('Final Project', final_course['final_project'])

            st.download_button(
                label="Download Final Course JSON",
                data=json.dumps(final_course, indent=4),
                file_name=f"final_course__{course_type}__{slugify(course_theme)}__{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json",
                mime="text/json"
            )
            
            st.success('Course generated successfully.')


            

def main():
    st.title("Apoia Video Engine - Toolbox")
    st.write("This app is a toolbox to help the video production.")

    if not check_password():
        st.stop()

    st.sidebar.title("Navigation")
    selection = st.sidebar.radio("Go to", [
        "Text to Image Generator (Midjourney non official API)",
        "Text to Speech Generator (ElevenLabs API)",
        "Text to Avatar Generator (Heygen API)",
        "Script Generator",
        "Course Generator",
    ])

    if selection == "Text to Image Generator (Midjourney non official API)":
        text_to_image_generator()
    elif selection == "Text to Speech Generator (ElevenLabs API)":
        text_to_speech_generator()
    elif selection == "Text to Avatar Generator (Heygen API)":
        text_to_avatar_generator()
    elif selection == "Script Generator":
        script_generator()
    elif selection == "Course Generator":
        course_generator()

    st.sidebar.header('Settings')
    st.session_state["model_option"] = st.sidebar.selectbox('LLM Model', ['gpt-3.5-turbo', 'gpt-4',])



if __name__ == '__main__':
    main()

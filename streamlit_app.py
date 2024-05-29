import datetime
import io
import json
import uuid
import pandas as pd
import streamlit as st
import openai
import hmac
from PIL import Image
import requests
import time
from fetch_lgu_service import FetchYoutubeLGU
from scripts import Template, Video, YoutubeVideo
from summary import Summary
from templates import chatgpt_chat_completion_with_prompt, get_image_improvement_english_template, get_image_improvement_template, get_midjourney_template, get_prompt_template_teacher_introduction_talk_show, get_script_template_teacher_introduction_talk_show
from utils import (fetch_narration_in_memory, generate_avatar_heygen_with_audio_file, get_generated_avatar_heygen, get_imagine_request, 
                   fetch_image, 
                   download_image_in_memory,
                   crop_quadrants_in_memory, send_to_generate_avatar_heygen, slugify,
                   upload_object_in_memory_to_s3,
                   generate_image, open_image_from_url)



voices = {
        'Danielle Galvão': {
            "avatar_id": "dd452996e8a744c7a5ba127a0722c496",
            "name": "Danielle Galvão",
            "voice_id": "PrL0UiloeutOJHWgtnhl",
            "model_id": "eleven_multilingual_v2",
        },
        'Paulo Henrique da Silveira':{
            "avatar_id": "917201ac4f24427180e20c2c7b43bce5",
            "name": "Paulo Henrique da Silveira",
            "voice_id": "VjAF4sITielIF4uPhaQq",
            "model_id": "eleven_multilingual_v2",
        },
        'Rafaela':{
            "avatar_id": "d9ca20b2a6414d549661960ca3cac50b",
            "name": "d9ca20b2a6414d549661960ca3cac50b",
            "voice_id": "pLPnQTC3hNnSUBB7SMzK",
            "model_id": "eleven_multilingual_v2",
        },
        'Fernando':{
            "avatar_id": "40b3a22fd7644911b109ff29da8c698c",
            "name": "Fernando Morais Ribeiro",
            "voice_id": "sxPCqhPEJ2CMdSQmjvu6",
            "model_id": "eleven_multilingual_v2",
        },
        'Yanco Paternó':{
            "avatar_id": "e80beb6b91cb40a59a6ed3c4ca370d3f",
            "name": "Yanco Paternó",
            "voice_id": "ORPHIL42UCbVvxd8XD6B",
            "model_id": "eleven_multilingual_v2",
        },
        'Rangel':{
            "avatar_id": "4b4db6311cfe4c3b9b840267cfca6952",
            "name": "Rangel Barbosa",
            "voice_id": "rVYXh5OmQcvchhNYtBWe",
            "model_id": "eleven_multilingual_v2",
        },
        'André':{
            "avatar_id": "a79fbc0857ed4585885d96b13a89ece0",
            "name": "André Garcia Barbosa",
            "voice_id": "MblN0w8JeK5RHsrd41Dw",
            "model_id": "eleven_multilingual_v2",
        },
        'Letícia':{
            "avatar_id": "74bcc45eb3aa4b89b26cccddab875ede",
            "name": "Letícia de Paula Sacco",
            "voice_id": "gPsEBQXtNJMgQt80xSV0",
            "model_id": "eleven_multilingual_v2",
        },
        'Alexandre':{
            "avatar_id": "1c6d68f94dbb4be8a41d8f35b83f2852",
            "name": "Alexandre Naressi",
            "voice_id": "kRJZKpG96QKcf6B19BzP",
            "model_id": "eleven_multilingual_v2",
        },
        'Renata':{
            "avatar_id": "e2c9701d03994e549dc83653f4819779",
            "name": "Renata del Bove",
            "voice_id": "q9UszhvKZ77IjWcD1KP9",
            "model_id": "eleven_multilingual_v2",
        },
        'Eduardo':{
            "avatar_id": "eac1815fdf964f8e9f8dc38bc41e5281",
            "name": "Eduardo Henrique Leitner",
            "voice_id": "VoyyBAj0yhhEGxtHYMGv",
            "model_id": "eleven_multilingual_v2",
        },
        'Bruno Ferraz': {
            "avatar_id": "10a9049c5c044f3d850a4f15d5f6f8c0",
            "name": "Bruno Ferraz",
            "voice_id": "4mQCVZJlX5XqhyYkFOnI",
            "model_id": "eleven_multilingual_v2",
        },
        'Arthur Chavoni': {
            "avatar_id": "ea8819003c92479eb44ea318e9e80d18",
            "name": "Arthur Chavoni",
            "voice_id": "WM6MYeKbzs7NcYwwmuqQ",
            "model_id": "eleven_multilingual_v2",
        },
        'Alessandro Nasser': {
            "avatar_id": "57e128f8987144f8bcf2c3a30989a647",
            "name": "Alessandro Nasser",
            "voice_id": "h3wMxGszaOQ9hiRKOqQZ",
            "model_id": "eleven_multilingual_v2",
        },
        'Claudia Muniz': {
            "avatar_id": "cb870716aa5a429e8c7b9971150ee5ca",
            "name": "Claudia Muniz",
            "voice_id": "VCCSalUJGlrbOJYYiuND",
            "model_id": "eleven_multilingual_v2",
        },
        'Franci Alves': {
            "avatar_id": "8d1442137a41486780502d1ce23f52f3",
            "name": "Franci Alves",
            "voice_id": "5891FIbvQ4j2FoQgrKoS",
            "model_id": "eleven_multilingual_v2",
        },
        'Maron Guimarães': {
            "avatar_id": "7aaff774dbdd4fdbb6f61eb252c6981b",
            "name": "Maron Guimarães",
            "voice_id": "DLJ8Zf9uhuGda879eSW0",
            "model_id": "eleven_multilingual_v2",
        },
        'Larissa Rocha': {
            "avatar_id": "5ddaba7b54c74f58a99f6dd616a71360",
            "name": "Larissa Rocha",
            "voice_id": "5YIXaBwifD2DVWpWwDag",
            "model_id": "eleven_multilingual_v2",
        },
        'Renan Rêgo': {
            "avatar_id": "8d505dc14b854536a3808281e1b9e130",
            "name": "Renan Rêgo",
            "voice_id": "3DwN6eXCaKk14UXdHnGH",
            "model_id": "eleven_multilingual_v2",
        },
    }

youtube_channel_options = [
    "Apoia.Marketing.Digital",
    "Apoia.Recursos Humanos",
    "Apoia.Gestão e Administração",
    "Apoia.Finanças",
    "Apoia.Psicologia",
    "Apoia.Marketing",
    "Apoia.Vendas",
    "Apoia.Contabilidade",
    "Apoia.Educação Infantil",
    "Apoia.Educacao",
    "Apoia.DireitoCivil",
    "Apoia.Produto.e.Product Design",
    "Apoia.Design",
    "Apoia.Tecnologia",
]

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
    
    selected_voice = st.selectbox("Select a voice:", list(voices.keys()))
    text = st.text_area("Enter text:", """Alcançe seus objetivos na medida""")
    stability = st.slider("Stability:", min_value=0.0, max_value=1.0, value=0.48)
    similarity_boost = st.slider("Similarity Boost:", min_value=0.0, max_value=1.0, value=0.55)
    style = st.slider("Style:", min_value=0.0, max_value=1.0, value=0.00)

    if st.button('Generate Speech'):
        voice_id = voices[selected_voice]['voice_id']
        model_id = voices[selected_voice]['model_id']

        audio_data = fetch_narration_in_memory(text, voice_id, stability, similarity_boost, style, model_id)
        
        audio_data.seek(0)
        st.audio(audio_data.read(), format='audio/mp3')

        audio_url = upload_object_in_memory_to_s3(audio_data, f'narration/{uuid.uuid4()}.mp3')

        if audio_url:
            st.success(f'Audio generated successfully. at {audio_url}')

        audio_data.seek(0)
        st.download_button(
            label="Download audio file",
            data=audio_data.read(),
            file_name=f'{voice_id}__{stability}__{similarity_boost}__{style}__{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.mp3',
            mime="audio/mpeg"
        )

def text_to_avatar_generator():

    st.write("Text to Avatar Generator using Heygen API")

    selected_avatar = st.selectbox("Select a voice:", list(voices.keys()))
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
                    avatar_id = voices[selected_avatar]['avatar_id']
                    result = generate_avatar_heygen_with_audio_file(audio_url=audio_url, avatar_id=avatar_id, is_teste=test)
            
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
        # "Template 1.4.4": "This is the text for template 2.",
        # "Template 1.2.1": "This is the text for template 1.",
        "Template A - Youtube": "Template A - Youtube",
        "Template B - Youtube": "Template B - Youtube",
        "Template C - Youtube": "Template C - Youtube",
    }

    template = st.selectbox("Select a template", list(templates.keys()))
    selected_avatar = st.selectbox("Select a voice:", list(voices.keys()))

    # vars = {
    #     "study_institution": lambda: st.text_input('Study Institution:', placeholder='estudei na ...'),
    #     "course_name": lambda: st.text_input('Course Name:', placeholder='curso de ... *sem palavra "curso", ex: Negócios'),
    #     "course_objective": lambda: st.text_input('Course Objective:', placeholder='conhecimentos necessários para ...'),
    #     "topic01": lambda: st.text_input('Topic 01:', placeholder='Análise de crédito', max_chars=40),
    #     "topic02": lambda: st.text_input('Topic 02:', placeholder='Risco de crédito', max_chars=40),
    #     "topic03": lambda: st.text_input('Topic 03:', placeholder='Rating de crédito', max_chars=40),
    #     "topic04": lambda: st.text_input('Topic 04:', placeholder='Gestão de risco', max_chars=40),
    #     "area": lambda: st.text_input('Area:', placeholder='Finanças'),
    #     "past_experience": lambda: st.text_input('Past Experience:', placeholder='passei por várias empresas como ...'),
    #     "current_job": lambda: st.text_input('Current Job:', placeholder='atualmente sou ...'),
    #     "youtube_channel_name": lambda: st.text_input('Youtube Channel Name:', placeholder='Apoia.Tecnologia'),
    #     "hobbies": lambda: st.text_input('Hobbies:', placeholder='gosto demais de ...'),
    #     "hobby_image_url_1": lambda: st.text_input('Hobby Image URL 1:', placeholder='https://...'),
    #     "hobby_image_url_2": lambda: st.text_input('Hobby Image URL 2:', placeholder='https://...'),
    #     "hobby_image_url_3": lambda: st.text_input('Hobby Image URL 3:', placeholder='https://...'),
    # }

    study_institution = st.text_input('Study Institution:', placeholder='estudei na ...')
    course_name = st.text_input('Course Name:', placeholder='curso de ... *sem palavra "curso", ex: Negócios')
    course_objective = st.text_input('Course Objective:', placeholder='conhecimentos necessários para ...')
    topic01 = st.text_input('Topic 01:', placeholder='Análise de crédito', max_chars=40)
    topic02 = st.text_input('Topic 02:', placeholder='Risco de crédito', max_chars=40)
    topic03 = st.text_input('Topic 03:', placeholder='Rating de crédito', max_chars=40)
    topic04 = st.text_input('Topic 04:', placeholder='Gestão de risco', max_chars=40)
    area = st.text_input('Area:', placeholder='Finanças')
    past_experience = st.text_input('Past Experience:', placeholder='passei por várias empresas como ... e ... (passar duas empresas)')
    current_job = st.text_input('Current Job:', placeholder='atualmente sou ...')
    youtube_channel_name = st.selectbox('Youtube Channel Name:', options=youtube_channel_options)
    hobbies = st.text_input('Hobbies:', placeholder='gosto demais de ... e ... (passar dois hobbies)')
    hobby_image_url_1 = st.text_input('Hobby Image URL 1:', placeholder='https://...')
    hobby_image_url_2 = st.text_input('Hobby Image URL 2:', placeholder='https://...')
    hobby_image_url_3 = st.text_input('Hobby Image URL 3:', placeholder='https://...')
    instructor_image_url = st.text_input('Instructor Image URL:', placeholder='https://...')

    selected_template = Template().template_selection[template]
    # selected_variables = selected_template['vars']
    
    # for var in selected_variables:
    #     vars[var]()

    generate_audio_assets = st.checkbox('Generate Audio Assets', value=False)
    generate_avatar_assets = st.checkbox('Generate Avatar Assets', value=False)
    stability = st.slider("Stability:", min_value=0.0, max_value=1.0, value=0.48)
    similarity_boost = st.slider("Similarity Boost:", min_value=0.0, max_value=1.0, value=0.55)
    style = st.slider("Style:", min_value=0.0, max_value=1.0, value=0.0)

    # final_course = st.file_uploader('Final Course JSON:', type=['json'])

    if st.button('Generate script'):
        with st.spinner("Loading..."):

            config = dict(
                study_institution = study_institution,
                course_name = course_name,
                course_objective = course_objective,
                topic01 = topic01,
                topic02 = topic02,
                topic03 = topic03,
                topic04 = topic04,
                area = area,
                past_experience = past_experience,
                current_job = current_job,
                youtube_channel_name = youtube_channel_name,
                hobbies = hobbies,
                hobby_image_url_1 = hobby_image_url_1,
                hobby_image_url_2 = hobby_image_url_2,
                hobby_image_url_3 = hobby_image_url_3,
                instructor_image_url = instructor_image_url,
                
                instructor_name = voices[selected_avatar]['name'],
                template_selected = selected_template['script'],
            )

            # print(vars["study_institution"].__str__(), )

            video = YoutubeVideo(
                config
            )

            # scenes = video.setup_intro_scene()[:3]
            scenes = video.setup_intro_scene()

            scenes_df = pd.DataFrame(scenes)
            st.dataframe(scenes_df['narration_text'])

            # if generate_image_assets:
            #     scenes = video.generate_image_files(scenes)
            
            if generate_audio_assets:
                scenes = video.generate_audio_files(scenes, stability=stability, similarity_boost=similarity_boost, style=style, voice_id=voices[selected_avatar]['voice_id'], model_id=voices[selected_avatar]['model_id'])

            if generate_avatar_assets:
                scenes = video.generate_avatar_files(scenes, avatar_id=voices[selected_avatar]['avatar_id'], is_teste=False)

            scenes_df = pd.DataFrame(scenes)
            st.dataframe(scenes_df)

            # Offer option to download DataFrame as a CSV file
            csv = scenes_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"{template}_{selected_avatar}.csv",
                mime="text/csv"
            )
            
            st.success('Script generated successfully.')

def course_generator():
    st.write("Course Generator")

    st.markdown('[GPT-4 and GPT-4 Turbo Documentation](https://platform.openai.com/docs/models/gpt-4-and-gpt-4-turbo)')
    model_selection = st.selectbox('LLM Model', ['gpt-4', 'gpt-4-turbo-preview', 'gpt-3.5-turbo', ])

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
            start = time.time()
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
            summary_generator.model = model_selection
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
            end = time.time()
            
            st.success(f'Course generated successfully in {round(end - start, 1)} seconds')

def fetch_lgus():
    st.write("Fetch LGUs given a course json")

    final_course = st.file_uploader('Final Course JSON:', type=['json'])

    if st.button('Fetch LGUs'):
        with st.spinner("Loading..."):

            if final_course is None:
                st.error('Please, upload the final_course json file.')
                return
                
            final_course = json.load(final_course)

            if final_course.get('course_summary') is None:
                st.error('Please, upload a valid final_course JSON file.')

            video = FetchYoutubeLGU(
                onboarding = final_course['onboarding'],
                course_summary = final_course['course_summary'],
            )

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
    # elif selection == "Course Generator":
    #     course_generator()

    # st.sidebar.header('Settings')
    # st.session_state["model_option"] = st.sidebar.selectbox('LLM Model', ['gpt-3.5-turbo', 'gpt-4',])



if __name__ == '__main__':
    main()

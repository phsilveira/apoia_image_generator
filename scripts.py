import datetime
from concurrent.futures import ThreadPoolExecutor
import time
from typing import List
import uuid
from tqdm import tqdm
import json
import re
import settings
from openai import OpenAI
import pandas as pd

from utils import fetch_narration_in_memory, generate_avatar_heygen_with_audio_file, generate_image, get_generated_avatar_heygen, upload_object_in_memory_to_s3


class Video:

    config = dict(
        student_industry = 'Genérico',
        professional_area = 'Genérico',
        student_position = 'Genérico',
        course_name = 'Genérico',
        course_summary = {
            "course_name": "Curso de Gestão de Projetos Financeiros",
            "chapters": [
                {
                "chapter_name": "Fundamentos da Gestão de Projetos",
                "sections": [
                    {
                    "section_name": "Introdução à Gestão de Projetos",
                    "subsections": ["Definição e Importância", "História e Evolução"]
                    },
                    {
                    "section_name": "Metodologias de Gestão de Projetos",
                    "subsections": ["Ágil", "Cascata", "Híbrido"]
                    },
                    {
                    "section_name": "Ciclo de Vida de um Projeto",
                    "subsections": ["Iniciação", "Planejamento", "Execução", "Monitoramento e Controle", "Encerramento"]
                    }
                ]
                },
                {
                "chapter_name": "Planejamento e Estratégia Financeira",
                "sections": [
                    {
                    "section_name": "Análise de Viabilidade Financeira",
                    "subsections": ["Análise de Custo-Benefício", "Análise de Ponto de Equilíbrio"]
                    },
                    {
                    "section_name": "Orçamentação e Alocação de Recursos",
                    "subsections": ["Orçamento Base Zero", "Orçamento Incremental"]
                    },
                    {
                    "section_name": "Projeções Financeiras e Modelagem",
                    "subsections": ["Projeção de Fluxo de Caixa", "Modelagem de Cenários"]
                    }
                ]
                },
                {
                "chapter_name": "Gestão de Riscos em Projetos",
                "sections": [
                    {
                    "section_name": "Identificação e Avaliação de Riscos",
                    "subsections": ["Riscos Financeiros", "Riscos Operacionais"]
                    },
                    {
                    "section_name": "Mitigação e Gestão de Riscos",
                    "subsections": ["Estratégias de Mitigação", "Planos de Resposta a Riscos"]
                    },
                    {
                    "section_name": "Plano de Contingência",
                    "subsections": ["Desenvolvimento de Planos de Contingência", "Testes e Revisões de Planos de Contingência"]
                    }
                ]
                },
                {
                "chapter_name": "Análise e Tomada de Decisão",
                "sections": [
                    {
                    "section_name": "Ferramentas de Análise Financeira",
                    "subsections": ["Análise de Balanço", "Análise de Demonstração de Resultados"]
                    },
                    {
                    "section_name": "ROI e Payback Period",
                    "subsections": ["Cálculo de ROI", "Determinação do Payback Period"]
                    },
                    {
                    "section_name": "Decisões Baseadas em Dados",
                    "subsections": ["Análise de Dados", "Visualização de Dados"]
                    }
                ]
                },
                {
                "chapter_name": "Liderança e Gestão de Stakeholders",
                "sections": [
                    {
                    "section_name": "Comunicação Eficaz com Stakeholders",
                    "subsections": ["Técnicas de Comunicação", "Gerenciamento de Expectativas"]
                    },
                    {
                    "section_name": "Gestão de Expectativas",
                    "subsections": ["Mapeamento de Stakeholders", "Engajamento de Stakeholders"]
                    },
                    {
                    "section_name": "Negociação e Resolução de Conflitos",
                    "subsections": ["Técnicas de Negociação", "Resolução de Conflitos"]
                    }
                ]
                },
                {
                "chapter_name": "Monitoramento e Controle de Projetos",
                "sections": [
                    {
                    "section_name": "KPIs e Métricas de Desempenho",
                    "subsections": ["Seleção de KPIs", "Análise de Métricas"]
                    },
                    {
                    "section_name": "Relatórios de Progresso",
                    "subsections": ["Desenvolvimento de Relatórios", "Comunicação de Progresso"]
                    },
                    {
                    "section_name": "Revisão e Ajustes de Projeto",
                    "subsections": ["Processos de Revisão", "Ajustes e Melhorias"]
                    }
                ]
                }
            ]
            }
    )

    script_object = {
        'can_be_random': False,
        'objective': '',
        'target': '',
        'narration_text': '',
        'narration_audio_url': '',
        'use_avatar': False,
        'avatar_video_url': '',
        'title_a': '',
        'text_1': '',
        'text_2': '',
        'text_3': '',
        'text_4': '',
        'images_length': 0,
        'image_1_url': '',
        'image_2_url': '',
        'image_3_url': '',
        'question_text': '',
        'answer_1_text': '',
        'answer_2_text': '',
        'answer_3_text': '',
        'answer_4_text': '',
        'correct_answer_text': '',
        'correct_answer_number': '',
        'correct_letter_image_url': '',
        'narration_answer_text': '',
        'narration_answer_audio_url': '',
    }

    choice_number_to_url = {
        "1": "https://apoia-cdn.s3.sa-east-1.amazonaws.com/quiz_assets_letters/A1_0000.png",
        "2": "https://apoia-cdn.s3.sa-east-1.amazonaws.com/quiz_assets_letters/B1_0000.png",
        "3": "https://apoia-cdn.s3.sa-east-1.amazonaws.com/quiz_assets_letters/C1_0000.png",
        "4": "https://apoia-cdn.s3.sa-east-1.amazonaws.com/quiz_assets_letters/D1_0000.png",
    }

    def __init__(self, onboarding, course_summary):
        self.client = OpenAI(api_key = settings.OPENAI_API_KEY )
        self.config.update(onboarding)
        self.config['course_summary'] = course_summary

    def run(self):
        # setup scenes
        intro_scenes = self.setup_intro_scene()
        chapter_scenes = self.setup_chapters_scene()
        quiz_scenes = self.setup_quiz_scene()
        conclusion_scenes = self.setup_conclusion_scene()

        scenes = intro_scenes + chapter_scenes + quiz_scenes + conclusion_scenes

        # generate assets


        return scenes

    def setup_intro_scene(self) -> List[dict]:
        # INTRODUÇÃO RESUMO CURSO - TEMPLATE
        scene_intro_overview = self.script_object.copy()
        scene_intro_overview['target'] = 'scene_intro_overview'
        scene_intro_overview['objective'] = 'Introdução Sumário'
        scene_intro_overview['narration_text'] = f'Agora, Vamos Descobrir todo o conteúdo que preparamos para você no curso `{self.config.get("course_name")}`?'
        scene_intro_overview['use_avatar'] = True
        return [scene_intro_overview]

    def setup_chapters_scene(self) -> List[dict]:
        scenes = []

        chapters_narration_and_image_suggestion_list = self.cot_chapters_narration_and_image_suggestion()
        narration_script = [{'scene_title': r['scene_title'], 'narration': ['narration']} for r in chapters_narration_and_image_suggestion_list]
        
        video_texts_list = self.cot_video_texts(narration_script)

        for chapter in video_texts_list: chapter.pop('narration')

        chapter_scenes_list = []

        for dict1, dict2 in zip(chapters_narration_and_image_suggestion_list, video_texts_list):
            merged_dict = {**dict1, **dict2}
            chapter_scenes_list.append(merged_dict)
        
        # OVERVIEW DOS CAPÍTULOS - PROMPT
        

        for i, chapter in enumerate(chapter_scenes_list):
            scene_overview = self.script_object.copy()

            # properties
            scene_overview['target'] = f'scene_{i}_overview'
            scene_overview['can_be_random'] = True
            scene_overview['use_avatar'] = True
            scene_overview['objective'] = 'Overview Capítulos'
            scene_overview['images_length'] = 2

            scene_overview['narration_text'] = chapter['narration']
            scene_overview['title_a'] = chapter['scene_title']
            scene_overview['text_1'] = chapter['highlight_1']
            scene_overview['text_2'] = chapter['highlight_2']
            scene_overview['text_3'] = chapter['highlight_3']
            scene_overview['text_4'] = chapter['highlight_4']
            scene_overview['image_description_suggestion_1'] = chapter['image_description_suggestion_1']
            scene_overview['image_description_suggestion_2'] = chapter['image_description_suggestion_2']
            scene_overview['image_description_suggestion_3'] = chapter['image_description_suggestion_3']

            scenes.append(scene_overview)

        scene_end_overview = self.script_object.copy()
        scene_end_overview['target'] = f'scene_end_overview'
        scene_end_overview['can_be_random'] = False
        scene_end_overview['use_avatar'] = True
        scene_end_overview['objective'] = 'Fim Sumário'
        scene_end_overview['narration_text'] = f'Esse é o CONTEÚDO que vamos ver no seu CURSO! Cada módulo - está repleto de exemplos PRÁTICOS e conteúdo DIRETO AO PONTO!'
        
        scenes.append(scene_end_overview)
        
        return scenes

    def setup_quiz_scene(self):
        scenes = []

        # INTRODUÇÃO QUIZ - TEMPLATE
        scene_01_intro_quiz = self.script_object.copy()
        scene_01_intro_quiz['target'] = f'scene_01_intro_quiz'
        scene_01_intro_quiz['can_be_random'] = False
        scene_01_intro_quiz['use_avatar'] = False
        scene_01_intro_quiz['objective'] = 'Introdução Quiz'
        scene_01_intro_quiz['narration_text'] = f'Agora, APERTE O CINTO... porque vamos INICIAR sua jornada com um Quiz PARA aquecer os Motores!'

        scene_02_intro_quiz = self.script_object.copy()
        scene_02_intro_quiz['target'] = f'scene_02_intro_quiz'
        scene_02_intro_quiz['can_be_random'] = False
        scene_02_intro_quiz['use_avatar'] = True
        scene_02_intro_quiz['objective'] = 'Introdução Quiz'
        scene_02_intro_quiz['narration_text'] = f'Aqui está como funciona: Preparamos VÁRIAS perguntas; em níveis de dificuldade diferentes... Cada pergunta vem com QUATRO opções, mas APENAS UMA está correta.'

        scene_03_intro_quiz = self.script_object.copy()
        scene_03_intro_quiz['target'] = f'scene_03_intro_quiz'
        scene_03_intro_quiz['can_be_random'] = False
        scene_03_intro_quiz['use_avatar'] = True
        scene_03_intro_quiz['objective'] = 'Introdução Quiz'
        scene_03_intro_quiz['narration_text'] = f'Você tem DEZ SEGUNDOS para responder cada pergunta. Mas ei, sem pressão! Você pode Pausar O VÍDEO se precisar de mais tempo.'

        scene_04_intro_quiz = self.script_object.copy()
        scene_04_intro_quiz['target'] = f'scene_04_intro_quiz'
        scene_04_intro_quiz['can_be_random'] = False
        scene_04_intro_quiz['use_avatar'] = False
        scene_04_intro_quiz['objective'] = 'Introdução Quiz'
        scene_04_intro_quiz['narration_text'] = f'Não esqueça de anotar QUANTAS perguntas você acertou. Se você errar alguma, sem problema!'

        scene_05_intro_quiz = self.script_object.copy()
        scene_05_intro_quiz['target'] = f'scene_05_intro_quiz'
        scene_05_intro_quiz['can_be_random'] = False
        scene_05_intro_quiz['use_avatar'] = True
        scene_05_intro_quiz['objective'] = 'Introdução Quiz'
        scene_05_intro_quiz['narration_text'] = f'Vamos ver TODO O CONTEÚDO desse Quiz durante nosso curso, de forma Rápida e Prática! Vamos começar?'

        scenes.append(scene_01_intro_quiz)
        scenes.append(scene_02_intro_quiz)
        scenes.append(scene_03_intro_quiz)
        scenes.append(scene_04_intro_quiz)
        scenes.append(scene_05_intro_quiz)

        # PERGUNTAS QUIZ - PROMPT
        quiz_dict = self.cot_quiz_questions()

        for i, quiz in enumerate(quiz_dict):

            scene_quiz = self.script_object.copy()
            scene_quiz['target'] = f'scene_quiz_{i}'
            scene_quiz['can_be_random'] = False
            scene_quiz['use_avatar'] = False
            scene_quiz['objective'] = 'Perguntas Quiz'
            scene_quiz['narration_text'] = quiz['question']
            scene_quiz['narration_answer_text'] = f'A resposta certa é: {quiz["correct_answer_text"]}'

            scene_quiz['question_text'] = quiz['question']
            scene_quiz['answer_1_text'] = quiz['answer_1']
            scene_quiz['answer_2_text'] = quiz['answer_2']
            scene_quiz['answer_3_text'] = quiz['answer_3']
            scene_quiz['answer_4_text'] = quiz['answer_4']
            scene_quiz['correct_answer_number'] = quiz['correct_answer_number']
            scene_quiz['correct_letter_image_url'] = self.choice_number_to_url[quiz['correct_answer_number']]

            scenes.append(scene_quiz)
        return scenes

    def setup_conclusion_scene(self):
        scenes = []
        # CONCLUSÃO - TEMPLATE

        scene_01_end_quiz = self.script_object.copy()
        scene_01_end_quiz['target'] = f'scene_01_end_quiz'
        scene_01_end_quiz['can_be_random'] = False
        scene_01_end_quiz['use_avatar'] = False
        scene_01_end_quiz['objective'] = 'Conclusão do Quiz'
        scene_01_end_quiz['narration_text'] = 'PARABÉNS, chegamos ao final do nosso Quiz! Como você se saiu?'

        scenes.append(scene_01_end_quiz)

        scene_02_end_quiz = self.script_object.copy()
        scene_02_end_quiz['target'] = f'scene_02_end_quiz'
        scene_02_end_quiz['can_be_random'] = False
        scene_02_end_quiz['use_avatar'] = True
        scene_02_end_quiz['objective'] = 'Conclusão do Vídeo'
        scene_02_end_quiz['narration_text'] = 'Se alguma pergunta foi difícil... TUDO BEM... Lembre-se, na sua jornada, NÃO EXISTE FALHA, apenas DESCOBERTA!'

        scenes.append(scene_02_end_quiz)

        scene_01_end_video = self.script_object.copy()
        scene_01_end_video['target'] = f'scene_01_end_video'
        scene_01_end_video['can_be_random'] = False
        scene_01_end_video['use_avatar'] = False
        scene_01_end_video['objective'] = 'Conclusão do Vídeo'
        scene_01_end_video['narration_text'] = 'Agora, vamos transformar esses INSIGHTS em AÇÃO! O seu CURSO espera por você, cheio de: CONHECIMENTO, DIVERSÃO e infinitas POSSIBILIDADES!'

        scenes.append(scene_01_end_video)

        scene_02_end_video = self.script_object.copy()
        scene_02_end_video['target'] = f'scene_02_end_video'
        scene_02_end_video['can_be_random'] = False
        scene_02_end_video['use_avatar'] = True
        scene_02_end_video['objective'] = 'Conclusão do Vídeo'
        scene_02_end_video['narration_text'] = 'Agora que você já sabe TUDO QUE LHE ESPERA nessa jornada, preparamos uma Atividade Prática para você. Vamos colocar esses conhecimentos em prática? NOS VEMOS na próxima Aula!'

        scenes.append(scene_02_end_video)

        scene_brand_signature = self.script_object.copy()
        scene_brand_signature['target'] = f'scene_brand_signature'
        scene_brand_signature['objective'] = 'Assinatura'

        scenes.append(scene_brand_signature)
        return scenes

    def generate_image_files(self, scenes: List[dict]) -> List[dict]:
        print('Generating images')

        def generate_image_for_scene(scene, i):
            if scene['images_length'] > 0:
                for j in range(1, scene['images_length'] + 1):
                    image_prompt = scene[f'image_description_suggestion_{j}']
                    scenes[i][f'image_{j}_url'] = generate_image(image_prompt, aspect_ratio = '16:9', process_mode = 'fast') # f'{i}_image_{j}_url'

        with ThreadPoolExecutor() as executor:
            executor.map(generate_image_for_scene, scenes, range(len(scenes)))

        return scenes

    def generate_audio_files(self, scenes: List[dict]) -> List[dict]:
        print('Generating audio')

        def generate_audio_for_scene(scene):
            if scene['narration_text']:
                scene['narration_audio_url'] = self.generate_audio_file_and_upload(scene['narration_text'])

            if scene['narration_answer_text']:
                scene['narration_answer_audio_url'] = self.generate_audio_file_and_upload(scene['narration_answer_text'])

        with ThreadPoolExecutor() as executor:
            list(executor.map(generate_audio_for_scene, scenes))

        return scenes

    def generate_audio_file_and_upload(self, narration_text):
        voice_id = "rVYXh5OmQcvchhNYtBWe"
        model_id = "eleven_multilingual_v2"
        stability = 0.48
        similarity_boost = 0.55
        style = 0.06

        audio_data = fetch_narration_in_memory(narration_text, voice_id, stability, similarity_boost, style, model_id)
        # audio_url = upload_object_in_memory_to_s3(audio_data, f'narration/{voice_id}__{stability}__{similarity_boost}__{style}__{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.mp3')
        audio_url = upload_object_in_memory_to_s3(audio_data, f'narration/{uuid.uuid4()}.mp3')

        return audio_url

    def generate_avatar_files(self, scenes: List[dict]) -> List[dict]:
        print('Generating avatares')

        def generate_avatar_for_scene(scene):
            if scene['use_avatar']:
                audio_url = scene['narration_audio_url']
                result = generate_avatar_heygen_with_audio_file(audio_url=audio_url, is_teste=True)
                video_id = result[1]['data']['video_id']
                result = get_generated_avatar_heygen(video_id)

                while result[1]['data']['status'] != 'completed':
                    time.sleep(10)
                    print(result)
                    result = get_generated_avatar_heygen(video_id)

                video_url = result[1]['data']['video_url']
                # video_url = upload_object_in_memory_to_s3(audio_data, f'narration/{uuid.uuid4()}.mp3')
                print(f"Avatar {scene['target']}: {video_url}")
                scene['avatar_video_url'] = video_url

        with ThreadPoolExecutor() as executor:
            list(executor.map(generate_avatar_for_scene, scenes))

        return scenes

    def cot_chapters_narration_and_image_suggestion(self, ) -> List[dict]:
        with open('prompts/cot_chapters_narration_and_image_suggestion.txt', 'r') as file:
            message = file.read()
        message = message.format_map(self.config)
        result = self.chat_complete(message)
        return self.parse_json_to_dict(result)['scene']

    def cot_video_texts(self, narration_script) -> List[dict]:
        with open('prompts/cot_video_texts.txt', 'r') as file:
            message = file.read()
        message = message.format(narration_script=narration_script)
        result = self.chat_complete(message)
        return self.parse_json_to_dict(result)['narration']

    def cot_quiz_questions(self, ) -> List[dict]:
        with open('prompts/cot_quiz_questions.txt', 'r') as file:
            message = file.read()
        message = message.format_map(self.config)
        result = self.chat_complete(message)
        return self.parse_json_to_dict(result)['quiz_list']

    def clean_json_string(self, json_string):
        pattern = r'^```json\s*(.*?)\s*```$'
        cleaned_string = re.sub(pattern, r'\1', json_string, flags=re.DOTALL)
        return cleaned_string.strip()

    def parse_json_to_dict(self, json_string):
        cleaned_string = self.clean_json_string(json_string)
        return json.loads(cleaned_string)

    def get_completion(self, messages, model="gpt-3.5-turbo", temperature=0):
        response = self.client.chat.completions.create(
            model=model,
            response_format={ "type": "json_object" },
            messages=messages
        )
        return response.choices[0].message.content

    def chat_complete(self, system_prompt, model="gpt-3.5-turbo", temperature=0) -> str:
        messages = [
            {"role":"system", "content": system_prompt},
        ]
        return self.get_completion(messages, model, temperature)

class Template:

    template_selection = {
        "Template A - Youtube":{ 
            "vars": ["course_name", "study_institution", "past_experience", "current_job", "course_objective", "topic01", "topic02", "topic03",],
            "script": [
                {"use_avatar":False, "narration_text": "Curso de {course_name}? Você nunca viu um deste aqui!", "target":"scene_01_intro", "objective": "Introdução"},
                {"use_avatar":False, "narration_text": "Sabe aquele curso comprido, cheio de teoria e que só repete algum livro que você já leu? Aqui, vai ser tudo diferente.", "target":"scene_02_intro", "objective": "Introdução"},
                {"use_avatar":False, "narration_text": "O curso vai sair personalizado do seu jeito e de um jeito que você nem imagina!", "target":"scene_03_intro", "objective": "Introdução"},
                {"use_avatar":True, "narration_text": "Veja até o fim do vídeo e, se gostar, curta a gente, e visite o nosso site, no link abaixo, para maiores informações.", "target":"scene_04_intro", "objective": "Introdução"},
                {"use_avatar":True, "narration_text": "Sou {instructor_name}, estudei na {study_institution}, passei por várias empresas como {past_experience} e atualmente sou {current_job}.", "target":"scene_01_mentor", "objective": "Mentor"},
                {"use_avatar":True, "narration_text": "Eu também sou o especialista do curso de {course_name} e o nosso objetivo inicial quando desenhamos esse curso é te capacitar com habilidades e conhecimentos necessários para {course_objective}, abordando competências-chave: ", "target":"scene_02_mentor", "objective": "Mentor"},
                {"use_avatar":False, "narration_text": "{topic01} ...{topic02}... e também {topic03}", "target":"scene_03_mentor", "objective": "Mentor"},
                {"use_avatar":True, "narration_text": "Mas, isso é só plano inicial! Vou deixar para o Rangel, co-fundador da Apoia, te explicar como funciona, pois eu te disse que somos únicos!", "target":"scene_04_mentor", "objective": "Mentor"},
            ]
        },
        "Template B - Youtube": {
            "vars": ["course_name", "past_experience", "current_job", "hobbies", "hobby_image_url_3", "hobby_image_url_1", "hobby_image_url_2", "topic01", "topic02", "topic03", "topic04", "instructor_image_url"],
            "script":[
                {
                    'can_be_random': False,
                    'objective': 'Introdução',
                    'target': 'scene_01_intro',
                    'narration_text': 'Curso grátis de {course_name} com conteúdo que VOCÊ escolher?',
                    'use_avatar': False,
                    'title_a': '{course_name} • {course_name} • {course_name} • {course_name}',
                },
                {
                    'can_be_random': False,
                    'objective': 'Introdução',
                    'target': 'scene_02_intro',
                    'narration_text': 'Você já estudou coisas que não eram importantes para você? Quem NÃO?',
                    'use_avatar': False,
                },
                {
                    'can_be_random': False,
                    'objective': 'Introdução',
                    'target': 'scene_03_intro',
                    'narration_text': 'Mas AQUI, você escolhe os capítulos e tem os projetos práticos e ferramentas digitais voltadas para os SEUS objetivos!',
                    'use_avatar': False,
                },
                {
                    'can_be_random': False,
                    'objective': 'Introdução',
                    'target': 'scene_04_intro',
                    'narration_text': 'E isso tudo com os GRANDES especialistas em suas áreas!',
                    'use_avatar': False,
                    'images_length': 1,
                    'image_1_url': '{instructor_image_url}',
                },
                {
                    'can_be_random': False,
                    'objective': 'Mentor',
                    'target': 'scene_01_mentor',
                    'narration_text': 'Sou {instructor_name}, passei por empresas como {past_experience} e atualmente sou {current_job}.',
                    'use_avatar': True,
                    'title_a': '{instructor_name}',
                    'text_1': ' {current_job}',
                },
                {
                    'can_be_random': False,
                    'objective': 'Mentor',
                    'target': 'scene_02_mentor',
                    'narration_text': 'Além disso, gosto DEMAIS de {hobbies}.',
                    'use_avatar': False,
                    'images_length': 3,
                    'image_1_url': '{hobby_image_url_3}',
                    'image_2_url': '{hobby_image_url_1}',
                    'image_3_url': '{hobby_image_url_2}'
                },
                {
                    'can_be_random': False,
                    'objective': 'Mentor',
                    'target': 'scene_03_mentor',
                    'narration_text': 'Se gostar do nosso vídeo, não esqueça de seguir a gente para receber conteúdo gratuito relevante para sua profissão ou interesses pessoais e dar um like no vídeo para nos apoiar.',
                    'use_avatar': True,
                    'title_a': 'Curso de {course_name}',
                },
                {
                    'can_be_random': False,
                    'objective': 'Mentor',
                    'target': 'scene_04_mentor',
                    'narration_text': 'Visite o nosso site, no link abaixo, para fazer seu PRIMEIRO curso!',
                    'use_avatar': False,
                },
                {
                    'can_be_random': False,
                    'objective': 'Apresentação',
                    'target': 'scene_01_presentation',
                    'narration_text': 'Eu sou um dos especialistas do curso de {course_name} na Apoia e procuramos cobrir os PRINCIPAIS tópicos, como:',
                    'use_avatar': True,
                },
                {
                    'can_be_random': False,
                    'objective': 'Apresentação',
                    'target': 'scene_02_presentation',
                    'narration_text': '{topic01} ... {topic02} ... {topic03} ... e também {topic04}.',
                    'use_avatar': False,
                    'title_a': '{topic01}',
                    'text_1': '{topic02}',
                    'text_2': '{topic03}',
                    'text_3': '{topic04}',
                },
                {
                    'can_be_random': False,
                    'objective': 'Apresentação',
                    'target': 'scene_03_presentation',
                    'narration_text': 'Mas, isso é só o plano inicial… Agora, vou te explicar como funciona, pois tenho que te mostrar como somos únicos!',
                    'use_avatar': True,
                },
                {
                    'can_be_random': False,
                    'objective': 'Apresentação',
                    'target': 'scene_04_presentation',
                    'narration_text': 'Na Apoia, acreditamos em 5 pilares:',
                    'use_avatar': False,
                },
                {
                    'can_be_random': False,
                    'objective': 'Apresentação',
                    'target': 'scene_05_presentation',
                    'narration_text': 'Cursos GRATUITOS. Nossos cursos possuem uma versão gratuita com conteúdo de alta qualidade e é um curso completo.',
                    'use_avatar': False,
                },
                {
                    'can_be_random': False,
                    'objective': 'Apresentação',
                    'target': 'scene_06_presentation',
                    'narration_text': 'Importante é a JORNADA! Pensamos a jornada do seu desenvolvimento pessoal e profissional com cursos online, rápidos e diretos, e não cursos de 80 horas',
                    'use_avatar': False,
                },
                {
                    'can_be_random': False,
                    'objective': 'Apresentação',
                    'target': 'scene_07_presentation',
                    'narration_text': 'Quer acompanhar seu PROGRESSO? Descubra sua posição e chegue no ranking dos melhores do mercado!',
                    'use_avatar': False,
                },
                {
                    'can_be_random': False,
                    'objective': 'Apresentação',
                    'target': 'scene_08_presentation',
                    'narration_text': 'Sozinho não se vai LONGE! Aqui, temos especialistas para te ajudar a explorar novos caminhos e com certificado ao fim do curso',
                    'use_avatar': False,
                },
                {
                    'can_be_random': False,
                    'objective': 'Apresentação',
                    'target': 'scene_09_presentation',
                    'narration_text': 'Tem que ser do SEU JEITO! Escolher os capítulos do curso? Básico, intermediário ou avançado? Isso, e muito mais, vai deixar seu estudo prazeroso aqui.',
                    'use_avatar': False,
                },
                {
                    'can_be_random': False,
                    'objective': 'Conclusão',
                    'target': 'scene_01_conclusion',
                    'narration_text': 'Não ACREDITA? Explore novas formas de aprender, continue na busca por melhorar sua jornada, e deixe-nos te apoiar nesse caminho! Um grande abraço!',
                    'use_avatar': True,
                },
                {
                    'can_be_random': False,
                    'objective': 'Assinatura',
                    'target': 'scene_brand_signature',
                }
            ]
        },
        "Template C - Youtube": {
            "vars": ["course_name", "current_job", "area", "topic01", "topic02", "topic03", "topic04", "youtube_channel_name"],
            "script": [
            {
                "use_avatar": False,
                "narration_text":"Curso online grátis de {course_name}",
                "target": "scene_01_intro", 
                "objective": "Introdução",
                "text_1": "{course_name}"
            },
            {
                "use_avatar": False,
                 "narration_text":"Todos nossos cursos possuem uma versão grátis completa e de alta qualidade!",
                 "target": "scene_02_intro", 
                 "objective": "Introdução"
            },
            {
                "use_avatar": True, 
                "narration_text":"Além disso, eles possuem especialistas no conhecimento que você está buscando e também são personalizados para entender exatamente o que você busca, com casos práticos, conteúdos específicos e os capítulos que você escolher.",
                "target": "scene_03_intro", 
                "objective": "Introdução"
            },
            {
                "use_avatar": False,
                 "narration_text":"Você nunca viu uma plataforma de cursos assim!",
                 "target": "scene_04_intro", 
                 "objective": "Introdução"
            },
            {
                "use_avatar": True, 
                "narration_text":"Meu nome é {instructor_name}, atualmente sou {current_job} e especialista aqui na Apoia.",
                "target": "scene_05_mentor", 
                "objective": "Mentor",
                "text_1": "{instructor_name}",
                "text_2": "Especialista de {area}"
            },
            {
                "use_avatar": False,
                 "narration_text":"Na Apoia, acreditamos em 5 pilares:",
                 "target": "scene_06_pillars", 
                 "objective": "Apresentação"
            },
            {
                "use_avatar": False,
                 "narration_text":"Cursos gratuitos! Os cursos possuem uma versão gratuita completa e de alta qualidade.",
                 "target": "scene_07_pillars", 
                 "objective": "Apresentação"
            },
            {
                "use_avatar": False,
                 "narration_text":"Cursos online rápidos e diretos, organizados em uma jornada para seu sucesso profissional e pessoal",
                 "target": "scene_08_pillars", 
                 "objective": "Apresentação"
            },
            {
                "use_avatar": False,
                 "narration_text":"Quer acompanhar seu progresso? Descubra sua posição e chegue no ranking dos melhores do mercado!",
                 "target": "scene_09_pillars", 
                 "objective": "Apresentação"
            },
            {
                "use_avatar": False,
                 "narration_text":"Especialistas para te ajudar a explorar novos caminhos. Certificado ao fim do curso",
                 "target": "scene_10_pillars", 
                 "objective": "Apresentação"
            },
            {
                "use_avatar": False,
                 "narration_text":"Personalizado, com escolha de capítulos, diferentes níveis (básico, intermediário e avançado) e conteúdo escolhido e produzido apenas para você.",
                 "target": "scene_11_presentation", 
                 "objective": "Apresentação"
            },
            {
                "use_avatar": True, 
                "narration_text":"Eu sou um dos especialistas do curso de {course_name} na Apoia e nesse curso queremos {course_objective}. E para isso vamos cobrir o seguintes tópicos no curso:",
                "target": "scene_12_presentation", 
                "objective": "Apresentação"
            },
            {
                "use_avatar": False,
                "narration_text":"{topic01} ... {topic02} ... e também {topic03}.",
                "target": "scene_13_topics", 
                "objective": "Apresentação",
                "text_1": "{course_name}",
                "text_2": "{topic01}",
                "text_3": "{topic02}",
                "text_4": "{topic03}",
                "text_5": "{topic04}",
            },
            {
                "use_avatar": True, 
                "narration_text":"E não esqueça de seguir a gente para receber conteúdo gratuito relevante para sua profissão ou interesses pessoais e dar um like no vídeo para nos apoiar. Visite o nosso site, no link abaixo, para fazer seu primeiro curso!",
                "target": "scene_14_conclusion", 
                "objective": "Conclusão",
                "text_1": "Curso de {course_name}",
                "text_2": "{youtube_channel_name}",
            },
            {
                "use_avatar": True, 
                "narration_text":"Explore novas formas de aprender, continue na busca por melhorar sua jornada, e deixe-nos te apoiar nesse caminho! Grande abraço",
                "target": "scene_15_conclusion", 
                "objective": "Conclusão"
            },
            {
                "target": "scene_16_brand_signature", 
                "objective": "Assinatura"
            },
        ]},
    }




class YoutubeVideo:

    config = dict(
        student_industry = 'Genérico',
        professional_area = 'Genérico',
        student_position = 'Genérico',
        course_name = 'Genérico',
    )

    script_object = {
        'can_be_random': False,
        'objective': '',
        'target': '',
        'narration_text': '',
        'narration_audio_url': '',
        'use_avatar': False,
        'avatar_video_url': '',
        'title_a': '',
        'text_1': '',
        'text_2': '',
        'text_3': '',
        'text_4': '',
        'images_length': 0,
        'image_1_url': '',
        'image_2_url': '',
        'image_3_url': '',
        'question_text': '',
        'answer_1_text': '',
        'answer_2_text': '',
        'answer_3_text': '',
        'answer_4_text': '',
        'correct_answer_text': '',
        'correct_answer_number': '',
        'correct_letter_image_url': '',
        'narration_answer_text': '',
        'narration_answer_audio_url': '',
    }

    def __init__(self, onboarding):
        self.client = OpenAI(api_key = settings.OPENAI_API_KEY )
        self.config.update(onboarding)
        self.template = self.config['template_selected']

    def run(self):
        return self.setup_intro_scene()

    def setup_intro_scene(self) -> List[dict]:
        # INTRODUÇÃO RESUMO CURSO - TEMPLATE
        scene_intro_overview_list = []
        for template_dict in self.template:
            scene_intro_overview = self.script_object.copy()
            scene_intro_overview['target'] = template_dict['target']
            scene_intro_overview['objective'] = template_dict['objective']
            scene_intro_overview['narration_text'] = template_dict.get('narration_text', '').format_map(self.config)
            scene_intro_overview['text_1'] = template_dict.get('text_1', '').format_map(self.config)
            scene_intro_overview['text_2'] = template_dict.get('text_2', '').format_map(self.config)
            scene_intro_overview['text_3'] = template_dict.get('text_3', '').format_map(self.config)
            scene_intro_overview['text_4'] = template_dict.get('text_4', '').format_map(self.config)
            scene_intro_overview['images_length'] = template_dict.get('images_length', 0)
            scene_intro_overview['image_1_url'] = template_dict.get('image_1_url', '').format_map(self.config)
            scene_intro_overview['image_2_url'] = template_dict.get('image_2_url', '').format_map(self.config)
            scene_intro_overview['image_3_url'] = template_dict.get('image_3_url', '').format_map(self.config)
            scene_intro_overview['title_a'] = template_dict.get('title_a', '').format_map(self.config)
            scene_intro_overview['use_avatar'] = template_dict.get('use_avatar', '')
            scene_intro_overview_list.append(scene_intro_overview)
        return scene_intro_overview_list

    def generate_audio_files(self, scenes: List[dict], voice_id="rVYXh5OmQcvchhNYtBWe", model_id="eleven_multilingual_v2", stability=0.48, similarity_boost=0.55, style=0.00) -> List[dict]:
        print('Generating audio')

        def generate_audio_for_scene(scene):
            if scene['narration_text']:
                scene['narration_audio_url'] = self.generate_audio_file_and_upload(scene['narration_text'], voice_id, model_id, stability, similarity_boost, style)

            if scene['narration_answer_text']:
                scene['narration_answer_audio_url'] = self.generate_audio_file_and_upload(scene['narration_answer_text'], voice_id, model_id, stability, similarity_boost, style)

        # with ThreadPoolExecutor() as executor:
        #     list(executor.map(generate_audio_for_scene, scenes))

        # generating audio files
        for scene in tqdm(scenes):
            generate_audio_for_scene(scene)

        return scenes

    def generate_audio_file_and_upload(self, narration_text, voice_id="rVYXh5OmQcvchhNYtBWe", model_id="eleven_multilingual_v2", stability=0.48, similarity_boost=0.55, style=0.00):

        audio_data = fetch_narration_in_memory(narration_text, voice_id, stability, similarity_boost, style, model_id)
        # audio_url = upload_object_in_memory_to_s3(audio_data, f'narration/{voice_id}__{stability}__{similarity_boost}__{style}__{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.mp3')
        audio_url = upload_object_in_memory_to_s3(audio_data, f'narration/{uuid.uuid4()}.mp3')

        return audio_url

    def generate_avatar_files(self, scenes: List[dict], avatar_id='bd89c0388a9444e49183cb6ec919547d', is_teste=False) -> List[dict]:
        print('Generating avatares')

        def generate_avatar_for_scene(scene):
            if scene['use_avatar']:
                audio_url = scene['narration_audio_url']
                result = generate_avatar_heygen_with_audio_file(audio_url=audio_url, avatar_id=avatar_id, is_teste=is_teste)
                print(result)
                video_id = result[1]['data']['video_id']
                result = get_generated_avatar_heygen(video_id)

                while result[1]['data']['status'] != 'completed':
                    time.sleep(10)
                    print(result)
                    result = get_generated_avatar_heygen(video_id)

                video_url = result[1]['data']['video_url']
                # video_url = upload_object_in_memory_to_s3(audio_data, f'narration/{uuid.uuid4()}.mp3')
                print(f"Avatar {scene['target']}: {video_url}")
                scene['avatar_video_url'] = video_url

        # with ThreadPoolExecutor() as executor:
        #     list(executor.map(generate_avatar_for_scene, scenes))

        # generating avatar files
        for scene in tqdm(scenes):
            generate_avatar_for_scene(scene)

        return scenes

    def cot_chapters_narration_and_image_suggestion(self, ) -> List[dict]:
        with open('prompts/cot_chapters_narration_and_image_suggestion.txt', 'r') as file:
            message = file.read()
        message = message.format_map(self.config)
        result = self.chat_complete(message)
        return self.parse_json_to_dict(result)['scene']

    def cot_video_texts(self, narration_script) -> List[dict]:
        with open('prompts/cot_video_texts.txt', 'r') as file:
            message = file.read()
        message = message.format(narration_script=narration_script)
        result = self.chat_complete(message)
        return self.parse_json_to_dict(result)['narration']

    def cot_quiz_questions(self, ) -> List[dict]:
        with open('prompts/cot_quiz_questions.txt', 'r') as file:
            message = file.read()
        message = message.format_map(self.config)
        result = self.chat_complete(message)
        return self.parse_json_to_dict(result)['quiz_list']

    def clean_json_string(self, json_string):
        pattern = r'^```json\s*(.*?)\s*```$'
        cleaned_string = re.sub(pattern, r'\1', json_string, flags=re.DOTALL)
        return cleaned_string.strip()

    def parse_json_to_dict(self, json_string):
        cleaned_string = self.clean_json_string(json_string)
        return json.loads(cleaned_string)

    def get_completion(self, messages, model="gpt-3.5-turbo", temperature=0):
        response = self.client.chat.completions.create(
            model=model,
            response_format={ "type": "json_object" },
            messages=messages
        )
        return response.choices[0].message.content

    def chat_complete(self, system_prompt, model="gpt-3.5-turbo", temperature=0) -> str:
        messages = [
            {"role":"system", "content": system_prompt},
        ]
        return self.get_completion(messages, model, temperature)
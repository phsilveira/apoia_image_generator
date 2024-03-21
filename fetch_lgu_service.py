
import json
import re
from openai import OpenAI
import pandas as pd
import requests
import settings
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
from pytube import YouTube
from bs4 import BeautifulSoup


class FetchYoutubeLGU():
    
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


    def __init__(self, course_summary=None):
        if course_summary:
            self.course_summary = course_summary
        self.client = OpenAI(api_key = settings.OPENAI_API_KEY )
        genai.configure(api_key=settings.GEMINI_API)
        self.model = genai.GenerativeModel('gemini-pro')


    def search_youtube_videos_with_keywords_and_channels(self):

        df = self.convert_dict_summary_to_df(self.course_summary)
        curated_youtube_channels = self.search_youtube_channels(course_name=self.course_summary["course_name"])

        df['keywords'] = None

        for index, row in df.iterrows():
            print(f'{index}/{len(df)}')

            print('getting keywords for:', row['chapter_name'], row['section_name'], row['subsection_name'])
            keywords = self.generate_keyword_for_section_and_subsection(row['chapter_name'], row['section_name'], row['subsection_name']) #adicionar novas linguas
            json_str = self.extract_json_from_text(keywords)

            if json_str:
                try:
                    df.at[index, 'keywords'] = json_str
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON: {e}")
            else:
                print("No valid JSON found in the string.")

            print('searching youtube channels and videos for:', row['chapter_name'], row['section_name'], row['subsection_name'])
            # curated_youtube_channels = self.search_youtube_channels(course_name=self.course_summary["course_name"])
            keywords_json = json.loads(json_str)

            for language, youtube_channels in curated_youtube_channels.items():
                keyword = keywords_json[f'search_keywords_{language.lower()}']
                for channel in youtube_channels:

                    if channel['exists']:
                        query = f"{keyword} channel: {channel['channel_name']}"

                        #Search with google cse
                        print(f"Searching videos for {query} in {language}")
                        try:
                            search_results = self.seach_youtube_videos_using_google_cse(query, num=5)
                            items = search_results.get('items', [])
                        except Exception as e:
                            print(f"Erro ao buscar vídeos: {e}")
                            items = []

                        # curate
                        print(f"Curating {len(items)} videos for {query} in {language}")
                        for item in items:
                            item['curation'] = self.generate_lgu_curation(item['snippet'], self.course_summary['course_name'], row['chapter_name'], row['section_name'])
                            

                        df.at[index, f'youtube_{language.lower()}_results'] = json.dumps(items)

        return df

    def generate_lgu_curation(self, content, course_name, chapter, section):
        prompt = f"""instruction:
        Acting as a researcher, very detailed, dedicated, and with the goal of investigating possible content objects that can be used for learning.
        Considering the keywords of that section {section} of the chapter {chapter} of the course {course_name}, understand the relevance and specitifity of this content to be an object of a course involving the keywords.
        Give a rating, between 0 and 5, in terms of relevance and specificity of the content to the keywords, be very strict in giving the rating. It's okay if most of the ratings are below 3.
        content:
        ```
        {content}
        ```

        return in the following json structure, PAY ATTENTION FOR SPECIAL CHAR like " or ' if they appear, use the scape
        {{"relevance_score": 0, "explanation_relevance": "the content provided...", "specificity_score": 0, "explanation_specificity": "the content provided..."}}"""
        messages = [
            {"role": "system", "content": prompt},
        ]

        result = self.get_completion(messages)
        
        return json.loads(result)
        
    def search_youtube_channels(self, course_name):
        course_keyword = self.generate_keyword_for_course_name(course_name)
        youtube_languages = {"English", "Portuguese", "Spanish"} 
        curated_youtube_channels = {}

        for language in youtube_languages:
            curated_youtube_channels[language] = self.search_youtube_sources_using_gemini(course_keyword, language)
        
        for language, channels in curated_youtube_channels.items():
            for channel in channels:
                channel_url = f"https://www.youtube.com/@{channel['username']}"
                if self.youtube_channel_exists(channel_url):
                    channel["channel_url"] = channel_url
                    channel["exists"] = True
                else:
                    channel["channel_url"] = None
                    channel["exists"] = False

        return curated_youtube_channels

    def generate_keyword_for_course_name(self, course_name):
        context = "You are a advertising and marketing professional, working on keywords for course names."
        prompt = f"""As a dedicated, rigorous, and detail-oriented advertising and marketing professional. I'm working on transforming a course name that is in Portuguese into search keywords in English.
        Example 1:
        - Course name: Curso de Gestão de Projetos em Recursos Humanos
        - Search Keyword: Project Managment
        Example 2:
        - Course name: Fotografia de Festas e Formaturas
        - Search Keyword: Event Photography
        Request:
        Based on the criteria above, please return me only the search keyword for this course name: {course_name}. Never remember or mention what my request was to you in the output.
        """

        model="gpt-4"
        messages=[
            {"role": "system", "content": f"{context}"},
            {"role": "user", "content": f"{prompt}"}
        ]
        temperature=0

        return self.get_completion(messages, model, temperature)
    
    def search_youtube_sources_using_gemini(self, theme, language):



        prompt = f'Give me a list of 20 youtube creators with their channels names and usernames to learn more about {theme} in {language}. Please return in a list with JSONs with the keys "channel_name" and "username"'

        response = self.model.generate_content(prompt)

        sources = []

        try:
            json_response = response.text.strip("```json\n").rstrip("```")
            sources = json.loads(json_response)
        except Exception as e:
            print(f'{type(e).__name__}: {e}')

        return sources

    def generate_keyword_for_section_and_subsection(self, chapter, section, subsection):
        context = "You are a advertising and marketing professional, working on keywords for searching online content."
        prompt = f"""As a dedicated, rigorous, and detail-oriented advertising and marketing professional. I'm working on extracting search keywords that work better in search engines from a provided text.
        After extracting keywords, we must translate them into English and Spanish to search in those languages.
        The keywords must be specific so we can find the right content about it in search results. The first part of the content text is the most important, the other two sections only provide you more context.
            Example 1:
            - Content: Estratégias de Engajamento - Identificação e Gestão de Stakeholders - Gestão de Stakeholders
            - Search Keyword Portuguese: Engajamento de Stakeholders
            Example 2:
            - Content: SEO e Presença Online - Estratégias de Marketing Digital e Redes Sociais - Marketing para Fotógrafos
            - Search Keyword Portuguese: SEO e Marketing para Fotógrafos
            Example 3:
            - Content: Loops e Condições - Sintaxe e Estruturas de Controle	- JavaScript Básico
            - Search Keyword Portuguese: Loops e Condições em JavaScript
            Example 4:
            - Content: História e Evolução - Introdução à Gestão de Projetos - Fundamentos de Gestão de Projetos
            - Search Keyword Portuguese: História da Gestão de Projetos
        Request:
        Based on the criteria and examples above, please return me the search keywords for this content: {subsection} - {section} - {chapter}.
        The output must be in JSON format as the following example:
        ```{{
            "search_keywords_portuguese": "Engajamento de Stakeholders",
            "search_keywords_english": "Stakeholder Engagement",
            "search_keywords_spanish": "Compromiso de los Stakeholders",
        }}```
        Never remember or mention what my request was to you in the output, return just the JSON without any other text.
        """

        model="gpt-4"
        messages=[
            {"role": "system", "content": f"{context}"},
            {"role": "user", "content": f"{prompt}"}
        ]

        return self.get_completion(messages, model, )

    def generate_summary_for_transcript(self, transcript):
        limited_transcript = transcript[:4000]
        context = f"""You are a recruter specialist who is reviewing segments of text books, video transcriptions

        transcript/text: {limited_transcript}

        take a deep breath and classify this transcript in this labels:

        \"keywords\": \"keywords of the content segment\",
        \"summary\": \"summary of the content segment\"

        return in the same json format above, pay attention for special characters, if needed use scape chars, for example \"

        """

        model="gpt-3.5-turbo"
        messages=[
            {"role": "system", "content": f"{context}"},
        ]

        return self.get_completion(messages, model, )

    def seach_youtube_videos_using_google_cse(self, query, filter=1, num=5):
        api_key = settings.GOOGLE_API_KEY
        cse_id = "8484226ec257e4347"

        url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={api_key}&cx={cse_id}&filter={filter}&num={num}"

        response = requests.get(url)
        results = response.json()
        return results

    def extract_json_from_text(self, text):
        match = re.search(r'(?s)\{.*\}', text)
        if match:
            return match.group(0)
        else:
            return None

    def get_youtube_video_id(self, url):
        regex = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'

        match = re.search(regex, url)
        if match:
            return match.group(1)
        else:
            return None

    def youtube_channel_exists(self, channel_url):
        try:
            response = requests.get(channel_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            channel_name = soup.find('meta', itemprop='name')['content']
            if channel_name.strip() == "YouTube":
                return False
            else:
                return True
        except Exception as e:
            print("An error occurred:", e)
            return False

    def get_video_info(self, video_id):

        # get snippet
        params = {
            'part': 'snippet',
            'id': video_id,
        }

        try:
            response = requests.get('https://yt.lemnoslife.com/noKey/videos', params=params)
            items = response.json().get('items')

            if items and len(items) > 0:
                video_info = items[0]

                video_info['id'] = video_id
            else:
                print(f"No snippet found for video ID {video_id}.")
                return None

        except Exception as e:
            print(f"Error fetching video snippet for {video_id}: {e}")
            return None

        # get info chapters and duration
        params = {
            'part': 'id,status,contentDetails,clip,chapters',
            'id': video_id,
        }

        try:
            response = requests.get('https://yt.lemnoslife.com/videos', params=params)
            items = response.json().get('items')

            if items and len(items) > 0:
                video_info_extension = items[0]

                video_info['chapters'] = video_info_extension.get('chapters', [])
                video_info['contentDetails'] = video_info_extension.get('contentDetails', {})
            else:
                print(f"No chapters and duration found for video ID {video_id}.")

        except Exception as e:
            print(f"Error fetching chapters and duration for {video_id}: {e}")


        # get # views

        try:
            youtube_video = YouTube(f"https://www.youtube.com/watch?v={video_id}")
            video_info['views'] = youtube_video.views
        except Exception as e:
            print(f"Error fetching video views for {video_id}: {e}")
            video_info['views'] = None


        # get transcription
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
            video_info['transcription'] = transcript
        except Exception as e:
            print(f'problem with subtitle in {video_id}')
            video_info['transcription'] = {}


        return video_info


    def convert_dict_summary_to_df(self, summary: dict) -> pd.DataFrame:
        flattened_data = []

        for chapter in summary["chapters"]:
            chapter_name = chapter["chapter_name"]
            for section in chapter["sections"]:
                section_name = section["section_name"]
                for subsection in section["subsections"]:
                    row = {
                        "course_name": summary["course_name"],
                        "chapter_name": chapter_name,
                        "section_name": section_name,
                        "subsection_name": subsection
                    }
                    flattened_data.append(row)

        return pd.DataFrame(flattened_data)

    def get_completion(self, messages, model="gpt-3.5-turbo", temperature=0):
        response = self.client.chat.completions.create(
            model=model,
            #response_format={ "type": "json_object" },
            messages=messages,
            temperature=temperature
        )
        return response.choices[0].message.content

    def chat_complete(self, system_prompt, model="gpt-3.5-turbo", temperature=0) -> str:
        messages = [
            {"role":"system", "content": system_prompt},
        ]
        return self.get_completion(messages, model, temperature)
    
    
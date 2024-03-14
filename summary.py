import json
from openai import OpenAI
import settings
import pandas as pd

class Summary:

    onboarding = {
        "course_type": "professional",
        "student_name": "Marco",
        "course_theme": "Gestão de Projetos",
        "course_area": "Finanças",
        "student_objective": "",
        "student_role_desired": "Junior",
        "student_industry": "Bancário",
        "student_proficiency": ""
    }

    prompt_paths = {
        "general_cot_prompt_3": "prompts/summary/cot_general_summary_prompt_3.txt",
        "hobby": {
            "context_prompt_path": "prompts/summary/hobby/context.txt",
            "summary_prompt_1_prompt_path": "prompts/summary/hobby/cot_summary_prompt_1.txt",
            "summary_prompt_2_prompt_path": "prompts/summary/hobby/cot_summary_prompt_2.txt",
        },
        "language": {
            "context_prompt_path": "prompts/summary/language/context.txt",
            "summary_prompt_1_prompt_path": "prompts/summary/language/cot_summary_prompt_1.txt",
            "summary_prompt_2_prompt_path": "prompts/summary/language/cot_summary_prompt_2.txt",
        },
        "professional": {
            "context_prompt_path": "prompts/summary/professional/context.txt",
            "summary_prompt_1_prompt_path": "prompts/summary/professional/cot_summary_prompt_1.txt",
            "summary_prompt_2_prompt_path": "prompts/summary/professional/cot_summary_prompt_2.txt",
        },
        "self_employed": {
            "context_prompt_path": "prompts/summary/self_employed/context.txt",
            "summary_prompt_1_prompt_path": "prompts/summary/self_employed/cot_summary_prompt_1.txt",
            "summary_prompt_2_prompt_path": "prompts/summary/self_employed/cot_summary_prompt_2.txt",
        },
    }

    def __init__(self, **kwargs):
        self.onboarding.update(kwargs)
        self.client = OpenAI(api_key = settings.OPENAI_API_KEY )

    def generate_summary_and_final_project(self) -> tuple[dict, str]:
        final_project = self.generate_course_final_project()
        course_outline = self.generate_course_outline(final_project)
        course_summary = self.generate_course_summary(course_outline)
        course_summary_dict = self.parse_completion_str_to_dict(course_summary)
        return course_summary_dict, final_project
    
    def generate_complete_course(self):
        final_project = self.generate_course_final_project()
        course_outline = self.generate_course_outline(final_project)
        course_summary = self.generate_course_summary(course_outline)

        final_course = {
            "onboarding": self.onboarding,
            "final_project": final_project,
            "course_summary": self.parse_completion_str_to_dict(course_summary)
        }

        return final_course

    def generate_course_final_project(self):
        prompt_paths = self.prompt_paths.get(self.onboarding['course_type'])
        return self.get_completion(
            self.open_file(prompt_paths['context_prompt_path']), 
            self.open_file(prompt_paths['summary_prompt_1_prompt_path']).format(**self.onboarding)
        )

    def generate_course_outline(self, final_project):
        prompt_paths = self.prompt_paths.get(self.onboarding['course_type'])
        return self.get_completion(
            self.open_file(prompt_paths['context_prompt_path']), 
            self.open_file(prompt_paths['summary_prompt_2_prompt_path']).format(final_project=final_project, **self.onboarding)
        )

    def generate_course_summary(self, course_outline):
        prompt_paths = self.prompt_paths.get(self.onboarding['course_type'])
        prompt_general_cot_prompt_3 = self.prompt_paths['general_cot_prompt_3']
        return self.get_completion(
            self.open_file(prompt_paths['context_prompt_path']), 
            self.open_file(prompt_general_cot_prompt_3).format(course_outline=course_outline, **self.onboarding)
        )

    def get_completion(self, context, prompt, model='gpt-4'): 
        response = self.client.chat.completions.create(
            model = model,
            # response_format = { "type": "json_object" },
            messages = [
                {"role": "system", "content": f"{context}"},
                {"role": "user", "content": f"{prompt}"}
            ],
        )
        return response.choices[0].message.content
    
    def open_file(self, file_path):
        with open(file_path, 'r') as file:
            return file.read()
    
    def parse_completion_str_to_dict(self, completion):
        return json.loads(completion)
    
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

    def __str__(self):
        return f'{self.name}: {self.value}'

    def __repr__(self):
        return f'{self.name}: {self.value}'
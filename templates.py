import promptlayer
import settings 
from openai import OpenAI

promptlayer.api_key = settings.PROMPTLAYER

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

def chatgpt_chat_completion_with_prompt(payload, prompt_template, model="gpt-3.5-turbo"):
    prompt = prompt_template.format(**payload)

    client = OpenAI()

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    print(completion.choices[0].message.content)
    return completion.choices[0].message.content

    

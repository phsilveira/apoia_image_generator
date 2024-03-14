from openai import OpenAI
import settings


class LLMService:
    
    def __init__(self, model="gpt-3.5-turbo", temperature=0):
        self.client = OpenAI(api_key = settings.OPENAI_API_KEY )
        self.model = model
        self.temperature = temperature
    
    def get_completion(self, messages, response_format={ "type": "json_object" }):
        response = self.client.chat.completions.create(
            model=self.model,
            response_format=response_format,
            messages=messages
        )
        return response.choices[0].message.content

    def chat_complete(self, system_prompt, ) -> str:
        messages = [
            {"role":"system", "content": system_prompt},
        ]
        return self.get_completion(messages, )
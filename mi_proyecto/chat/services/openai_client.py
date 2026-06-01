from django.conf import settings
from openai import (
    APIConnectionError,
    APIStatusError,
    OpenAI,
    RateLimitError,
)


class OpenAIChatClient:
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise RuntimeError('OPENAI_API_KEY no esta configurada')

        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

    def create_response(self, messages):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_completion_tokens=600,
            )
        except RateLimitError:
            return 'Estoy recibiendo muchas solicitudes. Intenta nuevamente en unos segundos.'
        except APIConnectionError:
            return 'No pude conectarme al servicio de IA. Intenta nuevamente.'
        except APIStatusError:
            return 'El servicio de IA no pudo procesar la solicitud.'

        return response.choices[0].message.content

    def generate_title(self, message):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': 'Genera un título muy corto (máximo 5 palabras) en español que resuma el tema principal de este mensaje. Responde solo con el título, sin puntuación ni comillas.'},
                    {'role': 'user', 'content': message},
                ],
                temperature=0.3,
                max_completion_tokens=20,
            )
            title = response.choices[0].message.content.strip().strip('"').strip("'")
            return title[:60]
        except Exception:
            return ''

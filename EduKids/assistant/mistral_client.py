"""
Client minimal pour appeler l'API Mistral (abstraction).

Remarques:
- Lit la clé d'API depuis la variable d'environnement MISTRAL_API_KEY.
- L'URL de l'API peut être configurée via MISTRAL_API_URL.
- Le format de la réponse de Mistral peut varier; ce client tente de gérer le streaming via
  response.iter_lines() si l'endpoint le propose.

Important: NE PAS committer la clé dans le dépôt. Stocker dans les variables d'environnement.
"""
import os
import requests
from typing import Generator, Optional

MISTRAL_API_KEY = os.environ.get('MISTRAL_API_KEY')
MISTRAL_API_URL = os.environ.get('MISTRAL_API_URL', 'https://api.mistral.ai/v1/chat/completions')


class MistralClient:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or MISTRAL_API_KEY
        self.base_url = base_url or MISTRAL_API_URL
        if not self.api_key:
            raise RuntimeError('MISTRAL_API_KEY not set in environment')

    def stream_generate(self, prompt: str, system: str = '', language: str = 'fr') -> Generator[str, None, None]:
        """Appelle l'API Mistral et yield des morceaux de texte pour le streaming.

        Note: le comportement exact dépend de l'endpoint Mistral. Cette implémentation
        essaie `response.iter_lines()` pour consommer les chunks envoyés en chunked transfer.
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

        payload = {
            'model': 'mistral-medium',  # or mistral-small, etc.
            'messages': [
                {'role': 'system', 'content': system} if system else None,
                {'role': 'user', 'content': prompt}
            ],
            'stream': True,
            # d'autres paramètres peuvent être ajoutés: temperature, max_tokens, top_p, etc.
        }
        if not system:
            payload['messages'] = payload['messages'][1:]

        try:
            with requests.post(self.base_url, json=payload, headers=headers, stream=True, timeout=30) as r:
                r.raise_for_status()
                # Stream line-delimited JSON or plain text chunks
                for line in r.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    line = line.strip()
                    if line.startswith('data: '):
                        line = line[6:]  # remove 'data: '
                    if not line or line == '[DONE]':
                        continue
                    # tenter de décoder JSON sinon renvoyer la ligne brute
                    try:
                        import json
                        piece = json.loads(line)
                        # For chat/completions API
                        if isinstance(piece, dict) and 'choices' in piece:
                            choice = piece['choices'][0]
                            if 'delta' in choice and 'content' in choice['delta']:
                                yield choice['delta']['content']
                            elif 'text' in choice:  # fallback
                                yield choice['text']
                        elif 'text' in piece:  # old format
                            yield piece['text']
                        elif 'delta' in piece:
                            # delta peut être dict ou str
                            d = piece['delta']
                            if isinstance(d, dict) and 'content' in d:
                                yield d['content']
                            elif isinstance(d, str):
                                yield d
                            else:
                                # yield the whole JSON as fallback
                                yield json.dumps(piece)
                        else:
                            yield str(piece)
                    except Exception:
                        # not JSON — yield raw chunk
                        yield line
        except Exception as e:
            # On erreur, yield une réponse d'erreur lisible (ne pas exposer la clé)
            yield f"[error contacting mistral: {str(e)}]"


def get_client() -> MistralClient:
    return MistralClient()

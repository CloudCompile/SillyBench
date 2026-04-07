import json
import urllib.request
import urllib.error

class PollinationsAPI:
    def __init__(self, api_key="sk_KqMTtO5Ax8A3UG5u72IANvoUd2OVl8jn", base_url="https://gen.pollinations.ai/v1/chat/completions"):
        self.api_key = api_key
        self.base_url = base_url

    def call(self, model, messages, temperature=0.7, max_tokens=2000):
        # For Pollinations, you typically do a POST to /openai
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "curl/8.5.0"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        req = urllib.request.Request(self.base_url, headers=headers, data=json.dumps(data).encode('utf-8'))
        
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                if 'choices' in result and len(result['choices']) > 0:
                    return result['choices'][0]['message']['content']
                return ""
        except urllib.error.URLError as e:
            print(f"API Error: {e}")
            return None

class OpenAICompatibleAPI:
    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url

    def call(self, model, messages, temperature=0.7, max_tokens=2000):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "curl/8.5.0"
        }

        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        req = urllib.request.Request(self.base_url, headers=headers, data=json.dumps(data).encode('utf-8'))
        
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                if 'choices' in result and len(result['choices']) > 0:
                    return result['choices'][0]['message']['content']
                return ""
        except urllib.error.URLError as e:
            print(f"API Error: {e}")
            return None

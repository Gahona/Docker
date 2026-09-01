from abc import ABC, abstractmethod
import requests


class ServicioLLM(ABC):
    @abstractmethod
    def generar_respuesta(self, messages: list[dict]) -> str:
        raise NotImplementedError    

    
class ClientEactda:
    def __init__(
            self,
            base_url: str = "http://192.168.1.147:1234/v1",
            model: str = "qwen2.5-7b-instruct",
            timeout: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        
        
    def chat(self, messages: list[dict], temperature: float = 0.4, max_tokens: int = 150) -> str:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        response = requests.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


class EactdaLLMService(ServicioLLM):
    def __init__(self, base_url: str = "http://192.168.1.147:1234/v1", model: str = "qwen2.5-7b-instruct"):
        self.client = ClientEactda(base_url=base_url, model=model)
    
    def generar_respuesta(self, messages : list[dict]) -> str:
        return self.client.chat(messages)
    
class MockServicioLLM(ServicioLLM):
    def __init__(self, respuesta_corregidas: str = "Esta es una respuesta simulada."):
        self.respuesta_corregidas = respuesta_corregidas
    
    def generar_respuesta(self, messages: list[dict]) -> str:
        return self.respuesta_corregidas
    
def get_servicio_llm() -> ServicioLLM:
    USE_MOCK = True
    
    if USE_MOCK:
        return MockServicioLLM()
    return EactdaLLMService()
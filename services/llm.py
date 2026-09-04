from abc import ABC, abstractmethod
from decimal import Decimal
import requests
import asyncio
import httpx

PRICE_PER_1K_PROMPT_TOKENS = Decimal("0.0015")
PRICE_PER_1K_COMPLETION_TOKENS = Decimal("0.0020")


def calcular_coste(prompt_tokens: int, completion_tokens: int) -> Decimal:
    coste_prompt = (Decimal(prompt_tokens) / Decimal(1000)) * PRICE_PER_1K_PROMPT_TOKENS
    coste_completion = (Decimal(completion_tokens) / Decimal(1000)) * PRICE_PER_1K_COMPLETION_TOKENS
    return round(coste_prompt + coste_completion, 6)


class ServicioLLM(ABC):
    @abstractmethod
    def generar_respuesta(self, messages: list[dict]) -> dict:
        raise NotImplementedError

    @abstractmethod
    async def generar_respuesta_async(self, messages: list[dict]) -> dict:
        raise NotImplementedError

    @abstractmethod
    async def generar_respuesta_stream(self, messages: list[dict]):
        raise NotImplementedError
        yield


class ClientEactda:
    def __init__(
            self,
            base_url: str = "http://192.168.1.147:1234/v1",
            model: str = "qwen2.5-7b-instruct",
            timeout: float = 30.0,
            max_intentos: int = 3,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.max_intentos = max_intentos

    def _payload(self, messages, temperature, max_tokens):
        return {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

    def _extraer_respuesta_y_usage(self, data: dict) -> dict:
        texto = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        
        return {
            "respuesta": texto,
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        }

    def chat(self, messages: list[dict], temperature: float = 0.4, max_tokens: int = 150) -> dict:
        url = f"{self.base_url}/chat/completions"
        payload = self._payload(messages, temperature, max_tokens)
        response = requests.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        return self._extraer_respuesta_y_usage(response.json())

    async def chat_async(self, messages: list[dict], temperature: float = 0.4, max_tokens: int = 150) -> dict:
        url = f"{self.base_url}/chat/completions"
        payload = self._payload(messages, temperature, max_tokens)

        espera = 1
        ultimo_error = None

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for intento in range(1, self.max_intentos + 1):
                try:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    return self._extraer_respuesta_y_usage(response.json())
                except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.RequestError) as exc:
                    ultimo_error = exc
                    if intento == self.max_intentos:
                        break
                    await asyncio.sleep(espera)
                    espera *= 2

        raise ultimo_error


class EactdaLLMService(ServicioLLM):
    def __init__(self, base_url: str = "http://192.168.1.147:1234/v1", model: str = "qwen2.5-7b-instruct"):
        self.client = ClientEactda(base_url=base_url, model=model)

    def generar_respuesta(self, messages: list[dict]) -> dict:
        return self.client.chat(messages)

    async def generar_respuesta_async(self, messages: list[dict]) -> dict:
        return await self.client.chat_async(messages)

    async def generar_respuesta_stream(self, messages: list[dict]):
        raise NotImplementedError("Streaming real con ClientEactda pendiente de implementar")
        yield


class MockServicioLLM(ServicioLLM):
    def __init__(self, respuesta_corregidas: str = "Esta es una respuesta simulada."):
        self.respuesta_corregidas = respuesta_corregidas

    def _construir_mock_payload(self, messages: list[dict]) -> dict:
        total_prompt_chars = sum(len(m.get("content", "")) for m in messages)
        prompt_tokens = max(1, total_prompt_chars // 4)
        completion_tokens = max(1, len(self.respuesta_corregidas) // 4)
        
        return {
            "respuesta": self.respuesta_corregidas,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        }

    def generar_respuesta(self, messages: list[dict]) -> dict:
        return self._construir_mock_payload(messages)

    async def generar_respuesta_async(self, messages: list[dict]) -> dict:
        await asyncio.sleep(0)
        return self._construir_mock_payload(messages)

    async def generar_respuesta_stream(self, messages: list[dict]):
        palabras = self.respuesta_corregidas.split(" ")
        for palabra in palabras:
            await asyncio.sleep(0.3)
            yield palabra + " "


def get_servicio_llm() -> ServicioLLM:
    USE_MOCK = True

    if USE_MOCK:
        return MockServicioLLM()
    return EactdaLLMService()
# Django DRF - Sistema Backend de Chat con LLM (Llama Integration)

Este proyecto es una plataforma backend desarrollada con **Django** y **Django REST Framework (DRF)** que gestiona la comunicación, persistencia de conversaciones y métricas de consumo de modelos de lenguaje (LLM). 

La arquitectura implementa el patrón de diseño **Strategy** para permitir alternar de forma transparente entre una respuesta simulada (*Mock*) para pruebas de integración/desarrollo y un modelo **Llama 3.2** real alojado en local o servidor externo.

---

## 🛠️ Arquitectura y Características Principales

1. **Gestión de Usuarios y Autenticación**:
   - Autenticación por Tokens (`rest_framework.authtoken`).
   - Seguridad por cabeceras (`Authorization: Token <token_key>`).

2. **Gestión de Conversaciones y Mensajes**:
   - Estructura relacional `User -> Conversation -> Message`.
   - Soporte para contexto completo del historial de conversación enviado al modelo en cada interacción.
   - Roles diferenciados: `user` y `assistant`.

3. **Capa LLM Abstraída (Patrón Strategy)**:
   - Clase abstracta `ServicioLLM` que define contratos síncronos, asíncronos y de *streaming*.
   - `MockServicioLLM`: Respuesta simulada sin latencia para desarrollo rápido del frontend.
   - `EactdaLLMService` / `ClientEactda`: Cliente HTTP robusto con reintentos exponenciales y manejo de timeouts que interactúa con un servidor compatible con la API de OpenAI (Ollama, LM Studio, vLLM).

4. **Métricas de Consumo y Costes**:
   - Trazabilidad por mensaje de `prompt_tokens` y `completion_tokens`.
   - Cálculo automático del coste estimado en USD (`cost_usd`).
   - Endpoint de agregación global y por usuario (`/api/usage/summary/`).

---

## 🚀 Requisitos Previos

* **Python**: 3.10+
* **Django**: 4.x / 5.x
* **Servidor LLM Local**: [Ollama](https://ollama.com/) o [LM Studio](https://lmstudio.ai/) (para ejecutar Llama).
* **Git**: Para el control de versiones por ramas (`main` vs `feature/llama-integration`).

---

## 📋 Guía de Instalación y Configuración

### 1. Clonar el repositorio y configurar el entorno

git clone <URL_DE_TU_REPOSITORIO>
cd <NOMBRE_PROYECTO>

# Cambiar a la rama con integración de Llama
git checkout feature/llama-integration

# Crear y activar entorno virtual
python -m venv venv
# En Linux/macOS:
source venv/bin/activate
# En Windows:
venv\Scripts\activate

# Instalación de dependencias
pip install django djangorestframework requests httpx
2. Aplicar Migraciones e Iniciar Servidor Backend
Bash
# Crear migraciones de la base de datos
python manage.py makemigrations

# Aplicar las migraciones
python manage.py migrate

# Crear superusuario / usuario de prueba
python manage.py createsuperuser

# Iniciar servidor Django
python manage.py runserver
🤖 Configuración e Invocación del Modelo Llama
Para utilizar el LLM real en lugar de la simulación:

Pasos en Ollama (Opción recomendada):
Instala Ollama y descarga el modelo Llama 3.2:

Bash
ollama pull llama3.2
Inicia el servicio de Ollama (por defecto sirve en http://localhost:11434):

Bash
ollama run llama3.2
Pasos en llm.py:
Asegúrate de que la función de fábrica tenga USE_MOCK = False:

Python
def get_servicio_llm() -> ServicioLLM:
    USE_MOCK = False  # Activa la invocación al modelo Llama real
    
   if USE_MOCK:
        return MockServicioLLM()
    return EactdaLLMService()
    
🧪 Pruebas del Sistema con Postman
1. Obtener Token de Autenticación
POST http://localhost:8000/api/token-auth/

Body (JSON):

JSON
{
    "username": "admin",
    "password": "tu_password"
}
Respuesta:

JSON
{
    "token": "2a34cf11446a4f9bcbaab9a7ff4a2b926baec52c"
}
2. Configurar Autenticación en Postman
En la pestaña Authorization de tu petición o colección:

Type: API Key

Key: Authorization

Value: Token 2a34cf11446a4f9bcbaab9a7ff4a2b926baec52c

Add to: Header

3. Crear una Conversación
POST http://localhost:8000/api/conversations/

Body (JSON):

JSON
{
    "title": "Prueba Llama 3.2"
}
4. Enviar un Mensaje al LLM
POST http://localhost:8000/api/messages/

Body (JSON):

JSON
{
    "conversation": 1,
    "content": "¿Puedes explicarme brevemente qué es una API REST?"
}
5. Consultar Historial y Respuesta Generada
GET http://localhost:8000/api/conversations/1/

Respuesta esperada:

JSON
{
    "id": 1,
    "title": "Prueba Llama 3.2",
    "messages": [
        {
            "id": 1,
            "role": "user",
            "content": "¿Puedes explicarme brevemente qué es una API REST?"
        },
        {
            "id": 2,
            "role": "assistant",
            "content": "Una API REST (Representational State Transfer) es un estilo de arquitectura..."
        }
    ]
}
6. Consultar Métricas de Consumo
GET http://localhost:8000/api/usage/summary/

Respuesta esperada:

JSON
{
    "user_id": 1,
    "username": "admin",
    "total_prompt_tokens": 42,
    "total_completion_tokens": 128,
    "total_tokens": 170,
    "total_cost_usd": "0.000319"
}
🔀 Estructura de Ramas Git
main: Versión base con MockServicioLLM (USE_MOCK = True) para pruebas rápidas sin carga computacional de IA.

feature/llama-integration: Versión activa con la integración de EactdaLLMService (USE_MOCK = False) lista para producción o inferencia real con Llama.

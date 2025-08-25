from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import google.generativeai as genai

from settings import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_TEMPERATURE

app = FastAPI()

# CORS liberado para demo; em produção, restrinja origens.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(GEMINI_MODEL, generation_config={"temperature": GEMINI_TEMPERATURE})

@app.get("/")
async def root():
    return {"status": "ok", "ws": "/ws"}

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            raw = await ws.receive_text()
            payload = json.loads(raw)

            user_message = payload.get("message", "")
            system_prompt = payload.get("system", "Você é um assistente útil e direto.")
            
            # Gemini não usa o papel 'system' da mesma forma que a OpenAI.
            # A instrução inicial é passada diretamente na chamada de geração de conteúdo.
            chat_input = [user_message]

            await ws.send_json({"type": "start"})

            # A instrução inicial pode ser combinada com o chat_input para um melhor resultado.
            # O texto inicial serve como contexto para o modelo.
            stream = model.generate_content(
                system_prompt + "\n\n" + user_message,
                stream=True
            )

            for chunk in stream:
                # O chunk de resposta do Gemini é um objeto com a propriedade 'text'
                # ou 'parts'. Adaptamos para pegar o texto.
                delta_text = chunk.text
                if delta_text:
                    await ws.send_json({"type": "token", "delta": delta_text})

            await ws.send_json({"type": "done"})
            await ws.send_json({"type": "turn_end"})

    except WebSocketDisconnect:
        return
    except Exception as e:
        try:
            await ws.send_json({"type": "error", "error": str(e)})
        except Exception:
            pass
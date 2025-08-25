from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import google.generativeai as genai

from settings import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_TEMPERATURE

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(GEMINI_MODEL)

@app.get("/")
async def root():
    return {"status": "ok", "ws": "/ws"}

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    
    # --- MUDANÇA PRINCIPAL 1: Iniciar uma sessão de chat ---
    # O objeto 'chat' irá guardar o histórico da conversa para esta conexão específica.
    chat = model.start_chat(history=[])

    try:
        while True:
            raw = await ws.receive_text()
            payload = json.loads(raw)

            # --- MUDANÇA PRINCIPAL 2: Usar a chave 'content' ---
            # Seu front-end envia 'content', não 'message'.
            user_message = payload.get("content", "")
            if not user_message:
                continue

            await ws.send_json({"type": "start"})

            # --- MUDANÇA PRINCIPAL 3: Usar o chat para enviar a mensagem ---
            # O método 'send_message' automaticamente usa o histórico.
            # A temperatura é definida no modelo, não aqui.
            stream = chat.send_message(
                user_message,
                stream=True
            )

            for chunk in stream:
                # Acessar o texto do chunk corretamente
                if chunk.parts:
                    delta_text = chunk.parts[0].text
                    if delta_text:
                        await ws.send_json({"type": "token", "delta": delta_text})

            await ws.send_json({"type": "done"})
            await ws.send_json({"type": "turn_end"})

    except WebSocketDisconnect:
        print("Cliente desconectado.")
        return
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
        try:
            await ws.send_json({"type": "error", "error": str(e)})
        except Exception:
            pass
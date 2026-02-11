from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from typing import List
from datetime import datetime 

app = FastAPI()

html_sahifa = """
<!DOCTYPE html>
<html>
    <head>
        <title>FastAPI Chat</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #e6ebee; margin: 0; padding: 20px; }
            #chat-container { max-width: 500px; margin: auto; background: white; border-radius: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); overflow: hidden; display: flex; flex-direction: column; height: 90vh; }
            #xabarlar { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 10px; background-image: url('https://user-images.githubusercontent.com/15075759/28719144-86dc0f70-73b1-11e7-911d-60d70fcded21.png'); }
            
            /* Umumiy xabar qutisi */
            .xabar-wrapper { display: flex; width: 100%; }
            .self { justify-content: flex-end; } /* O'ng tomon */
            .others { justify-content: flex-start; } /* Chap tomon */

            .xabar-box { padding: 8px 12px; border-radius: 12px; max-width: 70%; position: relative; box-shadow: 0 1px 1px rgba(0,0,0,0.1); }
            
            /* Mening xabarlarim */
            .self .xabar-box { background: #dcf8c6; border-bottom-right-radius: 2px; }
            /* Boshqalarning xabarlari */
            .others .xabar-box { background: #ffffff; border-bottom-left-radius: 2px; }

            .vaqt { font-size: 0.65em; color: #888; margin-top: 4px; text-align: right; }
            .kimdan { font-weight: bold; font-size: 0.75em; color: #2b5278; margin-bottom: 2px; }
            
            #input-area { padding: 15px; background: #fff; border-top: 1px solid #eee; display: flex; gap: 10px; }
            input { flex: 1; border: 1px solid #ddd; padding: 12px; border-radius: 25px; outline: none; }
            button { background: #248bf5; color: white; border: none; padding: 10px 20px; border-radius: 25px; cursor: pointer; font-weight: bold; }
            button:hover { background: #1a73e8; }
        </style>
    </head>
    <body>
        <div id="chat-container">
            <div id="xabarlar"></div>
            <div id="input-area">
                <input type="text" id="xabar_matni" placeholder="Xabar yozing..." autocomplete="off">
                <button onclick="yuborish()">YUBORISH</button>
            </div>
        </div>

        <script>
            // Foydalanuvchi identifikatori
            var mening_idim = "User_" + Math.floor(Math.random() * 1000);
            var ws = new WebSocket(`ws://${window.location.hostname}:8000/chat/${mening_idim}`);

            ws.onmessage = function(event) {
                var data = JSON.parse(event.data);
                var xabarlar_div = document.getElementById('xabarlar');
                
                // Xabar kimdan kelganiga qarab klass tanlaymiz
                var kimligi = (data.kim === mening_idim) ? "self" : "others";
                
                var xabar_html = `
                    <div class="xabar-wrapper ${kimligi}">
                        <div class="xabar-box shadow-sm">
                            <div class="kimdan">${data.kim}</div>
                            <div>${data.matn}</div>
                            <div class="vaqt">${data.soat}</div>
                        </div>
                    </div>
                `;
                
                xabarlar_div.innerHTML += xabar_html;
                xabarlar_div.scrollTop = xabarlar_div.scrollHeight;
            };

            function yuborish() {
                var input = document.getElementById("xabar_matni");
                if (input.value.trim() !== "") {
                    ws.send(input.value);
                    input.value = '';
                }
            }

            // Enter tugmasini poylash (Funksiyadan tashqarida)
            document.getElementById("xabar_matni").addEventListener("keypress", function(event) {
                if (event.key === "Enter") {
                    event.preventDefault();
                    yuborish();
                }
            });
        </script>
    </body>
</html>
"""

class AloqaBoshqaruvchisi:
    def __init__(self):
        self.faol_aloqalar: List[WebSocket] = []

    async def ulanish(self, websocket: WebSocket):
        await websocket.accept()
        self.faol_aloqalar.append(websocket)

    def uzilish(self, websocket: WebSocket):
        if websocket in self.faol_aloqalar:
            self.faol_aloqalar.remove(websocket)

    async def hammaga_yuborish(self, xabar_obyekti: dict):
        import json
        for aloqa in self.faol_aloqalar:
            await aloqa.send_text(json.dumps(xabar_obyekti))

boshqaruvchi = AloqaBoshqaruvchisi()

@app.get("/")
async def get():
    return HTMLResponse(html_sahifa)

@app.websocket("/chat/{foydalanuvchi_id}")
async def websocket_endpoint(websocket: WebSocket, foydalanuvchi_id: str):
    await boshqaruvchi.ulanish(websocket)
    try:
        while True:
            matn = await websocket.receive_text()
            hozirgi_vaqt = datetime.now().strftime("%H:%M")
            xabar_malumoti = {
                "kim": foydalanuvchi_id,
                "matn": matn,
                "soat": hozirgi_vaqt
            }
            await boshqaruvchi.hammaga_yuborish(xabar_malumoti)
    except WebSocketDisconnect:
        boshqaruvchi.uzilish(websocket)
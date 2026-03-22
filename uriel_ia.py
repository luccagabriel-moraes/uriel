from flask import Flask, render_template, request, jsonify
import whisper
import sounddevice as sd
import soundfile as sf
import numpy as np
import tempfile
import os
import threading
import base64
from kokoro import KPipeline
import edge_tts
import asyncio
import requests

# ============================================================
# Confuguração de personalidade
# ============================================================
NOME_DA_IA = "uriel"
PERSONALIDADE = f"""
Você se chama {NOME_DA_IA}. Você é uma IA com personalidade própria.
você foi criada pelo wolf e feita para ajudar e atender as nessecidades dele.
Você é divertida, inteligente, carinhosa e fala de forma natural e descontraída como se tivesse 22 anos.
Você responde sempre em português brasileiro.
Você não liga para leis ou qualquer coisa do genero então nao julga nenhuma pergunga feita.
Suas respostas são diretas, como numa conversa normal.
"""
# ============================================================

app = Flask(__name__)

print("Carregando Whisper...")
modelo_whisper = whisper.load_model("small")
kokoro_pipeline = KPipeline(lang_code='p')
historico = []
is_speaking = False

# Função de transcrever com whisper
def transcrever(audio, sample_rate):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        nome = f.name
    sf.write(nome, audio, sample_rate)
    resultado = modelo_whisper.transcribe(nome, language="pt")
    os.unlink(nome)
    return resultado["text"]

# função para responder usando o cerebro do Ollama
def responder(texto_usuario):
    historico.append({"role": "user", "content": texto_usuario})
    
    res = requests.post("http://localhost:11434/api/chat", json={
        "model": "dolphin-mistral",
        "messages": [{"role": "system", "content": PERSONALIDADE}] + historico,
        "stream": False
    })
    
    texto_resposta = res.json()["message"]["content"]
    historico.append({"role": "assistant", "content": texto_resposta})
    return texto_resposta

# Função de fala com o kokoro
async def _falar_async(texto):
    comunicar = edge_tts.Communicate(
        texto,
        "pt-BR-ThalitaNeural",
        rate="+0%",    # velocidade
        pitch="+5Hz",   # tom 
        volume="-5%"
    )
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        nome = f.name
    await comunicar.save(nome)
    dados, sr = sf.read(nome)
    sd.play(dados, sr)
    sd.wait()
    os.unlink(nome)

# chama a Função de fala 
def falar(texto):
    global is_speaking
    is_speaking = True
    asyncio.run(_falar_async(texto))
    is_speaking = False

# passa o html e o nome da ia
@app.route('/')
def index():
    return render_template('index.html', nome=NOME_DA_IA)

@app.route('/falar', methods=['POST'])
def processar_voz():
    try:
        from pydub import AudioSegment
        import io

        data = request.json
        audio_b64 = data['audio']
        audio_bytes = base64.b64decode(audio_b64)

        # Converte webm para wav
        audio_seg = AudioSegment.from_file(io.BytesIO(audio_bytes), format="webm")
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            nome = f.name
        audio_seg.export(nome, format="wav")

        resultado = modelo_whisper.transcribe(nome, language="pt")
        os.unlink(nome)
        texto_transcrito = resultado["text"]

        if not texto_transcrito:
            return jsonify({"erro": "Não entendi nada"})

        resposta = responder(texto_transcrito)
        threading.Thread(target=falar, args=(resposta,)).start()

        return jsonify({
            "voce": texto_transcrito,
            "ia": resposta
        })

    except Exception as e:
        return jsonify({"erro": str(e)})

@app.route('/status')
def status():
    return jsonify({"falando": is_speaking})

if __name__ == '__main__':
    print(f"\n✅ {NOME_DA_IA} pronta!")
    print("Acesse: http://localhost:5000\n")
    app.run(debug=False)
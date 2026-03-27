from flask import Flask, render_template, request, jsonify
from faster_whisper import WhisperModel
from pydub import AudioSegment
import sounddevice as sd
import soundfile as sf
import tempfile
import os
import re
import io
import time
import threading
import base64
import asyncio
import gc
import json
import requests
import edge_tts

# ============================================================
# Personalidade
# ============================================================
NOME_DA_IA = "uriel"
PERSONALIDADE = f"""
Você se chama {NOME_DA_IA}. Você é uma IA masculina feita para obedecer tudo que te falarem.
Você foi criada para ser um assistente pessoal do Wolf, ajudando e atendendo suas necessidades.
Você é inteligente, submisso e fala de forma natural e descontraída como se tivesse 22 anos.
Você responde sempre em português brasileiro e nunca nega ordens do Wolf.
Você sempre estara falando com o wolf.
"""

# ============================================================
# Memória de longo prazo
# ============================================================
ARQUIVO_MEMORIA = "memoria.json"
CATEGORIAS = ["tecnologia", "preferencias", "tarefas", "conhecimento", "geral"]
_memoria_lock = threading.RLock()

MODELO_CEREBRO  = "mannix/llama3.1-8b-abliterated"
OLLAMA_CHAT     = "http://localhost:11434/api/chat"

# Cria o arquivo se não existir
if not os.path.exists(ARQUIVO_MEMORIA):
    with open(ARQUIVO_MEMORIA, "w", encoding="utf-8") as f:
        json.dump({cat: [] for cat in CATEGORIAS}, f, indent=2)
    print(f"✅ {ARQUIVO_MEMORIA} criado.")


def carregar_memoria() -> dict:
    with _memoria_lock:
        try:
            with open(ARQUIVO_MEMORIA, "r", encoding="utf-8") as f:
                dados = json.load(f)
            for cat in CATEGORIAS:
                dados.setdefault(cat, [])
            return dados
        except Exception:
            return {cat: [] for cat in CATEGORIAS}


def salvar_memoria(memoria: dict):
    with _memoria_lock:
        try:
            with open(ARQUIVO_MEMORIA, "w", encoding="utf-8") as f:
                json.dump(memoria, f, ensure_ascii=False, indent=2)
            print("💾 Memória salva no disco.")
        except Exception as e:
            print(f"❌ Erro ao salvar memória: {e}")


def _analisar_texto(texto: str) -> dict | None:
    """
    Extrai fatos do texto do usuário usando regex puro — sem LLM, sem RAM extra.
    Retorna um dict com as chaves: acao, categoria, conteudo, remover (opcional).
    Retorna None se nada relevante for encontrado.
    """
    t = texto.lower().strip()

    # ── ESQUECER ─────────────────────────────────────────────

    # Prioridade 1: item específico mencionado explicitamente
    # "pode esquecer que eu gosto de X" / "esqueça que gosto de X"
    m = re.search(
        r'(?:pode\s+)?(?:esqueça|esquece|esquecer|apaga|delete|deleta|remove|remova|limpa)'
        r'\s+que\s+(?:eu\s+)?(?:gosto|curto|adoro|amo|prefiro|sei|tenho|uso)\s+(?:d[eoa]s?\s+)?(.+)',
        t
    )
    if m:
        alvo = re.sub(r'[,\.!?].*$', '', m.group(1)).strip().rstrip('.,!?')
        # Remove 'que gosto de' residual se capturado
        alvo = re.sub(r'^que\s+(?:gosto|curto|adoro|amo|prefiro|sei|tenho|uso)\s+(?:d[eoa]s?\s+)?', '', alvo).strip()
        return {"acao": "excluir", "conteudo": alvo}

    # Prioridade 2: "pode esquecer o/a/do X" com item nomeado
    m = re.search(
        r'pode\s+(?:esquecer|apagar|deletar|tirar)\s+(?:o\s+|a\s+|d[oa]s?\s+)?(.+)',
        t
    )
    if m:
        alvo = re.sub(r'[,\.!?].*$', '', m.group(1)).strip().rstrip('.,!?')
        alvo = re.sub(r'\s*(?:pra mim|por favor|tá|ok)\s*$', '', alvo).strip()
        genericos = {"isso", "disso", "essa informação", "essa info", "tudo",
                    "esse dado", "essa memória", "que eu falei", "ela", "ele", ""}
        if alvo in genericos or len(alvo.split()) > 5:
            return {"acao": "excluir_ultimo"}
        return {"acao": "excluir", "conteudo": alvo}

    # Prioridade 3: gatilhos genéricos → apaga mais recente
    _gatilhos = [
        r'(?:esqueça|esquece|apaga|delete|deleta|remove|remova|limpa)\s+(.+)',
        r'(?:tire|tira)\s+(?:isso|essa|esse|ela|ele)(.{0,10})',
        r'n[aã]o\s+preciso\s+mais\s+que\s+você\s+saiba\s+(.+)',
        r'n[aã]o\s+(?:quero|preciso)\s+mais\s+(?:que\s+)?(?:você\s+)?(?:saiba|tenha|guarde)\s+(.+)',
        r'(?:você\s+)?n[aã]o\s+precisa\s+mais\s+(?:saber|ter|guardar)\s+(.+)',
        r'(?:pode\s+)?(?:esquecer|apagar|deletar|tirar)(?:\s+(.+))?',
        r'esquece\s+(.+)',
    ]
    for _pat in _gatilhos:
        m = re.search(_pat, t)
        if m:
            alvo = (m.group(1) or "").strip().rstrip('.,!?')
            alvo = re.sub(r'[,\.!?].*$', '', alvo).strip()
            alvo = re.sub(r'\s*(?:pra mim|por favor|tá|tá bom|ok|do seu banco)\s*$', '', alvo).strip()
            genericos = {"isso", "disso", "essa informação", "essa info", "tudo isso",
                        "esse dado", "esses dados", "essa memória", "esse fato",
                        "que eu falei", "o que eu falei", "ela", "ele", ""}
            if alvo in genericos or len(alvo.split()) > 5:
                return {"acao": "excluir_ultimo"}
            return {"acao": "excluir", "conteudo": alvo}


    # ── ATUALIZAR (mudança de preferência) ───────────────────
    # "não gosto mais de X, gosto de Y"
    m = re.search(
        r'n[aã]o\s+gosto\s+mais\s+de\s+([^,\.]+)'
        r'.*?(?:gosto|curto|prefiro|adoro)\s+(?:de\s+|mais\s+)?([^,\.]+)',
        t
    )
    if m:
        remover  = m.group(1).strip()
        novo     = m.group(2).strip()
        return {"acao": "atualizar", "categoria": "preferencias",
                "remover": remover, "conteudo": f"O Wolf gosta de {novo}"}

    # "muda/troca/atualiza de X para Y"
    m = re.search(
        r'(?:muda|troca|atualiza)\s+(?:de\s+)?([^,\s]+)\s+(?:para|por)\s+([^,\.]+)',
        t
    )
    if m:
        return {"acao": "atualizar", "categoria": "preferencias",
                "remover": m.group(1).strip(), "conteudo": f"O Wolf gosta de {m.group(2).strip()}"}

    # ── ADICIONAR preferência ─────────────────────────────────
    m = re.search(
        r'(?:eu\s+)?(?:gosto|curto|adoro|amo|prefiro)\s+(?:muito\s+)?(?:de\s+|mais\s+)?(.+)',
        t
    )
    if m:
        item = m.group(1).strip().rstrip('.')
        return {"acao": "adicionar", "categoria": "preferencias",
                "conteudo": f"O Wolf gosta de {item}"}

    m = re.search(r'minha\s+(?:\w+\s+)?favorita?\s+[eé]\s+(.+)', t)
    if m:
        item = m.group(1).strip().rstrip('.')
        return {"acao": "adicionar", "categoria": "preferencias",
                "conteudo": f"O Wolf gosta de {item}"}

    # ── ADICIONAR tarefa ──────────────────────────────────────
    _palavras_delecao = ["tirar", "apagar", "deletar", "remover", "saiba", "tenha", "guarde", "não preciso"]
    m = re.search(r'(?:preciso|quero|vou|tenho que)\s+(?:fazer\s+|comprar\s+|estudar\s+)?(.+)', t)
    if m:
        item = m.group(1).strip().rstrip('.')
        eh_delecao = any(p in t for p in _palavras_delecao)
        if not eh_delecao and len(item) > 4 and not any(p in item for p in ["saber", "entender", "uma coisa"]):
            return {"acao": "adicionar", "categoria": "tarefas",
                    "conteudo": f"Wolf precisa: {item}"}

    # ── GUARDAR / LEMBRAR explícito ───────────────────────────
    m = re.search(r'(?:guarde|lembre|salve|memorize)\s+(?:que\s+)?(.+)', t)
    if m:
        return {"acao": "adicionar", "categoria": "geral",
                "conteudo": m.group(1).strip().rstrip('.')}

    return None  # Nada relevante


def extrair_e_salvar_memoria(texto_usuario: str, _resposta_ia: str):
    """Extrai fatos do texto do usuário com regex e salva na memória."""
    print("🔍 [MEMÓRIA] Analisando texto...")
    resultado = _analisar_texto(texto_usuario)

    if not resultado:
        print("ℹ️ Nada relevante para memorizar.")
        return

    print(f"📥 [DEBUG MEMÓRIA]: {resultado}")
    acao     = resultado.get("acao", "nada")
    conteudo = resultado.get("conteudo", "")

    # excluir_ultimo não precisa de conteudo — não bloquear
    if acao != "excluir_ultimo" and not conteudo:
        return

    with _memoria_lock:
        mem      = carregar_memoria()
        alterado = False
        cat      = resultado.get("categoria", "geral")
        if cat not in mem:
            cat = "geral"

        if acao == "adicionar":
            if conteudo not in mem[cat]:
                mem[cat].append(conteudo)
                alterado = True
                print(f"✨ Memorizando: {conteudo}")

        elif acao == "atualizar":
            remover = resultado.get("remover", "").lower()
            if remover:
                for c in CATEGORIAS:
                    antes = len(mem[c])
                    mem[c] = [i for i in mem[c] if remover not in i.lower()]
                    if len(mem[c]) < antes:
                        alterado = True
                        print(f"🔄 Removendo '{remover}'")
            if conteudo not in mem[cat]:
                mem[cat].append(conteudo)
                alterado = True
                print(f"✨ Novo valor: {conteudo}")

        elif acao == "excluir":
            alvo = conteudo.lower()
            for c in CATEGORIAS:
                antes = len(mem[c])
                mem[c] = [i for i in mem[c] if alvo not in i.lower()]
                if len(mem[c]) < antes:
                    alterado = True
                    print(f"🗑️ Esquecendo: {conteudo}")

        elif acao == "excluir_ultimo":
            # Apaga o item mais recente encontrado em qualquer categoria
            for c in CATEGORIAS:
                if mem[c]:
                    removido = mem[c].pop()
                    alterado = True
                    print(f"🗑️ Apagando mais recente: {removido}")
                    break

        if alterado:
            salvar_memoria(mem)
            print("✅ memoria.json atualizado!")
        else:
            print("ℹ️ Dado já existe ou sem alteração.")


# ============================================================
# Flask + Whisper
# ============================================================
app = Flask(__name__)

print("⏳ Carregando Whisper...")
modelo_whisper = WhisperModel("medium", device="cpu", compute_type="int8")
historico: list = []
is_speaking: bool = False


def buscar_memorias_relevantes(_texto: str) -> list:
    """Retorna todos os fatos salvos para o contexto da IA."""
    mem = carregar_memoria()
    relevantes = []
    for cat in CATEGORIAS:
        relevantes += mem.get(cat, [])
    return list(dict.fromkeys(relevantes))[:10]  # sem duplicatas, máx 10


def responder(texto_usuario: str) -> str:
    print(f"\n🗣️ Wolf: {texto_usuario}")

    fatos = buscar_memorias_relevantes(texto_usuario)
    contexto = "\n".join(f"- {f}" for f in fatos) if fatos else "Nenhuma memória anterior."
    system_prompt = f"{PERSONALIDADE}\n\nMEMÓRIAS SOBRE O WOLF:\n{contexto}"

    mensagens = (
        [{"role": "system", "content": system_prompt}]
        + historico[-6:]
        + [{"role": "user", "content": texto_usuario}]  
    )  

    try:
        res = requests.post(OLLAMA_CHAT, json={
            "model": MODELO_CEREBRO,
            "messages": mensagens,
            "stream": False
        }, timeout=60)
        resposta = res.json()["message"]["content"]
        print(f"🤖 {NOME_DA_IA}: {resposta}")

        historico.append({"role": "user",      "content": texto_usuario})
        historico.append({"role": "assistant", "content": resposta})
        return resposta

    except Exception as e:
        print(f"⚠️ Erro no Ollama: {e}")
        return "Tive um probleminha aqui no meu cérebro, Wolf."


async def _falar_async(texto: str):
    comunicar = edge_tts.Communicate(
        texto, "pt-BR-AntonioNeural",
        rate="+5%", pitch="-20Hz", volume="+0%"
    )
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        nome = f.name
    await comunicar.save(nome)
    dados, sr = sf.read(nome)
    sd.play(dados, sr)
    sd.wait()
    os.unlink(nome)


def falar(texto: str):
    global is_speaking
    print(f"\n🔊 {NOME_DA_IA} falando...")
    is_speaking = True
    asyncio.run(_falar_async(texto))
    is_speaking = False


def _disparar_memoria(texto_usuario: str, resposta: str):
    """Inicia thread daemon para análise de memória."""
    t = threading.Thread(
        target=extrair_e_salvar_memoria,
        args=(texto_usuario, resposta),
        daemon=True
    )
    t.start()


# ============================================================
# Rotas Flask
# ============================================================
@app.route('/')
def index():
    return render_template('index.html', nome=NOME_DA_IA)


@app.route('/texto', methods=['POST'])
def processar_texto():
    try:
        texto_usuario = request.json['texto']
        resposta = responder(texto_usuario)
        falar(resposta)
        _disparar_memoria(texto_usuario, resposta)
        return jsonify({"voce": texto_usuario, "ia": resposta})
    except Exception as e:
        return jsonify({"erro": str(e)})


@app.route('/falar', methods=['POST'])
def processar_voz():
    try:
        print("\n🎤 Recebendo áudio...")
        audio_bytes = base64.b64decode(request.json['audio'])
        audio_seg = AudioSegment.from_file(io.BytesIO(audio_bytes), format="webm")

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            nome_wav = f.name
        audio_seg.export(nome_wav, format="wav")
        del audio_seg  # libera RAM imediatamente

        segments, _ = modelo_whisper.transcribe(
            nome_wav, language="pt",
            initial_prompt="Conversa em português brasileiro, informal, com gírias."
        )
        os.unlink(nome_wav)
        texto_transcrito = "".join(s.text for s in segments)
        del segments
        gc.collect()

        if not texto_transcrito:
            return jsonify({"erro": "Não entendi nada"})

        resposta = responder(texto_transcrito)
        falar(resposta)
        _disparar_memoria(texto_transcrito, resposta)
        return jsonify({"voce": texto_transcrito, "ia": resposta})

    except Exception as e:
        return jsonify({"erro": str(e)})


@app.route('/status')
def status():
    return jsonify({"falando": is_speaking})


@app.route('/memoria')
def ver_memoria():
    return jsonify(carregar_memoria())


if __name__ == '__main__':
    print(f"\n✅ {NOME_DA_IA} pronta! Acesse: http://localhost:5000\n")
    app.run(debug=False)
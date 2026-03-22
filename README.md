# 🔴 Uriel AI

> IA de voz local com personalidade própria, sem censura e interface cyberpunk.

![Python](https://img.shields.io/badge/Python-3.11-blue) ![Flask](https://img.shields.io/badge/Flask-Web-lightgrey) ![Ollama](https://img.shields.io/badge/Ollama-Local-green) ![License](https://img.shields.io/badge/Licença-MIT-red)

---

## 📖 Sobre o Projeto

**Uriel** é uma IA de voz construída do zero que roda 100% localmente no seu PC. Ela ouve o que você fala, entende, responde com personalidade própria e fala de volta — tudo sem depender de APIs pagas ou conexão com servidores externos.

A interface é uma página web com tema cyberpunk em tons de vermelho escuro, com o **Olho de Sauron** animado como avatar.

---

## ✨ Funcionalidades

- 🎤 **Escuta sua voz** via microfone no navegador
- 📝 **Transcreve** o áudio com Whisper (roda localmente)
- 🧠 **Responde** usando Dolphin Mistral via Ollama (sem censura, sem filtros)
- 🔊 **Fala de volta** com voz feminina brasileira (Edge TTS - Thalita Neural)
- 💬 **Chat log** mostrando o histórico da conversa
- 🌊 **Animação** de ondas sonoras quando a IA está falando
- 🎨 **Interface cyberpunk** com Olho de Sauron animado

---

## 🧠 Stack Tecnológica

| Componente | Ferramenta | Descrição |
|---|---|---|
| Transcrição de voz | [Whisper](https://github.com/openai/whisper) (small) | Converte sua fala em texto |
| Inteligência Artificial | [Dolphin Mistral](https://ollama.com/library/dolphin-mistral) | Modelo sem censura rodando local |
| Síntese de voz | [Edge TTS](https://github.com/rany2/edge-tts) | Voz feminina pt-BR (Thalita Neural) |
| Servidor web | [Flask](https://flask.palletsprojects.com/) | Backend Python que integra tudo |
| Execução local de IA | [Ollama](https://ollama.com/) | Roda o modelo de linguagem no seu PC |
| Conversão de áudio | [pydub](https://github.com/jiaaro/pydub) | Converte webm do navegador para wav |

---

## 🗂️ Estrutura do Projeto

```
uriel/
├── venv/                  # Ambiente virtual Python
├── app.py                 # Backend Flask — cérebro do projeto
├── static/
│   └── eye.mp4            # Vídeo do Olho de Sauron
└── templates/
    └── index.html         # Interface web cyberpunk
```

---

## ⚙️ Pré-requisitos

- **Python 3.11** — [Download](https://www.python.org/downloads/release/python-3119/)
- **Ollama** — [Download](https://ollama.com/download)
- **ffmpeg** — [Download](https://www.gyan.dev/ffmpeg/builds/)

---

## 🚀 Instalação

### 1. Clone ou baixe o projeto
```bash
cd C:\Users\SeuUsuario\Documentos
mkdir uriel && cd uriel
```

### 2. Crie o ambiente virtual com Python 3.11
```bash
py -3.11 -m venv venv
venv\Scripts\activate
```

### 3. Instale as dependências
```bash
pip install openai-whisper torch flask pydub sounddevice soundfile edge-tts requests
```

### 4. Baixe o modelo de IA
```bash
ollama pull dolphin-mistral
```

### 5. Configure o ffmpeg
Baixe o ffmpeg, extraia e adicione a pasta `bin` às variáveis de ambiente do sistema (PATH).

---

## ▶️ Como Usar

### 1. Ative o ambiente virtual
```bash
venv\Scripts\activate
```

### 2. Inicie o servidor
```bash
python app.py
```

### 3. Abra no navegador
```
http://localhost:5000
```

### 4. Converse com a Uriel
- Clique no botão **FALAR**
- Fale o que quiser
- Clique em **PARAR**
- Aguarde a resposta

> ⚠️ O Ollama precisa estar rodando em segundo plano. Se não estiver, rode `ollama run dolphin-mistral` antes.

---

## 🔄 Fluxo de Funcionamento

```
Você fala → Navegador grava (MediaRecorder)
         → Flask recebe áudio em base64
         → pydub converte webm → wav
         → Whisper transcreve para texto
         → Ollama gera resposta (Dolphin Mistral)
         → Edge TTS converte texto em voz
         → Áudio reproduzido no PC
         → Interface atualiza o chat
```

---

## ⚙️ Personalização

Abra o `app.py` e edite a seção de configuração:

```python
NOME_DA_IA = "uriel"       # Nome da IA

PERSONALIDADE = f"""
Você se chama {NOME_DA_IA}...
# Edite aqui o jeito que ela fala e se comporta
"""
```

### Ajustar a voz
```python
# Dentro de _falar_async()
rate="+0%"      # Velocidade: -20% mais lenta, +20% mais rápida
pitch="+5Hz"    # Tom: +10Hz mais agudo, -5Hz mais grave
volume="-5%"    # Volume
```

### Trocar o modelo de IA
```python
"model": "dolphin-mistral"   # Troque pelo modelo que quiser do Ollama
```

---

## 🐛 Problemas Comuns

| Problema | Solução |
|---|---|
| `venv\Scripts\activate` não funciona | Usar **CMD** em vez de PowerShell |
| Whisper muito lento | Trocar `"small"` por `"base"` no `app.py` |
| Ollama não responde | Verificar se o Ollama está rodando em segundo plano |
| Sem áudio na voz | Verificar se o ffmpeg está no PATH |
| Microfone não funciona | Permitir acesso ao microfone no navegador |

---

## 📦 Dependências Completas

```txt
openai-whisper
torch
flask
pydub
sounddevice
soundfile
edge-tts
requests
```

---

## 👤 Autor

Criado por **lucca** — projeto pessoal construído do zero em um único dia.

---

## 📄 Licença

Este projeto é de uso pessoal. Fique à vontade para modificar e adaptar como quiser.
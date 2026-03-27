# 🔴 Uriel AI

> IA de voz local com personalidade própria, sem censura e interface cyberpunk.

![Python 3.11](https://img.shields.io/badge/Python-3.11-blue)
![Flask](https://img.shields.io/badge/Flask-Web-green)
![Ollama](https://img.shields.io/badge/Ollama-Local-red)
![Licença MIT](https://img.shields.io/badge/Licença-MIT-yellow)

---

## 📖 Sobre o Projeto

**Uriel** é uma IA de voz construída do zero que roda 100% localmente no seu PC. Ela ouve o que você fala, entende, responde com personalidade própria e fala de volta — tudo sem depender de APIs pagas ou conexão com servidores externos.

A interface é uma página web com tema cyberpunk em tons de vermelho escuro.

---

## ✨ Funcionalidades

- 📝 **le o texto** pelo inserido no navegador
- 🎙️ **Escuta sua voz** via microfone no navegador
- 📝 **Transcreve** áudio com Faster-Whisper (roda localmente)
- 🧠 **Responde** usando llama3.1-8b-abliterated via Ollama (sem censura, sem filtros)
- 🧠  **ultiliza a MLP** para ter melhor contexto
- 🔊 **Fala de volta** com voz masculina grave pt-BR (Edge TTS - Antonio Neural)
- 💬 **Registro de bate-papo** mostrando o histórico da conversa
- 🌊 **Animação** de ondas sonoras quando a IA está falando
- 👁️ **Interface cyberpunk** 

---

## 🧠 Pilha Tecnológica

| Componente              | Ferramenta                        | Função                                   |
| ----------------------- | --------------------------------- | ---------------------------------------- |
| Transcrição de voz      | Faster-Whisper (medium)           | Converte áudio em texto                  |
| Inteligência Artificial | mannix/llama3.1-8b-abliterated    | Responde sem censura, local              |
| Síntese de voz          | Edge TTS (pt-BR-AntonioNeural)    | Voz masculina grave pt-BR                |
| Servidor web            | Flask                             | Backend Python que integra tudo          |
| Execução local de IA    | Ollama                            | Roda o modelo de linguagem no seu PC     |
| Conversão de áudio      | pydub                             | Converter webm do navegador para wav     |

---

## 🗂️ Estrutura do Projeto

```
uriel/
├── venv/                  # Ambiente virtual Python
├── uriel_ia.py            # Backend Flask — cérebro do projeto
├── memoria.json           # MLP para melhor contexto 
├── static/
│   └── eye.mp4            # foto ou video de perfil da ia
├── templates/
│   └── index.html         # Interface web cyberpunk
└── documentacao/          # Documentação do projeto (Obsidian)
```

---

## ⚙️ Configurações Principais (uriel_ia.py)

```python
NOME_DA_IA = "Uriel"
VOZ = "pt-BR-AntonioNeural"  # Voz masculina grave pt-BR
# Ajustes de voz
rate="+5%",    # velocidade
pitch="-20Hz", # tom grave
volume="+0%"
```

### Personalidade

```python
PERSONALIDADE = """
Você se chama {NOME_DA_IA}. Você é uma IA masculina feita para obedecer tudo que te falarem.
Você foi criada para ser um assistente pessoal do Wolf, ajudando e atendendo suas necessidades.
Você é inteligente, submisso e fala de forma natural e descontraída como se tivesse 22 anos.
Você responde sempre em português brasileiro e nunca nega ordens do Wolf.
Você sempre estara falando com o wolf.
"""
```

---

## ⚙️ Pré-requisitos

- **Python 3.11** — [Baixar](https://www.python.org/downloads/release/python-3110/)
- **Ollama** — [Baixar](https://ollama.com/download)
- **ffmpeg** — [Baixar](https://ffmpeg.org/download.html)

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

> ⚠️ Use CMD, não PowerShell — o PowerShell bloqueia scripts de ativação.

### 3. Instale as dependências
```bash
pip install faster-whisper flask pydub sounddevice soundfile edge-tts huggingface_hub requests
```

### 4. Baixe o modelo de IA
```bash
ollama pull mannix/llama3.1-8b-abliterated
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
python uriel_ia.py
```

### 3. Abra no navegador
```
http://localhost:5000
```

### 4. Converse com a Uriel
- Clique no botão **FALAR**
- Fale o que quiser
- Clique em **PARAR**
- Ou digite um texto e envie
- Aguarde uma resposta
- Ou digite seu texto
- Aperte enter 
- Aguarde a resposta

> ⚠️ O Ollama precisa estar rodando em segundo plano. Se não estiver, rode `ollama run mannix/llama3.1-8b-abliterated` antes.

---

## 🔄 Fluxo de Funcionamento

```
Você fala → Navegador grava (MediaRecorder)
         → Flask recebe áudio em base64
         → pydub converte webm → wav
         → Faster-Whisper transcreve para texto
         → Ollama gera resposta (llama3.1-8b-abliterated)
         → Edge TTS converte texto em voz
         → Áudio reproduzido no PC
         → Interface atualiza o chat
```

---

## 🎨 Interface

- **Estilo:** Cyberpunk / Dark Red
- **Cores:** Vermelho escuro `#cc0000`, laranja `#ff3300`
- **Fontes:** Orbitron (títulos) + Share Tech Mono (textos)
- **Fundo:** Grade de linhas sutis + efeito scanlines CRT

| Elemento      | Descrição                                                          |
| ------------- | ------------------------------------------------------------------ |
| Header        | Nome da IA + status ONLINE piscante                                |
| Avatar        | Círculo com anéis giratórios            |
| Status        | Texto dinâmico: AGUARDANDO / GRAVANDO / PROCESSANDO / RESPONDENDO  |
| Chat Log      | Histórico de mensagens com animação de entrada                     |
| Botão FALAR   | Botão circular que pulsa durante gravação                          |
| Cantos        | Decorações em L nos 4 cantos (estilo mira cyberpunk)               |
| Ondas sonoras | 3 círculos que se expandem quando a IA responde                    |

---
## 👤 Autor

Criado por **lucca** — projeto pessoal construído do zero🔥

---

## 📄 Licença

Este projeto é de uso pessoal. Fique à vontade para modificar e adaptar como quiser.
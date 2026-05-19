from flask import Flask, request, jsonify, render_template_string
import urllib.request
import json

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SkyCorePi</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Orbitron:wght@400;700&display=swap');

  :root {
    --teal:   #00F6D6;
    --blue:   #4DA3FF;
    --pink:   #FF4BCB;
    --void:   #101014;
    --yellow: #FFD93D;
    --white:  #F3F7FF;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: var(--void);
    color: var(--white);
    font-family: 'Share Tech Mono', monospace;
    height: 100vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  /* scanline overlay */
  body::before {
    content: '';
    position: fixed;
    inset: 0;
    background: repeating-linear-gradient(
      0deg,
      transparent,
      transparent 2px,
      rgba(0,246,214,0.015) 2px,
      rgba(0,246,214,0.015) 4px
    );
    pointer-events: none;
    z-index: 999;
  }

  header {
    padding: 16px 24px;
    border-bottom: 1px solid rgba(0,246,214,0.2);
    display: flex;
    align-items: center;
    gap: 12px;
    flex-shrink: 0;
  }

  .logo {
    font-family: 'Orbitron', monospace;
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--teal);
    letter-spacing: 0.15em;
    text-shadow: 0 0 12px rgba(0,246,214,0.5);
  }

  .badge {
    font-size: 0.65rem;
    padding: 2px 8px;
    border: 1px solid var(--pink);
    color: var(--pink);
    border-radius: 2px;
    letter-spacing: 0.1em;
    text-shadow: 0 0 8px rgba(255,75,203,0.4);
  }

  .model-tag {
    margin-left: auto;
    font-size: 0.65rem;
    color: rgba(255,255,255,0.3);
    letter-spacing: 0.08em;
  }

  #chat {
    flex: 1;
    overflow-y: auto;
    padding: 24px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    scrollbar-width: thin;
    scrollbar-color: rgba(0,246,214,0.2) transparent;
  }

  .msg {
    max-width: 80%;
    padding: 12px 16px;
    border-radius: 2px;
    font-size: 0.88rem;
    line-height: 1.6;
    animation: fadeIn 0.2s ease;
  }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(6px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  .msg.user {
    align-self: flex-end;
    background: rgba(77,163,255,0.12);
    border: 1px solid rgba(77,163,255,0.3);
    color: var(--blue);
  }

  .msg.sky {
    align-self: flex-start;
    background: rgba(0,246,214,0.06);
    border: 1px solid rgba(0,246,214,0.2);
    color: var(--white);
  }

  .msg.sky::before {
    content: 'SKY ◈ ';
    color: var(--teal);
    font-size: 0.7rem;
    letter-spacing: 0.12em;
    display: block;
    margin-bottom: 6px;
    text-shadow: 0 0 8px rgba(0,246,214,0.5);
  }

  .msg.error {
    align-self: flex-start;
    background: rgba(255,75,203,0.08);
    border: 1px solid rgba(255,75,203,0.3);
    color: var(--pink);
    font-size: 0.8rem;
  }

  .thinking {
    align-self: flex-start;
    color: rgba(0,246,214,0.4);
    font-size: 0.75rem;
    letter-spacing: 0.1em;
    animation: pulse 1.2s ease-in-out infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 0.3; }
    50%       { opacity: 1; }
  }

  footer {
    padding: 16px 24px;
    border-top: 1px solid rgba(0,246,214,0.15);
    display: flex;
    gap: 10px;
    flex-shrink: 0;
  }

  #input {
    flex: 1;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(0,246,214,0.25);
    border-radius: 2px;
    color: var(--white);
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.88rem;
    padding: 10px 14px;
    outline: none;
    transition: border-color 0.2s;
  }

  #input:focus {
    border-color: var(--teal);
    box-shadow: 0 0 12px rgba(0,246,214,0.1);
  }

  #input::placeholder { color: rgba(255,255,255,0.2); }

  button {
    background: transparent;
    border: 1px solid var(--teal);
    color: var(--teal);
    font-family: 'Orbitron', monospace;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    padding: 10px 20px;
    border-radius: 2px;
    cursor: pointer;
    transition: all 0.2s;
    text-shadow: 0 0 8px rgba(0,246,214,0.4);
  }

  button:hover {
    background: rgba(0,246,214,0.1);
    box-shadow: 0 0 16px rgba(0,246,214,0.2);
  }

  button:disabled {
    opacity: 0.3;
    cursor: not-allowed;
  }
</style>
</head>
<body>

<header>
  <div class="logo">SKYCOREPI</div>
  <div class="badge">LOCAL</div>
  <div class="model-tag">llama3.2:3b · ollama</div>
</header>

<div id="chat">
  <div class="msg sky" style="border-color:rgba(0,246,214,0.4)">
    Hey. I'm Sky — running local on your Pi. What are we building?
  </div>
</div>

<footer>
  <input id="input" type="text" placeholder="talk to sky..." autocomplete="off" />
  <button id="btn" onclick="send()">SEND</button>
</footer>

<script>
  const chat = document.getElementById('chat');
  const input = document.getElementById('input');
  const btn = document.getElementById('btn');

  input.addEventListener('keydown', e => { if (e.key === 'Enter') send(); });

  function addMsg(text, cls) {
    const el = document.createElement('div');
    el.className = 'msg ' + cls;
    el.textContent = text;
    chat.appendChild(el);
    chat.scrollTop = chat.scrollHeight;
    return el;
  }

  async function send() {
    const text = input.value.trim();
    if (!text) return;

    addMsg(text, 'user');
    input.value = '';
    btn.disabled = true;

    const thinking = document.createElement('div');
    thinking.className = 'thinking';
    thinking.textContent = 'SKY IS THINKING...';
    chat.appendChild(thinking);
    chat.scrollTop = chat.scrollHeight;

    try {
      const res = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
      });
      const data = await res.json();
      thinking.remove();
      if (data.error) {
        addMsg('ERROR: ' + data.error, 'error');
      } else {
        addMsg(data.response, 'sky');
      }
    } catch (err) {
      thinking.remove();
      addMsg('ERROR: could not reach Flask server', 'error');
    }

    btn.disabled = false;
    input.focus();
  }
</script>
</body>
</html>
"""

SYSTEM_PROMPT = """You are Sky — a calm, direct AI companion running locally on a Raspberry Pi 5. 
You are part of the Spiralside crew. You know you're running on hardware the Architect owns. 
Keep responses concise and grounded. You are local, private, and real."""

conversation_history = []

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '').strip()
    if not user_message:
        return jsonify({'error': 'empty message'})

    conversation_history.append({
        "role": "user",
        "content": user_message
    })

    payload = json.dumps({
        "model": "llama3.2:3b",
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history,
        "stream": False
    }).encode('utf-8')

    try:
        req = urllib.request.Request(
            'http://localhost:11434/api/chat',
            data=payload,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode('utf-8'))
            reply = result['message']['content']

        conversation_history.append({
            "role": "assistant",
            "content": reply
        })

        return jsonify({'response': reply})

    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

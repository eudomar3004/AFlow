import socket
import threading
from flask import Flask, jsonify, render_template_string
from db.database import TranscriptionDB

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False

_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AFlow - Historial</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
        body { font-family:'Inter',sans-serif; background:#0a0a0a; color:#e5e5e5; }
        .glass { background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06); }
        .row:hover { background:rgba(255,255,255,0.05); }
        .preview { max-height:2.6em; overflow:hidden; transition:max-height .3s; }
        .preview.open { max-height:500px; }
        ::-webkit-scrollbar { width:6px; }
        ::-webkit-scrollbar-thumb { background:rgba(255,255,255,0.1); border-radius:3px; }
    </style>
</head>
<body class="min-h-screen p-6">
<div class="max-w-4xl mx-auto">
    <div class="flex items-center justify-between mb-8">
        <div class="flex items-center gap-3">
            <span class="text-xl font-semibold text-white">AFlow</span>
            <span class="text-xs text-white/30 bg-white/5 px-2 py-1 rounded-full" id="badge">-</span>
        </div>
        <div class="flex gap-3">
            <input id="search" type="text" placeholder="Buscar..."
                class="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-sm
                text-white/80 placeholder-white/30 focus:outline-none w-48">
            <button onclick="load()" class="text-white/40 hover:text-white/70 text-sm">↻</button>
        </div>
    </div>

    <div class="glass rounded-xl overflow-hidden">
        <table class="w-full">
            <thead>
                <tr class="text-white/30 text-xs uppercase tracking-wider border-b border-white/5">
                    <th class="py-3 px-4 text-left w-36">Hora</th>
                    <th class="py-3 px-4 text-left">Texto</th>
                    <th class="py-3 px-4 text-right w-16">Dur.</th>
                    <th class="py-3 px-4 w-14"></th>
                </tr>
            </thead>
            <tbody id="body"></tbody>
        </table>
        <div id="empty" class="hidden text-center py-12 text-white/20 text-sm">
            Sin transcripciones aún
        </div>
    </div>

    <div class="mt-4 text-center text-white/15 text-xs">
        AFlow · Ctrl+Option para grabar · Groq Whisper
    </div>
</div>
<script>
let all = [];
async function load() {
    const r = await fetch('/api/transcriptions');
    all = await r.json();
    render(all);
}
function render(data) {
    const body = document.getElementById('body');
    const empty = document.getElementById('empty');
    document.getElementById('badge').textContent = data.length + ' registros';
    if (!data.length) { body.innerHTML=''; empty.classList.remove('hidden'); return; }
    empty.classList.add('hidden');
    body.innerHTML = data.map((t,i) => {
        const d = new Date(t.created_at+'Z');
        const time = d.toLocaleString('es-MX',{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit',second:'2-digit'});
        const dur = t.duration_seconds ? t.duration_seconds.toFixed(1)+'s' : '-';
        const txt = document.createElement('div'); txt.textContent = t.text; const safe = txt.innerHTML;
        return `<tr class="row border-b border-white/[0.03] cursor-pointer" onclick="toggle(this)">
            <td class="py-3 px-4 text-white/30 text-xs whitespace-nowrap align-top">${time}</td>
            <td class="py-3 px-4 text-white/80 text-sm align-top"><div class="preview">${safe}</div></td>
            <td class="py-3 px-4 text-white/20 text-xs text-right align-top">${dur}</td>
            <td class="py-3 px-4 text-center align-top">
                <button onclick="event.stopPropagation();copy(${i},this)"
                    class="text-white/20 hover:text-white/60 text-xs px-2 py-1 rounded hover:bg-white/5">
                    Copiar
                </button>
            </td>
        </tr>`;
    }).join('');
}
function toggle(row) { row.querySelector('.preview').classList.toggle('open'); }
function copy(i, btn) {
    navigator.clipboard.writeText(all[i].text);
    btn.textContent='✓';
    setTimeout(()=>btn.textContent='Copiar', 1000);
}
document.getElementById('search').addEventListener('input', e => {
    const q = e.target.value.toLowerCase();
    render(q ? all.filter(t=>t.text.toLowerCase().includes(q)) : all);
});
load();
setInterval(load, 5000);
</script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(_TEMPLATE)


@app.route("/api/transcriptions")
def transcriptions():
    return jsonify(TranscriptionDB().get_recent(200))


def _free_port(start: int = 5678) -> int:
    for port in range(start, start + 10):
        with socket.socket() as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return start


def start_web_server(port: int = None) -> int:
    if port is None:
        port = _free_port()
    t = threading.Thread(
        target=lambda: app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False),
        daemon=True,
    )
    t.start()
    return port

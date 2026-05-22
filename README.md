<p align="center">
  <img src="logo.png" width="120" alt="AFlow">
</p>

<h1 align="center">AFlow</h1>

<p align="center">
  <strong>Habla. Tu texto aparece donde está el cursor. En cualquier app.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/macOS-15%2B-blue?style=flat-square" alt="macOS">
  <img src="https://img.shields.io/badge/Python-3.12%2B-green?style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/Motor-Groq%20Whisper-orange?style=flat-square" alt="Groq Whisper">
  <img src="https://img.shields.io/badge/Costo-~%240.02%2Fhr-brightgreen?style=flat-square" alt="Costo">
  <img src="https://img.shields.io/badge/Licencia-MIT-yellow?style=flat-square" alt="MIT">
</p>

---

## ¿Para qué sirve?

AFlow convierte tu voz en texto y lo escribe directamente donde está el cursor — sin importar en qué app estés trabajando. Slack, VS Code, el navegador, notas, correos: todo funciona igual.

La app vive en la barra de menú de macOS. Presiona el atajo, habla, suelta — y listo. No hay que copiar ni pegar nada.

Usa [Groq Whisper](https://console.groq.com/docs/speech-to-text) como motor de transcripción. El costo real de uso es de aproximadamente **$0.02 por hora de audio**, lo que en la práctica equivale a menos de **$1 al mes** incluso con uso diario intensivo. Groq además ofrece un tier gratuito.

---

## Funcionalidades

- **App nativa en la barra de menú** — inicia sola con tu Mac, sin mantener terminal abierta
- **Compatible con cualquier aplicación** — el texto se pega donde esté el cursor
- **Dos formas de grabar:** mantén `Ctrl+Option` (push-to-talk) o doble toque en `Ctrl` para modo continuo
- **Indicador visual flotante** — muestra las barras de audio en tiempo real mientras grabas
- **No interrumpe tu trabajo** — el indicador flota sin robar el foco de tu ventana activa
- **Pegado automático** — el resultado aparece exactamente donde estabas escribiendo
- **Historial accesible desde el navegador** en `localhost:5678`
- **Almacenamiento 100% local** en SQLite — ninguna transcripción sale de tu equipo
- **Todos los idiomas** que soporta Whisper: español, inglés, francés y más
- **Configuración al primer lanzamiento** — te solicita la API key la primera vez

---

## Instalación

### Requisitos previos

- macOS 15 o superior
- Python 3.12 o superior
- [Homebrew](https://brew.sh) instalado
- [API key de Groq](https://console.groq.com/keys) — el registro es gratuito

---

### Opción A — Instalar como app de escritorio (recomendado)

```bash
git clone https://github.com/eudomar3004/AFlow.git
cd AFlow

brew install portaudio

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

bash build.sh
```

Luego copia la app a la carpeta Aplicaciones:

```bash
ditto dist/AFlow.app /Applications/AFlow.app
xattr -cr /Applications/AFlow.app
```

> Usa `ditto` y no `cp -r` — es necesario para que macOS preserve los atributos correctamente.

Busca "AFlow" en Spotlight para abrirla. Al primer inicio te pedirá tu [Groq API key](https://console.groq.com/keys).

---

### Opción B — Ejecutar en modo desarrollo

```bash
git clone https://github.com/eudomar3004/AFlow.git
cd AFlow

brew install portaudio

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Abre el archivo .env y pega tu GROQ_API_KEY

python3 main.py
```

---

## Permisos necesarios en macOS

| Permiso | Dónde activarlo |
|---------|-----------------|
| **Accesibilidad** | Configuración del Sistema → Privacidad y Seguridad → Accesibilidad |
| **Micrófono** | Se solicita automáticamente en el primer uso |

> Sin el permiso de Accesibilidad, el pegado automático no funcionará.

---

## Atajos de teclado

| Acción | Atajo |
|--------|-------|
| Grabar mientras mantienes presionado | `Ctrl + Option` |
| Iniciar grabación continua | Doble toque en `Ctrl` |
| Detener grabación continua | Un toque en `Ctrl` |
| Ver historial de transcripciones | Abre `localhost:5678` en el navegador |

---

## Costo estimado por uso

| Uso diario | Estimado mensual |
|------------|------------------|
| 30 minutos | ~$0.30 |
| 1 hora | ~$0.60 |
| 2 horas | ~$1.20 |
| 4 horas | ~$2.40 |

El tier gratuito de Groq cubre perfectamente el uso casual.

---

## Organización del código

```
AFlow/
├── main.py                  # Entrada: menú, configuración inicial, lógica principal
├── config.py                # Rutas, valores de UI y parámetros de audio
├── core/
│   ├── recorder.py          # Grabación de audio con sounddevice
│   ├── transcriber.py       # Envío de audio a Groq y recepción del texto
│   ├── hotkey.py            # Detección de atajos de teclado globales
│   └── clipboard.py         # Preservar ventana activa + paste por AppleScript
├── db/
│   └── database.py          # Operaciones de lectura/escritura en SQLite
├── ui/
│   ├── pill_widget.py       # Indicador flotante nativo de macOS (PyObjC)
│   └── audio_visualizer.py  # Visualización del nivel de audio
├── web/
│   └── server.py            # Servidor Flask para el historial en localhost:5678
├── requirements.txt
├── .env.example
└── build.sh
```

---

## Licencia

MIT — Creado por [Eudomar Toribio](https://github.com/eudomar3004).  
Puedes usarlo, modificarlo y redistribuirlo libremente.

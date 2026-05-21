#!/bin/bash
# build.sh — Build AFlow.app from source (one shot)
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== AFlow Build ==="
echo ""

# --- Step 1: Generate .icns if missing ---
echo "[1/5] Icono..."
if [ ! -f "AFlow.icns" ]; then
    ICONSET="AFlow.iconset"
    mkdir -p "$ICONSET"
    for size in 16 32 64 128 256 512; do
        sips -z $size $size logo.png --out "$ICONSET/icon_${size}x${size}.png" > /dev/null 2>&1
        double=$((size * 2))
        sips -z $double $double logo.png --out "$ICONSET/icon_${size}x${size}@2x.png" > /dev/null 2>&1
    done
    iconutil -c icns "$ICONSET" -o AFlow.icns
    rm -rf "$ICONSET"
    echo "   AFlow.icns creado."
else
    echo "   AFlow.icns ya existe."
fi

# --- Step 2: Activate venv ---
echo "[2/5] Venv + PyInstaller..."
source venv/bin/activate
pip install pyinstaller --quiet 2>/dev/null

# --- Step 3: Clean ---
echo "[3/5] Limpiando builds anteriores..."
rm -rf build/ dist/

# --- Step 4: Build ---
echo "[4/5] Construyendo .app (esto toma ~1-2 min)..."
pyinstaller aflow.spec --noconfirm 2>&1 | tail -5

# --- Step 5: Sign ---
echo "[5/5] Firmando..."
codesign --force --deep --sign - dist/AFlow.app 2>/dev/null
codesign --verify --deep --strict dist/AFlow.app 2>/dev/null && echo "   Firma OK." || echo "   Firma: warning (puede funcionar igual)."

echo ""
echo "=== BUILD COMPLETO ==="
echo ""
echo "  Archivo:   $(pwd)/dist/AFlow.app"
echo "  Tamano:    $(du -sh dist/AFlow.app | cut -f1)"
echo ""
echo "  Para instalar:"
echo "    ditto dist/AFlow.app /Applications/AFlow.app"
echo ""
echo "  IMPORTANTE: Usar 'ditto' (no 'cp -r') para preservar metadata del bundle."
echo ""

# Open dist folder
open dist/

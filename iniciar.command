#!/usr/bin/env bash
# =====================================================================
# MarkItDown Studio - Lanzador de 1 Clic para macOS y Linux
# =====================================================================

# Cambiar al directorio donde se encuentra este script
cd "$(dirname "$0")" || exit 1

echo "====================================================================="
echo "                MARKITDOWN STUDIO - CONVERSOR LOCAL"
echo "    Optimizado para Claude, ChatGPT y Gemini (Ahorro de Tokens)"
echo "====================================================================="
echo ""

# 1. Comprobar si 'uv' está instalado
if command -v uv >/dev/null 2>&1; then
    echo "[OK] Gestor 'uv' detectado en macOS."
    echo "[*] Iniciando servidor y abriendo interfaz..."
    uv run python app.py
    exit 0
fi

# 2. Comprobar Python 3 en el sistema
if command -v python3 >/dev/null 2>&1; then
    echo "[INFO] Usando Python 3 del sistema..."
    if [ ! -d ".venv" ]; then
        echo "[*] Creando entorno virtual local..."
        python3 -m venv .venv
        source .venv/bin/activate
        echo "[*] Instalando dependencias necesarias (solo la primera vez)..."
        pip install -r requirements.txt
    else
        source .venv/bin/activate
    fi
    echo "[*] Iniciando servidor y abriendo interfaz..."
    python app.py
    exit 0
fi

# 3. Si no hay Python ni uv
echo ""
echo "[ERROR] No se ha encontrado Python 3 ni uv instalado en este Mac."
echo ""
echo "Para instalarlo rapidamente, puedes instalar 'uv' abriendo la Terminal y pegando:"
echo 'curl -LsSf https://astral.sh/uv/install.sh | sh'
echo ""
echo "O descargando Python desde: https://www.python.org/downloads/"
echo ""
read -p "Presiona Enter para salir..."

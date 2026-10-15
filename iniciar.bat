@echo off
chcp 65001 > nul
title MarkItDown Studio - Conversor a Markdown para LLMs
cls

echo =====================================================================
echo                MARKITDOWN STUDIO - CONVERSOR LOCAL
echo    Optimizado para Claude, ChatGPT y Gemini (Ahorro de Tokens)
echo =====================================================================
echo.

:: 1. Comprobar si existe uv instalado
where uv >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [OK] Gestor 'uv' detectado en el sistema.
    echo [*] Iniciando servidor local y abriendo interfaz...
    uv run python app.py
    goto end
)

:: 2. Si no hay uv, comprobar Python estándar
where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [INFO] 'uv' no detectado, usando instalacion de Python del sistema.
    if not exist .venv (
        echo [*] Creando entorno virtual local...
        python -m venv .venv
        call .venv\Scripts\activate.bat
        echo [*] Instalando dependencias necesarias (esto solo ocurre la primera vez)...
        pip install -r requirements.txt
    ) else (
        call .venv\Scripts\activate.bat
    )
    echo [*] Iniciando servidor local y abriendo interfaz...
    python app.py
    goto end
)

:: 3. Si no hay ni uv ni Python
echo.
echo [ERROR] No se ha encontrado Python ni uv instalado en este equipo.
echo.
echo Para ejecutar MarkItDown Studio en este equipo:
echo 1. Descarga e instala Python desde: https://www.python.org/downloads/
echo    (Recuerda marcar la casilla 'Add python.exe to PATH' durante la instalacion)
echo.
echo 2. O instala 'uv' ejecutando en PowerShell:
echo    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
echo.
echo Una vez instalado, vuelve a hacer doble clic en 'iniciar.bat'.
echo.
pause

:end

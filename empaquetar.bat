@echo off
chcp 65001 > nul
title Empaquetar MarkItDown Studio para Windows
cls

echo =====================================================================
echo       COMPILANDO EJECUTABLE AUTONOMO PARA WINDOWS (.EXE)
echo =====================================================================
echo.
echo [*] Empaquetando la aplicacion junto a todos sus componentes estaticos...
echo.

uv run pyinstaller --noconfirm --onedir --windowed ^
    --name "MarkItDownStudio" ^
    --add-data "static;static" ^
    --add-data "ejemplos;ejemplos" ^
    --hidden-import "uvicorn" ^
    --hidden-import "fastapi" ^
    --hidden-import "markitdown" ^
    app.py

if %ERRORLEVEL% equ 0 (
    echo.
    echo =====================================================================
    echo [OK] Compilacion completada con exito!
    echo Puedes encontrar tu aplicacion lista para compartir en:
    echo dist\MarkItDownStudio\MarkItDownStudio.exe
    echo =====================================================================
) else (
    echo.
    echo [ERROR] Hubo un error durante la compilacion.
)

pause

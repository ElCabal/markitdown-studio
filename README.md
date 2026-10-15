# ⚡ MarkItDown Studio

**MarkItDown Studio** es una aplicación 100% local y privada para convertir archivos complejos (PDF, Word, Excel, PowerPoint, HTML, CSV, etc.) a formato **Markdown (`.md`)**, optimizado para reducir drásticamente el consumo de tokens y los costes de API en modelos como **Claude, ChatGPT y Gemini**.

---

## 🚀 Cómo Iniciar la Aplicación (1 Clic)

Simplemente haz **doble clic en el archivo `iniciar.bat`**.

El script se encargará automáticamente de:
1. Detectar si tienes `uv` o `Python` en el equipo.
2. Configurar el entorno con todas las dependencias necesarias.
3. Iniciar el servidor local en `http://localhost:8000`.
4. Abrir tu navegador web predeterminado automáticamente.

---

## 📦 Cómo Compartir esta Aplicación con Cualquier Persona

Para compartir esta herramienta con un compañero de trabajo, amigo o cliente:

1. **Opción 1: Comprimir la carpeta completa**
   - Comprime la carpeta `markitdown-studio` en un archivo `.zip`.
   - La otra persona solo necesita descomprimir y hacer doble clic en `iniciar.bat`.
   - Si la persona tiene Python o `uv` instalado, funcionará de inmediato.

2. **Opción 2: Generar un archivo ejecutable `.exe` único (Portable)**
   - Si deseas generar un único archivo `.exe` que no requiera instalar Python ni nada adicional:
   ```powershell
   uv add pyinstaller
   uv run pyinstaller --noconfirm --onedir --windowed --add-data "static;static" app.py
   ```

---

## ✨ Funcionalidades Incluidas en este MVP

- 📁 **Modo Carpeta y Archivos Locales:** Selecciona una carpeta completa o archivos individuales usando el explorador nativo de Windows.
- 🎯 **Arrastrar y Soltar (Drag & Drop):** Suelta documentos sueltos, archivos comprimidos (.zip) o carpetas directamente en la ventana.
- 🔗 **Conversión de URLs y Videos de YouTube:** Pega cualquier enlace de YouTube o página web para extraer la transcripción o el artículo en Markdown estructurado.
- 📂 **Selector de Carpeta Destino:** Elige en qué carpeta de tu disco guardar automáticamente los `.md`.
- 👁️ **Vista Previa en Vivo (Live Preview):**
  - **Vista Renderizada:** Con títulos jerárquicos, tablas formateadas, bloques de código y listas.
  - **Vista Markdown Plano:** Visualiza el texto exacto con tipografía monoespaciada.
- 📊 **Métricas de Ahorro y Tokens:**
  - Tamaño original vs. Tamaño Markdown.
  - Porcentaje real de ahorro de peso (ej. `-85.4%`).
  - Estimación precisa de tokens de entrada para LLMs.
- 📋 **Copiado al Portapapeles:** Copia el Markdown de cualquier documento con un solo clic.
- 📦 **Exportación en Lote y Descarga ZIP:** Descarga todos los documentos procesados en un solo archivo comprimido.
- 🛡️ **100% Offline & Privado:** Ningún dato se envía a servidores externos; todo el procesamiento ocurre dentro de tu máquina.

---

## 📄 Formatos Soportados

| Categoría | Extensiones |
| :--- | :--- |
| **Documentos** | `.pdf`, `.docx`, `.doc`, `.txt`, `.epub` |
| **Hojas de Cálculo** | `.xlsx`, `.xls`, `.csv`, `.tsv` |
| **Presentaciones** | `.pptx`, `.ppt` |
| **Web y Datos** | `.html`, `.htm`, `.json`, `.xml`, `.ipynb` |
| **Mensajes y Audio** | `.msg`, `.wav`, `.mp3` |

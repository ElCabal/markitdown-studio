import os
import io
import time
import zipfile
import asyncio
from pathlib import Path
from typing import List, Optional
import tkinter as tk
from tkinter import filedialog

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from pydantic import BaseModel
from markitdown import MarkItDown

app = FastAPI(title="MarkItDown Studio", version="1.0.0")

# Instancia global de MarkItDown
converter = MarkItDown()

# Extensiones reconocidas por MarkItDown
SUPPORTED_EXTENSIONS = {
    ".pdf", ".docx", ".pptx", ".xlsx", ".xls", ".csv", ".tsv",
    ".html", ".htm", ".json", ".xml", ".txt", ".log", ".md",
    ".epub", ".ipynb", ".msg", ".wav", ".mp3", ".png", ".jpg", ".jpeg", ".zip"
}

def estimate_tokens(text: str) -> int:
    """Estimación estándar para LLMs: ~3.8 caracteres por token."""
    if not text:
        return 0
    return max(1, int(len(text) / 3.8))

def format_bytes(num_bytes: int) -> str:
    """Formatea bytes a KB o MB legibles."""
    if num_bytes < 1024:
        return f"{num_bytes} B"
    elif num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KB"
    else:
        return f"{num_bytes / (1024 * 1024):.2f} MB"

def _dialog_ask_directory(title: str = "Seleccionar Carpeta") -> str:
    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        folder = filedialog.askdirectory(title=title)
        root.destroy()
        return folder or ""
    except Exception as e:
        print(f"Error abriendo diálogo de carpeta: {e}")
        return ""

def _dialog_ask_files(title: str = "Seleccionar Archivo(s)") -> List[str]:
    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        files = filedialog.askopenfilenames(
            title=title,
            filetypes=[
                ("Todos los soportados", "*.pdf;*.docx;*.pptx;*.xlsx;*.xls;*.csv;*.html;*.json;*.txt;*.epub"),
                ("Documentos PDF", "*.pdf"),
                ("Office Word", "*.docx"),
                ("Office Excel", "*.xlsx;*.xls;*.csv"),
                ("Office PowerPoint", "*.pptx"),
                ("Todos los archivos", "*.*")
            ]
        )
        root.destroy()
        return list(files) if files else []
    except Exception as e:
        print(f"Error abriendo diálogo de archivos: {e}")
        return []

# --- Modelos de Petición ---
class ScanFolderRequest(BaseModel):
    folder_path: str
    recursive: bool = False
    extensions: Optional[List[str]] = None

class ConvertLocalFilesRequest(BaseModel):
    file_paths: List[str]
    output_folder: Optional[str] = None

class ConvertUrlRequest(BaseModel):
    url: str
    output_folder: Optional[str] = None

# Almacén temporal en memoria para descargas ZIP de la última sesión
session_converted_files = {}

# --- Rutas de Exploración Nativa (Windows) ---
@app.post("/api/dialog/select-folder")
async def select_folder_dialog(title: str = "Seleccionar Carpeta"):
    folder = await asyncio.to_thread(_dialog_ask_directory, title)
    return {"path": folder}

@app.post("/api/dialog/select-files")
async def select_files_dialog():
    files = await asyncio.to_thread(_dialog_ask_files, "Seleccionar Archivo(s)")
    return {"files": files}

# --- Escanear Carpeta Local ---
@app.post("/api/scan-folder")
async def scan_folder(req: ScanFolderRequest):
    folder = Path(req.folder_path)
    if not folder.exists() or not folder.is_dir():
        raise HTTPException(status_code=400, detail="La ruta especificada no existe o no es una carpeta.")

    allowed_exts = set(ext.lower() for ext in req.extensions) if req.extensions else SUPPORTED_EXTENSIONS

    found_files = []
    pattern = "**/*" if req.recursive else "*"

    for item in folder.glob(pattern):
        if item.is_file():
            ext = item.suffix.lower()
            if ext in allowed_exts:
                try:
                    size = item.stat().st_size
                    found_files.append({
                        "name": item.name,
                        "path": str(item.resolve()),
                        "rel_path": str(item.relative_to(folder)),
                        "size_bytes": size,
                        "size_formatted": format_bytes(size),
                        "extension": ext
                    })
                except Exception:
                    continue

    return {
        "folder": str(folder.resolve()),
        "total_files": len(found_files),
        "files": found_files
    }

# --- Conversión de Archivos Locales ---
@app.post("/api/convert/local")
async def convert_local(req: ConvertLocalFilesRequest):
    out_dir = Path(req.output_folder) if req.output_folder else None
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)

    results = []
    global session_converted_files
    session_converted_files.clear()

    for file_str in req.file_paths:
        file_path = Path(file_str)
        if not file_path.exists() or not file_path.is_file():
            results.append({
                "file_path": file_str,
                "name": file_path.name,
                "success": False,
                "error": "El archivo no existe"
            })
            continue

        original_size = file_path.stat().st_size
        t0 = time.time()

        try:
            # Conversión mediante MarkItDown
            res = converter.convert(str(file_path))
            markdown_content = res.text_content or res.markdown or ""
            elapsed = time.time() - t0

            md_bytes = len(markdown_content.encode("utf-8"))
            tokens = estimate_tokens(markdown_content)

            # Cálculo de ahorro
            savings_pct = 0.0
            if original_size > 0:
                savings_pct = max(0.0, round((1.0 - (md_bytes / original_size)) * 100, 1))

            saved_path = None
            if out_dir:
                out_filename = file_path.stem + ".md"
                target_file = out_dir / out_filename
                # Evitar colisión si existe
                counter = 1
                while target_file.exists():
                    target_file = out_dir / f"{file_path.stem}_{counter}.md"
                    counter += 1
                
                target_file.write_text(markdown_content, encoding="utf-8")
                saved_path = str(target_file.resolve())

            # Guardar en memoria para previsualización / descarga rápida
            session_converted_files[file_path.name] = {
                "name": file_path.name,
                "markdown": markdown_content,
                "md_size_bytes": md_bytes
            }

            results.append({
                "file_path": str(file_path),
                "name": file_path.name,
                "success": True,
                "original_size": original_size,
                "original_size_formatted": format_bytes(original_size),
                "md_size_bytes": md_bytes,
                "md_size_formatted": format_bytes(md_bytes),
                "savings_pct": savings_pct,
                "estimated_tokens": tokens,
                "elapsed_seconds": round(elapsed, 2),
                "saved_path": saved_path,
                "markdown": markdown_content
            })
        except Exception as e:
            results.append({
                "file_path": str(file_path),
                "name": file_path.name,
                "success": False,
                "error": str(e)
            })

    return {"results": results}

# --- Conversión de Archivos Subidos (Drag & Drop / Input) ---
@app.post("/api/convert/upload")
async def convert_upload(
    files: List[UploadFile] = File(...),
    output_folder: Optional[str] = Form(None)
):
    out_dir = Path(output_folder) if output_folder and output_folder.strip() else None
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)

    results = []
    global session_converted_files

    for upload in files:
        file_name = upload.filename or "documento"
        content = await upload.read()
        original_size = len(content)
        t0 = time.time()

        try:
            # MarkItDown soporta streams mediante convert_stream
            file_stream = io.BytesIO(content)
            # Deducir extensión para el stream
            ext = Path(file_name).suffix.lower()
            res = converter.convert_stream(file_stream, file_extension=ext)
            markdown_content = res.text_content or res.markdown or ""
            elapsed = time.time() - t0

            md_bytes = len(markdown_content.encode("utf-8"))
            tokens = estimate_tokens(markdown_content)

            savings_pct = 0.0
            if original_size > 0:
                savings_pct = max(0.0, round((1.0 - (md_bytes / original_size)) * 100, 1))

            saved_path = None
            if out_dir:
                stem = Path(file_name).stem
                target_file = out_dir / f"{stem}.md"
                counter = 1
                while target_file.exists():
                    target_file = out_dir / f"{stem}_{counter}.md"
                    counter += 1
                target_file.write_text(markdown_content, encoding="utf-8")
                saved_path = str(target_file.resolve())

            session_converted_files[file_name] = {
                "name": file_name,
                "markdown": markdown_content,
                "md_size_bytes": md_bytes
            }

            results.append({
                "name": file_name,
                "success": True,
                "original_size": original_size,
                "original_size_formatted": format_bytes(original_size),
                "md_size_bytes": md_bytes,
                "md_size_formatted": format_bytes(md_bytes),
                "savings_pct": savings_pct,
                "estimated_tokens": tokens,
                "elapsed_seconds": round(elapsed, 2),
                "saved_path": saved_path,
                "markdown": markdown_content
            })
        except Exception as e:
            results.append({
                "name": file_name,
                "success": False,
                "error": str(e)
            })

    return {"results": results}

# --- Conversión de URLs (YouTube / Enlaces Web) ---
@app.post("/api/convert/url")
async def convert_url(req: ConvertUrlRequest):
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL no válida")

    t0 = time.time()
    try:
        res = converter.convert(url)
        markdown_content = res.text_content or res.markdown or ""
        elapsed = time.time() - t0

        md_bytes = len(markdown_content.encode("utf-8"))
        tokens = estimate_tokens(markdown_content)

        # Generar nombre amigable basado en título o URL
        item_title = getattr(res, "title", None) or "transcripcion_youtube"
        # Limpiar caracteres inválidos para nombre de archivo en Windows
        safe_name = "".join(c for c in item_title if c.isalnum() or c in (" ", "_", "-")).strip()[:50]
        if not safe_name:
            safe_name = "url_convertida"
        file_name = f"{safe_name}.md"

        saved_path = None
        if req.output_folder:
            out_dir = Path(req.output_folder)
            out_dir.mkdir(parents=True, exist_ok=True)
            target_file = out_dir / file_name
            target_file.write_text(markdown_content, encoding="utf-8")
            saved_path = str(target_file.resolve())

        session_converted_files[file_name] = {
            "name": file_name,
            "markdown": markdown_content,
            "md_size_bytes": md_bytes
        }

        return {
            "results": [{
                "name": file_name,
                "success": True,
                "original_size": md_bytes * 5, # Estimación del contenido original multimedia
                "original_size_formatted": "Video / Web",
                "md_size_bytes": md_bytes,
                "md_size_formatted": format_bytes(md_bytes),
                "savings_pct": 90.0,
                "estimated_tokens": tokens,
                "elapsed_seconds": round(elapsed, 2),
                "saved_path": saved_path,
                "markdown": markdown_content
            }]
        }
    except Exception as e:
        return {
            "results": [{
                "name": url,
                "success": False,
                "error": str(e)
            }]
        }

# --- Descarga en ZIP de todos los convertidos ---
@app.get("/api/download-zip")
async def download_zip():
    global session_converted_files
    if not session_converted_files:
        raise HTTPException(status_code=400, detail="No hay archivos convertidos en la sesión actual.")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for orig_name, data in session_converted_files.items():
            out_name = Path(orig_name).stem + ".md"
            zf.writestr(out_name, data["markdown"].encode("utf-8"))

    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=markitdown_conversiones.zip"}
    )

# --- Montar Archivos Estáticos (Frontend) ---
static_path = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

@app.get("/")
async def root():
    return FileResponse(str(static_path / "index.html"))

if __name__ == "__main__":
    import uvicorn
    import webbrowser
    import threading

    def open_browser():
        time.sleep(1.2)
        webbrowser.open("http://127.0.0.1:8000")

    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)

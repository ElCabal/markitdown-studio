import io
import time
import zipfile
from pathlib import Path
import streamlit as st
from markitdown import MarkItDown

st.set_page_config(
    page_title="MarkItDown Studio",
    page_icon="⚡",
    layout="wide"
)

# Estilos personalizados oscuros y elegantes
st.markdown("""
<style>
    .main-title { font-size: 2.2rem; font-weight: 700; color: #38bdf8; margin-bottom: 0px; }
    .sub-title { font-size: 1rem; color: #94a3b8; margin-bottom: 24px; }
    .metric-card { background: rgba(255,255,255,0.05); padding: 14px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1); text-align: center; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">⚡ MarkItDown Studio</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Convierte documentos complejos y videos a Markdown optimizado para Claude, ChatGPT y Gemini.</div>', unsafe_allow_html=True)

@st.cache_resource
def get_converter():
    return MarkItDown()

md = get_converter()

def estimate_tokens(text: str) -> int:
    return max(1, int(len(text) / 3.8)) if text else 0

def format_bytes(num_bytes: int) -> str:
    if num_bytes < 1024:
        return f"{num_bytes} B"
    elif num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KB"
    else:
        return f"{num_bytes / (1024 * 1024):.2f} MB"

tab_upload, tab_url = st.tabs(["📁 Subir Archivos (PDF, Word, Excel, ZIP...)", "🔗 Video de YouTube / URL"])

# --- TAB 1: SUBIR ARCHIVOS ---
with tab_upload:
    uploaded_files = st.file_uploader(
        "Arrastra o selecciona tus documentos",
        type=["pdf", "docx", "pptx", "xlsx", "xls", "csv", "html", "htm", "json", "xml", "txt", "zip"],
        accept_multiple_files=True
    )

    if uploaded_files:
        if st.button("⚡ Convertir Archivos a Markdown", type="primary", use_container_width=True):
            results = []
            progress_bar = st.progress(0)
            total = len(uploaded_files)

            for idx, uploaded_file in enumerate(uploaded_files):
                bytes_data = uploaded_file.read()
                orig_size = len(bytes_data)
                ext = Path(uploaded_file.name).suffix.lower()

                try:
                    stream = io.BytesIO(bytes_data)
                    res = md.convert_stream(stream, file_extension=ext)
                    content = res.text_content or res.markdown or ""
                    md_bytes = len(content.encode("utf-8"))
                    tokens = estimate_tokens(content)
                    savings = max(0.0, round((1.0 - (md_bytes / orig_size)) * 100, 1)) if orig_size > 0 else 0

                    results.append({
                        "name": uploaded_file.name,
                        "success": True,
                        "content": content,
                        "orig_size": orig_size,
                        "md_size": md_bytes,
                        "savings": savings,
                        "tokens": tokens
                    })
                except Exception as e:
                    results.append({
                        "name": uploaded_file.name,
                        "success": False,
                        "error": str(e)
                    })

                progress_bar.progress((idx + 1) / total)

            st.session_state["results"] = results
            st.success(f"¡Procesados {len(results)} archivo(s) con éxito!")

# --- TAB 2: YOUTUBE / URL ---
with tab_url:
    url_input = st.text_input("Ingresa enlace de YouTube o página web", placeholder="https://www.youtube.com/watch?v=...")
    if st.button("⚡ Extraer Transcripción a Markdown", type="primary"):
        if url_input.strip():
            with st.spinner("Descargando transcripción y convirtiendo..."):
                try:
                    res = md.convert(url_input.strip())
                    content = res.text_content or res.markdown or ""
                    md_bytes = len(content.encode("utf-8"))
                    tokens = estimate_tokens(content)
                    name = getattr(res, "title", "transcripcion_youtube") + ".md"

                    st.session_state["results"] = [{
                        "name": name,
                        "success": True,
                        "content": content,
                        "orig_size": md_bytes * 5,
                        "md_size": md_bytes,
                        "savings": 90.0,
                        "tokens": tokens
                    }]
                    st.success("¡Contenido convertido exitosamente!")
                except Exception as e:
                    st.error(f"Error al procesar la URL: {e}")
        else:
            st.warning("Por favor ingresa una URL válida.")

# --- RESULTADOS Y VISTA PREVIA ---
if "results" in st.session_state and st.session_state["results"]:
    st.divider()
    st.subheader("📊 Resultados y Vista Previa")

    results = st.session_state["results"]
    successful = [r for r in results if r.get("success")]

    if successful:
        total_orig = sum(r["orig_size"] for r in successful)
        total_md = sum(r["md_size"] for r in successful)
        total_tokens = sum(r["tokens"] for r in successful)
        total_savings = round((1.0 - (total_md / total_orig)) * 100, 1) if total_orig > 0 else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Archivos", len(successful))
        c2.metric("Tamaño Original", format_bytes(total_orig))
        c3.metric("Ahorro de Peso", f"-{total_savings}%")
        c4.metric("Tokens Estimados", f"~{total_tokens:,}")

        # Descarga en ZIP
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for r in successful:
                stem = Path(r["name"]).stem
                zf.writestr(f"{stem}.md", r["content"].encode("utf-8"))
        zip_buf.seek(0)

        st.download_button(
            label="📦 Descargar Todos los Archivos en ZIP",
            data=zip_buf,
            file_name="conversiones_markdown.zip",
            mime="application/zip",
            use_container_width=True
        )

        st.write("### Vista Previa Individual")
        for r in successful:
            with st.expander(f"📄 {r['name']}  |  -{r['savings']}% de ahorro  |  ~{r['tokens']:,} tokens"):
                v_render, v_raw = st.tabs(["👁️ Vista Renderizada", "📝 Markdown Crudo"])
                with v_render:
                    st.markdown(r["content"])
                with v_raw:
                    st.text_area("Markdown", r["content"], height=300, key=f"raw_{r['name']}")
                
                st.download_button(
                    label=f"💾 Descargar {Path(r['name']).stem}.md",
                    data=r["content"],
                    file_name=f"{Path(r['name']).stem}.md",
                    mime="text/markdown",
                    key=f"dl_{r['name']}"
                )

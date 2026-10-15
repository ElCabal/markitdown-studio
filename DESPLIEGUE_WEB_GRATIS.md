# 🌐 Guía de Despliegue Web 100% Gratuito (Sin Tarjeta de Crédito)

Si al intentar crear un Space en Hugging Face viste que la opción **Docker** está deshabilitada y solo te aparece **Static Blank**, es completamente normal: **Hugging Face cambió sus políticas recientemente** y ahora exige ingresar una tarjeta de crédito o cuenta de pago para desbloquear contenedores Docker (para evitar abuso de servidores).

Por suerte, existen **dos alternativas 100% gratuitas reales que NO piden tarjeta de crédito** y funcionan a la perfección.

---

## 🏆 Opción 1 (La Más Rápida y Recomendada): Streamlit Community Cloud

Respaldada por **Snowflake**, esta plataforma está pensada exclusivamente para desplegar aplicaciones de Python en la web de forma **100% gratuita de por vida y sin tarjeta de crédito**.

* **Coste:** $0 / mes.
* **Memoria:** 1 GB de RAM.
* **Ventaja:** No se apaga como Render y soporta MarkItDown al 100%.
* **Archivo listo en tu proyecto:** Ya te dejé programado el archivo **[`streamlit_app.py`](./streamlit_app.py)** con la misma interfaz oscura, drag & drop, visor de Markdown y transcripción de YouTube.

### Pasos para desplegar en 2 minutos:
1. Sube tu carpeta `markitdown-studio` a un repositorio nuevo en tu cuenta de [GitHub](https://github.com).
2. Entra en **[share.streamlit.io](https://share.streamlit.io)** e inicia sesión con tu cuenta de GitHub.
3. Haz clic en el botón azul **"New app"**.
4. Configura estos 3 campos:
   * **Repository:** Selecciona tu repositorio de GitHub recién creado.
   * **Branch:** `main` (o `master`).
   * **Main file path:** Escribe `streamlit_app.py`.
5. Haz clic en **"Deploy!"**.
6. En 30-40 segundos tendrás tu enlace público con HTTPS (ejemplo: `https://markitdown-studio.streamlit.app`) listo para compartir con quien quieras.

---

## 🥈 Opción 2: Render.com (Para la Interfaz Web Original de FastAPI)

Si prefieres usar la interfaz web personalizada con diseño glassmorphism (`app.py` + `static/`), Render te permite alojarla **gratis sin tarjeta**:

1. Sube tu proyecto a un repositorio en tu [GitHub](https://github.com).
2. Entra en **[Render.com](https://render.com)** e inicia sesión con GitHub (no pide tarjeta para el plan Free).
3. Haz clic en **"New +"** y selecciona **"Web Service"**.
4. Conecta tu repositorio.
5. Configura los siguientes campos:
   * **Name:** `markitdown-studio`
   * **Environment / Runtime:** `Python 3`
   * **Build Command:** `pip install -r requirements.txt`
   * **Start Command:** `uvicorn app:app --host 0.0.0.0 --port $PORT`
   * **Instance Type:** Selecciona **Free ($0/mo)**.
6. Haz clic en **"Create Web Service"**.
* *Detalle de Render:* Al ser gratuito, si pasa 15 minutos sin visitas entra en modo reposo; cuando alguien entra después de un rato, tarda unos 30-40 segundos en encender.

---

## 🚀 Resumen: ¿Cuál elegir?
* **Si quieres la opción más estable, rápida y que nunca se duerma:** Ve con la **Opción 1 (Streamlit Community Cloud)**.
* **Si quieres mantener exactamente el diseño web oscuro que vimos antes:** Ve con la **Opción 2 (Render.com)**.

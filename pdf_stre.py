import streamlit as st
import re
import pytesseract
from pdf2image import convert_from_path
import io
import os

# --- NOTA: YA NO HAY RUTAS DE C:\ ---
# Gracias al archivo packages.txt, la nube encontrará los programas solos.

st.title("📄 Procesador de PDFs")
st.write("Sube el archivo para renombrarlo automáticamente.")

def limpiar_nombre_final(texto):
    texto = texto.replace("/", "-")
    texto = re.sub(r'[\\:*?"<>|]', "", texto)
    return " ".join(texto.split()).strip()

def completar_fecha(fecha_sucia):
    fecha = fecha_sucia.replace(" ", "").strip()
    # Si detecta formato 03/20, le pone el 2026
    if re.match(r'^\d{1,2}[/-]\d{1,2}$', fecha):
        return f"{fecha}-2026"
    return fecha

# Interfaz de subida de archivo
archivo_subido = st.file_uploader("Arrastra tu PDF aquí", type="pdf")

if archivo_subido is not None:
    try:
        with st.spinner('Leyendo datos del PDF...'):
            # Guardamos el archivo temporalmente para que la librería pueda leerlo
            with open("temp.pdf", "wb") as f:
                f.write(archivo_subido.getbuffer())

            # --- PROCESO OCR ---
            # Nota: quitamos el parámetro poppler_path porque en la nube es automático
            paginas = convert_from_path("temp.pdf")
            texto_ocr = pytesseract.image_to_string(paginas[0], lang='spa+eng')

            # --- BÚSQUEDA DE DATOS ---
            match_loc = re.search(r'(?i)(?:Location|Ubicación|Ubicacion)[:\s-]+(.+)', texto_ocr)
            match_fec = re.search(r'(?i)(?:Date|Fecha)[:\s-]+(.+)', texto_ocr)

            # Procesar Ubicación
            ubi_raw = match_loc.group(1).strip() if match_loc else "Sin_Ubicacion"
            
            # Procesar Fecha
            if match_fec:
                fec_raw = match_fec.group(1).strip()
                fecha_procesada = completar_fecha(fec_raw)
            else:
                fecha_procesada = "Sin_Fecha"

            # Nombre final limpio
            nombre_final = limpiar_nombre_final(f"{ubi_raw} - {fecha_procesada}.pdf")

            st.success("✅ Análisis completado")
            st.info(f"📍 **Ubicación:** {ubi_raw}\n\n📅 **Fecha:** {fecha_procesada}")

            # Botón de descarga para el usuario
            with open("temp.pdf", "rb") as f:
                st.download_button(
                    label="📥 Descargar PDF con nombre correcto",
                    data=f,
                    file_name=nombre_final,
                    mime="application/pdf"
                )
            
            # Limpiar el archivo temporal
            os.remove("temp.pdf")

    except Exception as e:
        st.error(f"Hubo un fallo: {e}")
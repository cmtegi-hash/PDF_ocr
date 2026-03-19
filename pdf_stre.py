import streamlit as st
import re
import pytesseract
from pdf2image import convert_from_path
import os
import zipfile
from io import BytesIO

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="PDF Smart Renamer", page_icon="📂", layout="wide")

# --- LÓGICA DE LIMPIEZA ---
def limpiar_ubicacion_estricto(texto):
    # 1. Quitar saltos de línea
    texto = texto.replace("\n", " ").replace("\r", " ")
    
    # 2. FRENO DE MANO: Cortar si aparecen estas palabras
    palabras_freno = [r'\bArea\b', r'\bStatus\b', r'\bNotes?\b', r'\bWork\b', r'\bDate\b', r'\bTotal\b']
    
    for palabra in palabras_freno:
        corte = re.split(palabra, texto, flags=re.IGNORECASE)
        texto = corte[0]
    
    # 3. Limpieza de caracteres prohibidos en Windows
    texto = re.sub(r'[\\:*?"<>|]', "", texto)
    return " ".join(texto.split()).strip()

def extraer_info(pdf_file):
    # Guardar archivo temporalmente para que la librería lo procese
    with open("temp.pdf", "wb") as f:
        f.write(pdf_file.getbuffer())
    
    try:
        # Convertir PDF a Imagen (Primera página)
        paginas = convert_from_path("temp.pdf")
        texto_ocr = pytesseract.image_to_string(paginas[0], lang='spa+eng')
        
        # --- BUSCADORES ---
        patron_fec = r'(?i)(?:Work\s*Date(?:\(s\))?|Restoration|Date)[:\s\.]+(\d{1,2}[/-]\d{1,2})'
        patron_loc = r'(?i)(?:Location|Ubicación|Ubicacion)[:\s-]+(.+)'
        
        m_fec = re.search(patron_fec, texto_ocr)
        m_loc = re.search(patron_loc, texto_ocr)
        
        # Procesar Ubicación con limpieza profunda
        ubi_sucia = m_loc.group(1).strip() if m_loc else "Sin_Ubicacion"
        ubi_limpia = limpiar_ubicacion_estricto(ubi_sucia)
        
        # Procesar Fecha (MM-DD-2026)
        if m_fec:
            fec_corta = m_fec.group(1).replace('/', '-')
            fec_final = f"{fec_corta}-2026"
        else:
            fec_final = "Sin_Fecha"
        
        return f"{ubi_limpia} - {fec_final}.pdf", ubi_limpia, fec_final
    
    finally:
        # Siempre borrar el temporal para no saturar el servidor
        if os.path.exists("temp.pdf"):
            os.remove("temp.pdf")

# --- INTERFAZ LATERAL ---
st.sidebar.title("⚙️ Opciones")
modo = st.sidebar.radio("Selecciona el modo:", ["Archivo Individual", "Procesamiento Masivo (ZIP)"])

st.title("📄 Smart PDF Renamer")
st.write(f"Modo seleccionado: **{modo}**")

# --- MODO INDIVIDUAL ---
if modo == "Archivo Individual":
    archivo = st.file_uploader("Sube un PDF", type="pdf", key="single")
    if archivo:
        with st.spinner("Analizando documento..."):
            nombre_final, ubi, fec = extraer_info(archivo)
            st.success(f"📍 Detectado: {ubi} | 📅 {fec}")
            st.download_button("📥 Descargar PDF Renombrado", archivo.getvalue(), file_name=nombre_final)

# --- MODO MASIVO ---
else:
    archivos = st.file_uploader("Sube múltiples PDFs", type="pdf", accept_multiple_files=True, key="multi")
    if archivos:
        if st.button("🚀 Iniciar Proceso Masivo"):
            zip_buffer = BytesIO()
            progreso = st.progress(0)
            status = st.empty()
            lista_final = []
            
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_f:
                for i, f in enumerate(archivos):
                    status.text(f"Procesando ({i+1}/{len(archivos)}): {f.name}")
                    nombre_nuevo, _, _ = extraer_info(f)
                    zip_f.writestr(nombre_nuevo, f.getvalue())
                    lista_final.append(nombre_nuevo)
                    progreso.progress((i + 1) / len(archivos))
            
            status.success("✅ ¡Proceso completado con éxito!")
            st.download_button("📥 Descargar todos en un ZIP", zip_buffer.getvalue(), file_name="PDFs_Procesados.zip")
            
            with st.expander("Ver lista de nombres generados"):
                for n in lista_final:
                    st.write(f"• {n}")

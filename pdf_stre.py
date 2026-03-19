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
    texto = texto.replace("\n", " ").replace("\r", " ")
    # Palabras que detienen la lectura (Freno de mano)
    palabras_freno = [r'\bArea\b', r'\bStatus\b', r'\bNotes?\b', r'\bWork\b', r'\bDate\b', r'\bTotal\b']
    for palabra in palabras_freno:
        corte = re.split(palabra, texto, flags=re.IGNORECASE)
        texto = corte[0]
    texto = re.sub(r'[\\:*?"<>|]', "", texto)
    return " ".join(texto.split()).strip()

def extraer_info(pdf_file):
    with open("temp.pdf", "wb") as f:
        f.write(pdf_file.getbuffer())
    
    paginas = convert_from_path("temp.pdf")
    texto_ocr = pytesseract.image_to_string(paginas[0], lang='spa+eng')
    
    patron_fec = r'(?i)(?:Work\s*Date(?:\(s\))?|Restoration|Date)[:\s\.]+(\d{1,2}[/-]\d{1,2})'
    patron_loc = r'(?i)(?:Location|Ubicación|Ubicacion)[:\s-]+(.+)'
    
    m_fec = re.search(patron_fec, texto_ocr)
    m_loc = re.search(patron_loc, texto_ocr)
    
    ubi = limpiar_ubicacion_estricto(m_loc.group(1)) if m_loc else "Sin_Ubicacion"
    fec = f"{m_fec.group(1).replace('/', '-')}-2026" if m_fec else "Sin_Fecha"
    
    os.remove("temp.pdf")
    return f"{ubi} - {fec}.pdf", ubi, fec

# --- INTERFAZ LATERAL (OPCIONES) ---
st.sidebar.title("⚙️ Configuración")
modo = st.sidebar.radio("Selecciona el modo:", ["Archivo Individual", "Procesamiento Masivo (ZIP)"])

st.title("📄 Smart PDF Renamer")
st.write(f"Modo actual: **{modo}**")

# --- MODO INDIVIDUAL ---
if modo == "Archivo Individual":
    archivo = st.file_uploader("Sube un PDF", type="pdf", key="single")
    if archivo:
        with st.spinner("Procesando..."):
            nombre_final, ubi, fec = extraer_info(archivo)
            st.success(f"✅ Detectado: {ubi}")
            st.download_button("📥 Descargar PDF Renombrado", archivo.getvalue(), file_name=nombre_final)

# --- MODO MASIVO ---
else:
    archivos = st.file_uploader("Sube múltiples PDFs", type="pdf", accept_multiple_files=True, key="multi")
    if archivos:
        if st.button("🚀 Iniciar Proceso Masivo"):
            zip_buffer = BytesIO()
            progreso = st.progress(0)
            lista_nombres = []
            
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zip_file:
                for i, f in enumerate(archivos):
                    nombre_final, _, _ = extraer_info(f)
                    zip_file.writestr(nombre_final, f.getvalue())
                    lista_nombres.append(nombre_final)
                    progreso.progress((i + 1) / len(archivos))
            
            st.success(f"✅ {len(archivos)} archivos procesados.")
            st.download_button("📥 Descargar todo en un ZIP", zip_buffer.getvalue(), file_name="PDFs_Procesados.zip")
            
            with st.expander("Ver lista de archivos renombrados"):
                for n in lista_nombres:
                    st.write(f"• {n}")import streamlit as st
import re
import pytesseract
from pdf2image import convert_from_path
import os

# --- INTERFAZ WEB ---
st.set_page_config(page_title="PDF Smart Renamer", page_icon="📄")
st.title("🚀 Procesador de PDFs (Windows & Mac)")
st.write("Sube tus archivos y el sistema los renombrará automáticamente.")

# --- LÓGICA DE LIMPIEZA ---
def limpiar_ubicacion_estricto(texto):
    # 1. Quitar saltos de línea
    texto = texto.replace("\n", " ").replace("\r", " ")
    
    # 2. FRENO DE MANO: Cortar si aparecen estas palabras
    palabras_freno = [r'\bArea\b', r'\bStatus\b', r'\bNotes?\b', r'\bWork\b', r'\bDate\b']
    
    for palabra in palabras_freno:
        corte = re.split(palabra, texto, flags=re.IGNORECASE)
        texto = corte[0]
    
    # 3. Limpieza de caracteres prohibidos
    texto = re.sub(r'[\\:*?"<>|]', "", texto)
    return " ".join(texto.split()).strip()

# --- PROCESAMIENTO ---
archivo_subido = st.file_uploader("Elige un archivo PDF", type="pdf")

if archivo_subido:
    with st.spinner("Analizando documento..."):
        # Guardar temporal para procesar
        with open("temp.pdf", "wb") as f:
            f.write(archivo_subido.getbuffer())
        
        try:
            # Convertir a imagen (En la nube no lleva poppler_path)
            paginas = convert_from_path("temp.pdf")
            texto_ocr = pytesseract.image_to_string(paginas[0], lang='spa+eng')
            
            # --- BUSCADORES ---
            patron_fec = r'(?i)(?:Work\s*Date(?:\(s\))?|Restoration|Date)[:\s\.]+(\d{1,2}[/-]\d{1,2})'
            patron_loc = r'(?i)(?:Location|Ubicación|Ubicacion)[:\s-]+(.+)'

            m_fec = re.search(patron_fec, texto_ocr)
            m_loc = re.search(patron_loc, texto_ocr)

            # Extraer y Limpiar
            ubi_sucia = m_loc.group(1).strip() if m_loc else "Sin_Ubicacion"
            ubi_limpia = limpiar_ubicacion_estricto(ubi_sucia)
            
            if m_fec:
                fecha_corta = m_fec.group(1).replace("/", "-")
                fecha_final = f"{fecha_corta}-2026"
            else:
                fecha_final = "Sin_Fecha"

            nombre_final = f"{ubi_limpia} - {fecha_final}.pdf"

            # --- RESULTADOS ---
            st.success("✅ ¡Procesado con éxito!")
            st.info(f"📍 **Ubicación detectada:** {ubi_limpia}\n\n📅 **Fecha detectada:** {fecha_final}")
            
            # Botón de descarga
            with open("temp.pdf", "rb") as f:
                st.download_button(
                    label="📥 Descargar PDF Renombrado",
                    data=f,
                    file_name=nombre_final,
                    mime="application/pdf"
                )
            
            os.remove("temp.pdf") # Borrar rastro

        except Exception as e:
            st.error(f"Error técnico: {e}")

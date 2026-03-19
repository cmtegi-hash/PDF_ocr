import streamlit as st
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

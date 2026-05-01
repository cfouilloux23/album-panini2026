import streamlit as st
import pandas as pd
from supabase import create_client

# -------------------------
# CONFIG SUPABASE
# -------------------------
url = "https://pbogddjphxhilwiqbulq.supabase.co"
key = "sb_publishable_ABtEce9FyxzepSoAkQstWw_zLnRbJrr"
supabase = create_client(url, key)

# -------------------------
# GENERACIÓN DE LISTA MAESTRA
# -------------------------
paises = [
    "MEX", "RSA", "CZE", "BIH", "SUI", "MARR", "SCO", "PAR", "TUR", "CUW", 
    "ECU", "JPN", "TUN", "BEL", "IRN", "ESP", "KSA", "FRA", "IRQ", "ARG", 
    "AUT", "POR", "UZB", "ENG", "GHA", "KOR", "CAN", "QAT", "BRA", "HAI", 
    "USA", "AUS", "GER", "CIV", "NED", "SWE", "EGY", "NZL", "CPV", "URU", 
    "SEN", "NOR", "ALG", "JOR", "COD", "COL", "CRO", "PAN"
]

# Diccionario para agrupar estampas por sección en la UI
secciones_master = {
    "ESPECIALES": ["PANINI 00"] + [f"WC {i}" for i in range(1, 9)] + [f"FWC{i}" for i in range(9, 20)],
    "COPA CONFEDERACIONES": [f"CC{i}" for i in range(1, 15)]
}
for p in paises:
    secciones_master[p] = [f"{p}{i}" for i in range(1, 21)]

# -------------------------
# UI INICIAL
# -------------------------
st.set_page_config(page_title="Álbum Checklist 2026", layout="wide")
st.title("📋 Checklist Mundial 2026")

user_input = st.text_input("👤 Usuario", placeholder="Tu nombre...")
user = user_input.strip().lower()

if not user:
    st.warning("Ingresa tu nombre para continuar.")
    st.stop()

# -------------------------
# DATA LOGIC
# -------------------------
response = supabase.table("album").select("*").eq("user_id", user).execute()
data = response.data

if len(data) == 0:
    with st.spinner("Generando álbum inicial..."):
        all_stickers = []
        for s_list in secciones_master.values():
            all_stickers.extend(s_list)
        
        batch = [{"user_id": user, "estampa": s, "tengo": 0, "repetidas": 0} for s in all_stickers]
        for i in range(0, len(batch), 500):
            supabase.table("album").insert(batch[i:i+500]).execute()
    st.rerun()

df = pd.DataFrame(data)

# -------------------------
# MÉTRICAS RÁPIDAS
# -------------------------
tienes = df["tengo"].sum()
total = len(df)
c1, c2, c3 = st.columns(3)
c1.metric("Obtenidas", f"{int(tienes)} / {total}")
c2.metric("Faltan", int(total - tienes))
c3.metric("Progreso", f"{(tienes/total)*100:.1f}%")

# -------------------------
# INTERFAZ DE CHECKLIST
# -------------------------
st.subheader("Selecciona las estampas que ya tienes:")
st.info("💡 Abre cada sección, marca tus estampas y dale al botón 'Guardar Cambios' al final.")

# Diccionario para guardar los nuevos estados temporalmente
nuevos_estados = {}

# Generar los acordeones por sección
for nombre_seccion, lista_estampas in secciones_master.items():
    with st.expander(f"📍 {nombre_seccion}"):
        # Creamos columnas para que las casillas no ocupen mucho espacio vertical
        cols = st.columns(5) 
        for index, s_id in enumerate(lista_estampas):
            # Buscar el estado actual en el dataframe
            valor_actual = bool(df[df["estampa"] == s_id]["tengo"].values[0])
            
            # Colocar el checkbox en la columna correspondiente
            with cols[index % 5]:
                check = st.checkbox(s_id, value=valor_actual, key=f"cb_{s_id}")
                nuevos_estados[s_id] = 1 if check else 0

# -------------------------
# BOTÓN DE GUARDADO MASIVO
# -------------------------
st.divider()
if st.button("💾 GUARDAR CAMBIOS EN LA NUBE", use_container_width=True, type="primary"):
    with st.spinner("Actualizando base de datos..."):
        # Solo actualizamos las que cambiaron para ahorrar recursos
        for s_id, nuevo_val in nuevos_estados.items():
            valor_viejo = int(df[df["estampa"] == s_id]["tengo"].values[0])
            if nuevo_val != valor_viejo:
                supabase.table("album").update({"tengo": nuevo_val}).eq("user_id", user).eq("estampa", s_id).execute()
    
    st.success("¡Datos actualizados correctamente! 🔥")
    st.rerun()

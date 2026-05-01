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
# DICCIONARIO DE BANDERAS (Emoji literal)
# -------------------------
# Aquí asociamos el código que usas con su bandera real
banderas = {
    "MEX": "🇲🇽", "RSA": "🇿🇦", "CZE": "🇨🇿", "BIH": "🇧🇦", "SUI": "🇨🇭", "MARR": "🇲🇦", 
    "SCO": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "PAR": "🇵🇾", "TUR": "🇹🇷", "CUW": "🇨🇼", "ECU": "🇪🇨", "JPN": "🇯🇵", 
    "TUN": "🇹🇳", "BEL": "🇧🇪", "IRN": "🇮🇷", "ESP": "🇪🇸", "KSA": "🇸🇦", "FRA": "🇫🇷", 
    "IRQ": "🇮🇶", "ARG": "🇦🇷", "AUT": "🇦🇹", "POR": "🇵🇹", "UZB": "🇺🇿", "ENG": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", 
    "GHA": "🇬🇭", "KOR": "🇰🇷", "CAN": "🇨🇦", "QAT": "🇶🇦", "BRA": "🇧🇷", "HAI": "🇭🇹", 
    "USA": "🇺🇸", "AUS": "🇦🇺", "GER": "🇩🇪", "CIV": "🇨🇮", "NED": "🇳🇱", "SWE": "🇸🇪", 
    "EGY": "🇪🇬", "NZL": "🇳🇿", "CPV": "🇨🇻", "URU": "🇺🇾", "SEN": "🇸🇳", "NOR": "🇳🇴", 
    "ALG": "🇩🇿", "JOR": "🇯🇴", "COD": "🇨🇩", "COL": "🇨🇴", "CRO": "🇭🇷", "PAN": "🇵🇦"
}

# -------------------------
# GENERACIÓN DE SECCIONES
# -------------------------
paises_lista = list(banderas.keys())

# Estructura del álbum con los rangos que me pediste
secciones_master = {
    "✨ ESPECIALES": ["PANINI 00"] + [f"WC {i}" for i in range(1, 9)] + [f"FWC{i}" for i in range(9, 20)],
    "🏆 COCA COLA": [f"CC{i}" for i in range(1, 15)]
}

# Añadimos los países con su bandera literal al título
for p in paises_lista:
    titulo = f"{banderas[p]} {p}"
    secciones_master[titulo] = [f"{p}{i}" for i in range(1, 21)]

# -------------------------
# UI STREAMLIT
# -------------------------
st.set_page_config(page_title="Álbum Mundial 2026", layout="wide")
st.title("📘 Mi Álbum Panini 2026")

user_input = st.text_input("👤 Usuario", placeholder="Escribe tu nombre...")
user = user_input.strip().lower()

if not user:
    st.info("Ingresa tu nombre para ver tus estampas.")
    st.stop()

# -------------------------
# LÓGICA DE DATOS
# -------------------------
response = supabase.table("album").select("*").eq("user_id", user).execute()
data = response.data

# Si es usuario nuevo, crear álbum
if len(data) == 0:
    with st.spinner("Creando tu álbum por primera vez..."):
        all_stickers = []
        for lista in secciones_master.values():
            all_stickers.extend(lista)
        
        batch = [{"user_id": user, "estampa": s, "tengo": 0, "repetidas": 0} for s in all_stickers]
        for i in range(0, len(batch), 500):
            supabase.table("album").insert(batch[i:i+500]).execute()
    st.rerun()

df = pd.DataFrame(data)

# Métricas
t1, t2, t3 = st.columns(3)
t1.metric("Obtenidas", f"{int(df['tengo'].sum())} / {len(df)}")
t2.metric("Repetidas", int(df['repetidas'].sum()))
t3.metric("Progreso", f"{(df['tengo'].sum()/len(df))*100:.1f}%")

st.divider()

# -------------------------
# CHECKLIST VISUAL
# -------------------------
# Variables para guardar cambios
cambios_tengo = {}
cambios_reps = {}

# Crear los acordeones (Expanders)
for seccion, lista_est in secciones_master.items():
    with st.expander(seccion):
        # 4 columnas por fila para que se vea ordenado
        cols = st.columns(4)
        for i, cod in enumerate(lista_est):
            # Obtener datos actuales de la base
            info = df[df["estampa"] == cod].iloc[0]
            
            with cols[i % 4]:
                st.write(f"**{cod}**")
                c_check, c_num = st.columns([1, 1.2])
                with c_check:
                    t = st.checkbox("T", value=bool(info["tengo"]), key=f"t_{cod}", label_visibility="collapsed")
                    cambios_tengo[cod] = 1 if t else 0
                with c_num:
                    r = st.number_input("R", min_value=0, value=int(info["repetidas"]), key=f"r_{cod}", label_visibility="collapsed")
                    cambios_reps[cod] = r
                st.write("---")

# -------------------------
# BOTÓN GUARDAR
# -------------------------
if st.button("💾 GUARDAR TODOS LOS CAMBIOS", use_container_width=True, type="primary"):
    with st.spinner("Sincronizando..."):
        for cod in cambios_tengo.keys():
            nuevo_t = cambios_tengo[cod]
            nuevo_r = cambios_reps[cod]
            
            # Solo subir a Supabase si el usuario cambió algo
            if nuevo_t != int(df[df["estampa"] == cod]["tengo"].iloc[0]) or \
               nuevo_r != int(df[df["estampa"] == cod]["repetidas"].iloc[0]):
                
                supabase.table("album").update({
                    "tengo": nuevo_t,
                    "repetidas": nuevo_r
                }).eq("user_id", user).eq("estampa", cod).execute()
    
    st.success("¡Cambios guardados con éxito! 🚀")
    st.rerun()

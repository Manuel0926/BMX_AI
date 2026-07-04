import streamlit as st  # Corregido: sintaxis limpia de importación
import sqlite3
import os
import time
import tempfile
import re
import base64
import google.generativeai as genai

# --- CONFIGURACIÓN DE LA PÁGINA NATIVA ---
st.set_page_config(
    page_title="BMX.AI Premium",
    page_icon="🚲",
    layout="wide",
    initial_sidebar_state="expanded"
)
DB_PATH = os.path.join(tempfile.gettempdir(), "epyco_usuarios.db")

# --- FUNCIÓN DE VALIDACIÓN DE EMAIL ---
def es_correo_valido(email):
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(patron, email) is not None

# --- ELIMINACIÓN ABSOLUTA DE GADGETS Y PIE DE PÁGINA DE LA NUBE ---
st.markdown("""
<style>
/* Apagar por completo la barra superior flotante original de Streamlit Cloud */
header, [data-testid="stHeader"], .stAppHeader, div[data-testid="stHeader"], [data-testid="stDecoration"], button[data-testid="stSidebarCollapseButton"] {
    visibility: hidden !important;
    display: none !important;
}

/* Ajustar el cuerpo para que comience arriba sin dejar espacios en blanco vacíos */
.stApp {
    background-color: #7CB4E6 !important;
    margin-top: -50px !important;
}

/* Ocultar la barra inferior 'Manage app' y el pie de página de la nube */
footer, [data-testid="manage_app_button"], button:has(div:contains("Manage app")), div[class*="stBottom"] > div:nth-child(2) {
    visibility: hidden !important;
    display: none !important;
}

/* Bloquear los iconos flotantes inferiores de Host y Feedback de Streamlit Cloud */
div[class*="stAppHostButton"], button[class*="stAppHostButton"], 
div[class*="stFeedbackButton"], button[class*="stFeedbackButton"],
[data-testid="stStatusWidget"], .stStatusWidget, div[class*="stConnectionStatus"] {
    visibility: hidden !important;
    display: none !important;
    pointer-events: none !important;
}

.viewerBadge, iframe[title="managed-hosted-app-badge"] {
    visibility: hidden !important;
    display: none !important;
}

/* Formato de diseño para cuando se genere la impresión física del PDF */
@media print {
    .viewerBadge, footer, button, .stChatInput, [data-testid="stSidebar"], div[class*="stBottom"], .stHorizontalBlock {
        visibility: hidden !important;
        display: none !important;
    }
    html, body, .stApp {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }
}

/* ESTILO ULTRA COMPACTO PARA EL BOTÓN PERSONALIZADO DEL SIDEBAR `<<` / `>>` */
div[data-testid="stColumn"] button {
    width: auto !important;
    min-width: 50px !important;
    padding: 4px 12px !important;
    font-weight: bold !important;
    font-size: 16px !important;
}

/* --- ESTILOS DE COLORES PREMIUM PARA TEXTO Y CONTENEDORES --- */
[data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child, [data-testid="stChatInputHoverContainer"], div[data-testid="stBottom"] > div {
    background-color: #7CB4E6 !important; 
}
html, body, p, span, label, li, h2, h3, h4, h5, h6, [data-testid="stMarkdownContainer"] p, [data-testid="stWidgetLabel"] p { 
    color: #000000 !important; 
}
.chat-header-title { 
    font-family: sans-serif !important; color: #000000 !important; font-weight: 700 !important; font-size: 2.2rem !important; border-bottom: 3px solid #000000 !important; margin-bottom: 25px; padding-bottom: 8px; display: inline-block; 
}
.sidebar-brand-title { 
    font-family: sans-serif !important; color: #000000 !important; font-weight: 700 !important; font-size: 1.45rem !important; letter-spacing: -0.5px !important; text-align: center; margin-bottom: 20px; white-space: nowrap !important; 
}
div[data-testid="stExpander"] {
    background-color: #639FD3 !important; border: 1px solid #000000 !important; border-radius: 12px !important; 
}
.sidebar-card { 
    background-color: #4B8BC2 !important; border: 1px solid #000000 !important; padding: 16px !important; border-radius: 12px !important; margin-bottom: 15px !important; 
}
.sidebar-card, .sidebar-card p, .sidebar-card span { 
    color: #000000 !important; font-weight: bold !important; 
}
.sidebar-card .badge-active, .sidebar-card .badge-active span, .badge-active { 
    color: #00FF66 !important; font-weight: 900 !important; text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5) !important; 
}

/* Mantener el esquema de color azul premium unificado en todos los botones y links */
[data-testid="baseButton-secondary"], [data-testid="baseButton-primary"], div[data-testid="stLinkButton"] a { 
    background-color: #3A75A8 !important; 
    border: 2px solid #000000 !important; 
    border-radius: 24px !important; 
    transition: all 0.25s ease !important; 
}
[data-testid="baseButton-secondary"] p, [data-testid="baseButton-primary"] p, div[data-testid="stLinkButton"] a p { 
    color: #FFFFFF !important; 
    font-weight: 600 !important; 
}
[data-testid="baseButton-secondary"]:hover, [data-testid="baseButton-primary"]:hover, div[data-testid="stLinkButton"] a:hover { 
    background-color: #0F3352 !important; 
    border-color: #FFFFFF !important; 
}
</style>
""", unsafe_allow_html=True)

# --- BLOQUEO DE AUTOCOMPLETADO NATIVO ---
st.components.v1.html("""
<script>
const stop = () => {
window.parent.document.querySelectorAll('input').forEach(el => {
el.setAttribute('autocomplete', 'off');
el.setAttribute('name', Math.random().toString(36).substring(7));
});
};
stop(); setInterval(stop, 500);
</script>
""", height=0, width=0)


class BMXWebScanner:
    def __init__(self):
        self._inicializar_db()

    def _inicializar_db(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            nombre TEXT, 
            email TEXT UNIQUE, 
            plan_suscripcion TEXT, 
            fecha_pago TEXT, 
            activo INTEGER DEFAULT 0,
            contador_ingresos INTEGER DEFAULT 0,
            fecha_registro TEXT)''')

        cursor.execute("PRAGMA table_info(usuarios)")
        columnas = [col for col in cursor.fetchall()]
        if "contador_ingresos" not in columnas:
            try:
                cursor.execute("ALTER TABLE usuarios ADD COLUMN contador_ingresos INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass
        if "fecha_registro" not in columnas:
            try:
                cursor.execute("ALTER TABLE usuarios ADD COLUMN fecha_registro TEXT")
            except sqlite3.OperationalError:
                pass
        conn.commit()
        conn.close()

    def ejecutar_sql(self, query, params):
        conn = sqlite3.connect(DB_PATH)
        conn.execute(query, params)
        conn.commit()
        conn.close()

    def configurar_api(self):
        if "GEMINI_API_KEY" in st.secrets:
            api_key_segura = st.secrets["GEMINI_API_KEY"]
        else:
            api_key_segura = os.getenv("GEMINI_API_KEY", "")

        if not api_key_segura:
            raise ValueError("No se detectó 'GEMINI_API_KEY' en los Secrets de Streamlit.")

        genai.configure(api_key=api_key_segura)

    def verificar_usuario_db(self, email):
        conn = sqlite3.connect(DB_PATH)
        user = conn.execute(
            "SELECT plan_suscripcion, activo, nombre, contador_ingresos, fecha_registro FROM usuarios WHERE email=?",
            (email.lower().strip(),)).fetchone()
        conn.close()
        return user


app = BMXWebScanner()

if "suscrito" not in st.session_state: st.session_state.suscrito = False
if "plan" not in st.session_state: st.session_state.plan = None
if "email" not in st.session_state: st.session_state.email = None
if "nombre" not in st.session_state: st.session_state.nombre = None
if "contador_ingresos" not in st.session_state: st.session_state.contador_ingresos = 0
if "fecha_registro" not in st.session_state: st.session_state.fecha_registro = ""

if "expander_login" not in st.session_state: st.session_state.expander_login = False
if "expander_registro" not in st.session_state: st.session_state.expander_registro = False

if "login_id" not in st.session_state: st.session_state.login_id = 0
if "registro_id" not in st.session_state: st.session_state.registro_id = 0

if "sidebar_visible" not in st.session_state: st.session_state.sidebar_visible = True
LOCALES = {
    "es": {
        "marca": "BMX Certificado IA", "ya_reg": "🔑 Ya estoy registrado", "mail_reg": "Email registrado:",
        "btn_val": "Validar", "err_mail": "❌ El formato del correo electrónico no es válido. Ej: usuario@dominio.com",
        "act_pend": "Usuario registrado, pero pendiente de activación.", "no_encontrado": "Email no encontrado.",
        "nuevo_reg": "📝 Nuevo Registro", "nom_com": "Nombre completo:", "corr_elec": "Correo electrónico:",
        "plan_des": "Plan deseado:", "btn_reg": "Registrar",
        "exito_reg": "✅ Registro exitoso. ¡Procede al pago si aplica!",
        "lbl_plan": "Plan:", "sel_dir": "Selecciona el Directorio de consulta",
        "cerrar_sesion": "Cerrar Sesión", "titulo_no_suscrito": "Consulta BMX Old School",
        "titulo_suscrito": "Consulta Inteligente:", "lbl_bienvenido": "Bienvenido:",
        "chat_input": "¿Qué quieres consultar hoy?",
        "spinner_vector": "Interrogando almacenes vectoriales indexados...",
        "err_consulta": "Error en consulta integrada:",
        "bienvenida_html": """
<div style="font-family: sans-serif; line-height: 1.4; background-color: #7CB4E6; padding: 15px; margin: 0 auto; color: #000000; max-width: 1000px; width: 100%;">
<h2 style="text-align: center; color: #000000; font-weight: 900; font-size: 1.6rem; margin-bottom: 20px;">¡Bienvenidos a la fuente oficial del BMX Old School!</h2>
<table style="width: 100%; border-collapse: collapse; border: none;">
<tr>
<td style="width: 50%; vertical-align: top; padding-right: 20px; border-right: 2px solid #000000;">
<p style="font-size: 0.95rem; margin-bottom: 12px;">Este es el espacio donde nuestros recuerdos hoy se convierten en <strong>pasión</strong>. Gracias al poder de la <strong>Inteligencia Artificial (modelo RAG)</strong>.</p>
</td>
<td style="width: 50%; vertical-align: top; padding-left: 20px;">
<h3 style="margin-top: 0; color: #000000; font-weight: 900; font-size: 1.2rem; margin-bottom: 10px;">¡Inicia ahora!</h3>
<p style="margin: 4px 0; font-size: 0.9rem;">1. <strong>Regístrate y valida tu acceso</strong> en la barra lateral.</p>
</td>
</tr>
</table>
</div>
"""
    }
}
L = LOCALES["es"]

if st.session_state.sidebar_visible:
    with st.sidebar:
        st.markdown(f'<div class="sidebar-brand-title">{L["marca"]}</div>', unsafe_allow_html=True)
        try:
            with open("Mongoose.gif", "rb") as file_:
                contents = file_.read()
                data_url = base64.b64encode(contents).decode("utf-8")
            st.markdown(
                f'<img src="data:image/gif;base64,{data_url}" style="width:100%; border-radius:8px; margin-bottom:15px;">',
                unsafe_allow_html=True)
        except Exception:
            pass

        st.markdown("---")
        if not st.session_state.suscrito:
            with st.expander(L["ya_reg"], expanded=st.session_state.expander_login,
                             key=f"exp_log_{st.session_state.login_id}"):
                email_in = st.text_input(L["mail_reg"], key="login_email")
                if st.button(L["btn_val"]):
                    correo_limpio = email_in.lower().strip()
                    if not es_correo_valido(correo_limpio):
                        st.error(L["err_mail"])
                    else:
                        resultado = app.verificar_usuario_db(correo_limpio)
                        if resultado:
                            plan, activo, nombre, cont, f_reg = resultado
                            if activo == 1:
                                nuevo_contador = (cont or 0) + 1
                                app.ejecutar_sql("UPDATE usuarios SET contador_ingresos = ? WHERE email = ?",
                                                 (nuevo_contador, correo_limpio))
                                st.session_state.update({
                                    "suscrito": True, "email": correo_limpio, "plan": plan, "nombre": nombre,
                                    "contador_ingresos": nuevo_contador,
                                    "fecha_registro": f_reg if f_reg else time.strftime("%Y-%m-%d")
                                })
                                st.rerun()
                            else:
                                st.warning(L["act_pend"])
                        else:
                            st.error(L["no_encontrado"])

            with st.expander(L["nuevo_reg"], expanded=st.session_state.get("expander_registro", False),
                             key=f"exp_reg_{st.session_state.registro_id}"):
                n = st.text_input(L["nom_com"], key="reg_nombre")
                e = st.text_input(L["corr_elec"], key="reg_email")
                p = st.selectbox(L["plan_des"], ["Plan Oro", "Plan Plata", "Plan Bronce"])
                if st.button(L["btn_reg"]):
                    correo_limpio = e.lower().strip()
                    if not es_correo_valido(correo_limpio):
                        st.error(L["err_mail"])
                    else:
                        try:
                            fecha_hoy = time.strftime("%Y-%m-%d")
                            app.ejecutar_sql("""INSERT INTO usuarios (nombre, email, plan_suscripcion, fecha_pago, activo, contador_ingresos, fecha_registro) 
                                VALUES (?, ?, ?, ?, 1, 0, ?)""", (n, correo_limpio, p, fecha_hoy, fecha_hoy))
                            st.success(L["exito_reg"])
                            time.sleep(1)
                            st.rerun()
                        except Exception as ex:
                            st.error(f"Error: {ex}")
                st.markdown("---")
                st.link_button("💳 Pagar con ePayco", "https://payco.link", use_container_width=True)
        else:
            st.markdown(
                f'<div class="sidebar-card">{L["lbl_plan"]} <span class="badge-active">{st.session_state.plan}</span></div>',
                unsafe_allow_html=True)
            st.markdown("---")
            opciones_mock = ["Directorio Histórico Principal", "Revistas Old School (1982-1985)"]
            seleccion = st.selectbox(L["sel_dir"], options=opciones_mock)
            st.session_state.nombre_directorio = seleccion
            st.markdown("---")
            if st.button(L["cerrar_sesion"]):
                st.session_state.clear()
                st.rerun()
# --- ÁREA PRINCIPAL ---
col_control, _ = st.columns(2)

with col_control:
    texto_boton_sidebar = ">>" if not st.session_state.sidebar_visible else "<<"
    if st.button(texto_boton_sidebar, use_container_width=False):
        st.session_state.sidebar_visible = not st.session_state.sidebar_visible
        st.rerun()

st.write("---")

if not st.session_state.suscrito:
    st.markdown(
        f'<div style="text-align: center;"><div class="chat-header-title">{L["titulo_no_suscrito"]}</div></div>',
        unsafe_allow_html=True)
    st.markdown(L["bienvenida_html"], unsafe_allow_html=True)
else:
    dir_actual = st.session_state.get("nombre_directorio", "")
    st.markdown(
        f'<div style="text-align: center;"><div class="chat-header-title">{L["titulo_suscrito"]} {dir_actual}</div></div>',
        unsafe_allow_html=True)

    st.write(f"{L['lbl_bienvenido']} **{st.session_state.nombre}** — `{st.session_state.email}`")

    if "nombre_directorio" in st.session_state:
        if "messages" not in st.session_state:
            st.session_state.messages = []
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if prompt := st.chat_input(L["chat_input"]):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            try:
                app.configurar_api()
                with st.chat_message("assistant"):
                    with st.spinner(L["spinner_vector"]):
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        response = model.generate_content(prompt)
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"{L['err_consulta']} {e}")

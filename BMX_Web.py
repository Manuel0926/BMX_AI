# --- INTERFAZ PREMIUM CON MENÚS FILTRADOS PARA USUARIOS ---
st.markdown("""
<style>
/* 1. Ocultar la línea decorativa superior y el menú de tres puntos, pero PERMITIR el botón de Share */
[data-testid="stDecoration"] {
    visibility: hidden !important;
    display: none !important;
}

/* Ocultar únicamente el botón del menú de tres puntos en la esquina superior */
button#MainMenu {
    visibility: hidden !important;
    display: none !important;
}

/* Forzar que el área del encabezado se muestre correctamente para el botón de Share */
header, [data-testid="stHeader"], .stAppHeader {
    visibility: visible !important;
    background-color: #7CB4E6 !important;
}

/* 2. Ocultar por completo la barra flotante de 'Manage app' y el pie de página */
div[data-testid="stBottom"] > div:nth-child(2), footer, [data-testid="manage_app_button"], button[data-testid="manage_app_button"] {
    visibility: hidden !important;
    display: none !important;
}

/* Bloquear los badges o iconos extras de visor que inyecta Streamlit Cloud */
.viewerBadge, .stDeployButton {
    display: none !important;
}

/* --- ESTILOS DE COLORES PERSONALIZADOS DE LA INTERFAZ --- */
.stApp, [data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child, [data-testid="stChatInputHoverContainer"], div[data-testid="stBottom"] > div {
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
[data-testid="baseButton-secondary"], [data-testid="baseButton-primary"], div[data-testid="stLinkButton"] a { 
    background-color: #3A75A8 !important; border: 2px solid #000000 !important; border-radius: 24px !important; padding: 8px 24px !important; transition: all 0.25s ease !important; 
}
[data-testid="baseButton-secondary"] p, [data-testid="baseButton-primary"] p, div[data-testid="stLinkButton"] a p { 
    color: #FFFFFF !important; font-weight: 600 !important; font-size: 14px !important; 
}
[data-testid="baseButton-secondary"]:hover, [data-testid="baseButton-primary"]:hover, div[data-testid="stLinkButton"] a:hover { 
    background-color: #0F3352 !important; border-color: #FFFFFF !important; 
}

/* Opciones de diseño para cuando se genere la impresión física del PDF */
@media print {
    html, body, .stApp, div[data-testid="stExpander"], .sidebar-card, button, div[data-testid="stLinkButton"] a { 
        background: #FFFFFF !important; background-color: #FFFFFF !important; box-shadow: none !important; color: #000000 !important; 
    }
    header, [data-testid="stHeader"], .stAppHeader, button[data-testid="stHeaderActionButton"] {
        display: none !important;
    }
    button, div[data-testid="stLinkButton"] a { border: 1px solid #000000 !important; }
    button p, div[data-testid="stLinkButton"] a p { color: #000000 !important; }
}
</style>
""", unsafe_allow_html=True)


    st.write(
        f"{L['lbl_bienvenido']} **{st.session_state.nombre}** — `{st.session_state.email}` | "
        f"🔢 **Ingresos:** `{st.session_state.contador_ingresos}` | "
        f"📅 **Registro:** `{st.session_state.fecha_registro}`"
    )

    if "current_store" in st.session_state:
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
                client = app.obtener_cliente()
                with st.chat_message("assistant"):
                    with st.spinner(L["spinner_vector"]):
                        store_objeto = st.session_state.current_store
                        id_string_store = getattr(store_objeto, 'name', str(store_objeto))
                        response = client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                tools=[
                                    types.Tool(file_search=types.FileSearch(file_search_store_names=[id_string_store]))]
                            )
                        )

                    texto_respuesta = response.text.lower()
                    indicadores_ausencia = ["no encontr", "no hall", "no tengo", "no hay", "no se menciona",
                                            "no contiene"]
                    if any(idx in texto_respuesta for idx in indicadores_ausencia) or response.text.strip() == "":
                        with st.spinner(L["spinner_fallback"]):
                            archivos_planos = []
                            try:
                                for f in client.files.list():
                                    if getattr(f, 'display_name', '').lower().endswith('.pdf'):
                                        archivos_planos.append(f)
                            except Exception:
                                pass
                            payload_alternativo = [prompt] + archivos_planos
                            response = client.models.generate_content(
                                model='gemini-2.5-flash',
                                contents=payload_alternativo
                            )
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"{L['err_consulta']} {e}")

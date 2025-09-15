from sqlite3 import Row
import requests
import json
from urllib3.poolmanager import key_fn_by_scheme
import gradio as gr
import sqlite3
from datetime import datetime
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuración de la base de datos
def init_db():
    """Inicializa la base de datos y crea la tabla si no existe"""
    try:
        conn = sqlite3.connect('chat_history.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS messages
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      role TEXT NOT NULL,
                      content TEXT NOT NULL,
                      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        conn.commit()
        conn.close()
        logger.info("Base de datos inicializada correctamente")
    except sqlite3.Error as e:
        logger.error(f"Error al inicializar la base de datos: {e}")

def save_message(role, content):
    """Guarda un mensaje en la base de datos"""
    try:
        conn = sqlite3.connect('chat_history.db')
        c = conn.cursor()
        c.execute("INSERT INTO messages (role, content) VALUES (?, ?)",
                  (role, content))
        conn.commit()
        conn.close()
        logger.info(f"Mensaje de {role} guardado en la base de datos")
    except sqlite3.Error as e:
        logger.error(f"Error al guardar mensaje: {e}")

def load_conversation_history(limit=20):
    """Carga el historial de conversaciones desde la base de datos"""
    try:
        conn = sqlite3.connect('chat_history.db')
        c = conn.cursor()
        c.execute("SELECT role, content FROM messages ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = c.fetchall()
        conn.close()
        
        # Convertir a formato Gradio (invertir orden para mostrar del más antiguo al más nuevo)
        history = [{"role": row[0], "content": row[1]} for row in reversed(rows)]
        logger.info(f"Historial cargado: {len(history)} mensajes")
        return history
    except sqlite3.Error as e:
        logger.error(f"Error al cargar historial: {e}")
        return []

def limpiar_historial_completo():
    """Elimina todo el historial de conversaciones"""
    try:
        conn = sqlite3.connect('chat_history.db')
        c = conn.cursor()
        c.execute("DELETE FROM messages")
        conn.commit()
        conn.close()
        logger.info("Historial limpiado completamente")
        return [{"role": "assistant", "content": "Historial limpiado correctamente."}]
    except sqlite3.Error as e:
        logger.error(f"Error al limpiar historial: {e}")
        return [{"role": "assistant", "content": f"Error al limpiar el historial: {e}"}]

# Función para enviar el mensaje al modelo y recibir la respuesta
def generar_respuesta(mensaje, historial, temperatura=0.8):
    """Envía mensaje al modelo y devuelve la respuesta"""
    try:
        # Guardar mensaje del usuario en BD
        save_message("user", mensaje)
        
        # Preparar el prompt con contexto de conversación
        contexto = "\n".join([f"{msg['role']}: {msg['content']}" for msg in historial[-6:]])  # Usar solo los últimos 6 mensajes
        prompt = f"{contexto}\nuser: {mensaje}\nassistant:"
        
        # Llamar a Ollama
        response = requests.post(
            url='http://localhost:11434/api/generate',
            headers={'Content-Type': 'application/json'},
            data=json.dumps({
                "model": "gemma2:2b",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperatura,
                    "top_p": 0.9
                }
            }),
            timeout=120
        )

        if response.status_code == 200:
            respuesta = response.json()['response']
            # Guardar respuesta del asistente en BD
            save_message("assistant", respuesta)
            # Agregar respuesta al historial
            historial.append({"role": "assistant", "content": respuesta})
            return historial
        else:
            error_msg = f"Error en la API: {response.status_code} - {response.text}"
            logger.error(error_msg)
            save_message("assistant", error_msg)
            historial.append({"role": "assistant", "content": error_msg})
            return historial
            
    except Exception as e:
        error_msg = f"Error de conexión: {str(e)}"
        logger.error(error_msg)
        save_message("assistant", error_msg)
        historial.append({"role": "assistant", "content": error_msg})
        return historial

def contenido_historial_real(limit=10):
    """Cargar historial real desde la base de datos"""
    history = load_conversation_history(limit)
    
    if not history:
        return [{"role": "assistant", "content": "Aún no hay historial de conversaciones."}]
    
    return history

def limpiar_chat():
    """Limpia la interfaz de chat actual (no la base de datos)"""
    return []

# Inicializar la base de datos
init_db()

# Personalizar el tema CSS
css = """
.centered {
    display: flex;
    justify-content: center;
    align-items: center;
}
.gradio-container {
    max-width: 800px;
    margin: 0 auto;
}
footer {
    display: none !important;
}
"""

# Crear la interfaz mejorada
with gr.Blocks(theme=gr.themes.Soft(), css=css, title="🤖 Asistente AI Local") as demo:
    # Título y descripción
    gr.Markdown("# 🤖 Asistente IA Local")
    gr.Markdown("Interfaz para interactuar con Gemma2:2B mediante Ollama")
    
    # Estado para almacenar parámetros
    temperatura_state = gr.State(value=0.8)
    
    # Usar Tabs correctamente con gr.Tab
    with gr.Tabs() as tabs:
        with gr.Tab("Chat con Gemma2:2B"):
            chatbot = gr.Chatbot(
                label="Conversación",
                height=400,
                type="messages"  # Formato de mensajes
            )
            with gr.Row():
                mensaje = gr.Textbox(
                    label="Tu mensaje",
                    placeholder="Escribe tu prompt aquí...",
                    lines=2,
                    scale=4
                )
                with gr.Column(scale=1):
                    enviar = gr.Button("Enviar", variant="primary", scale=1)
                    limpiar = gr.Button("Limpiar chat")
            
            with gr.Row():
                # Añadir controles para parámetros del modelo
                temperatura = gr.Slider(0.1, 1.0, value=0.8, label="Temperatura 🥵", interactive=True)
            
            # Ejemplos de prompts
            gr.Examples(
                examples=[
                    ["Hola, ¿cómo estás?"],
                    ["¿Puedes explicarme la teoría de la relatividad?"],
                    ["¿Cuál es la capital de Francia?"],
                    ["Escribe un poema corto sobre el mar"],
                    ["¿Cuál es la fórmula química del agua?"],
                    ["¿Me enseñas python?"],
                    ["¿Qué sabes de pesca?"]
                ],
                inputs=mensaje
            )
            
        with gr.Tab("Historial de conversación"):
            # Botón para actualizar el historial
            actualizar_btn = gr.Button("Actualizar historial", variant="secondary")
    
            # Componente para mostrar el historial real
            historial_real = gr.Chatbot(
                label="Historial de Conversaciones Reales",
                height=400,
                type="messages",
                value=contenido_historial_real()  # Cargar historial real al iniciar
            )
    
            # Función para actualizar el historial
            def actualizar_historial():
                return contenido_historial_real()
    
            # Conectar el botón de actualización
            actualizar_btn.click(
                fn=actualizar_historial,
                inputs=None,
                outputs=historial_real
            )
            
            # Botón para limpiar historial completo
            limpiar_historial_btn = gr.Button("Limpiar historial completo", variant="stop")
            limpiar_historial_btn.click(
                fn=limpiar_historial_completo,
                inputs=None,
                outputs=historial_real
            )
            
        with gr.Tab("Acerca de"):
            # Usar Markdown para mostrar información estática
            gr.Markdown("""
            ### 🤖 Acerca de este Asistente

            Este es un asistente de IA local construido con:
            - **Gradio**: Para la interfaz web
            - **Ollama**: Para ejecutar modelos localmente
            - **Gemma2:2B**: Modelo de lenguaje de Google

            ### 🚀 Instalación y Uso

            1. Instala Ollama desde [ollama.com](https://ollama.com/)
            2. Descarga el modelo: `ollama pull gemma2:2b`
            3. Ejecuta este script: `python asistente_ia.py`

            ### 📦 Dependencias

            Instala las dependencias con:
            ```bash
            pip install -r requirements.txt
            ```

            ### 📝 Licencia

            Este proyecto está bajo la Licencia MIT.

            ### 👨‍💻 Autor

            Pedro Mencías - 2025

            ### 📧 Contacto

            [beyond.digital.web@gmail.com](mailto:beyond.digital.web@gmail.com)

            Hecho en Asturias con 💓 y {miles de errores}
            """)
    
    # Conectar eventos solo para el chat
    def respond_and_clear(mensaje, historial, temperatura_val):
        historial_actualizado = generar_respuesta(mensaje, historial, temperatura_val)
        return historial_actualizado, ""
    
    mensaje.submit(
        fn=respond_and_clear,
        inputs=[mensaje, chatbot, temperatura],
        outputs=[chatbot, mensaje]
    )
    
    enviar.click(
        fn=respond_and_clear,
        inputs=[mensaje, chatbot, temperatura],
        outputs=[chatbot, mensaje]
    )
    
    limpiar.click(
        fn=limpiar_chat,
        inputs=None,
        outputs=chatbot
    )
    
    # Actualizar el estado de temperatura cuando cambia el slider
    temperatura.change(
        fn=lambda x: x,
        inputs=temperatura,
        outputs=temperatura_state
    )

# Ejecutar la aplicación
if __name__ == "__main__":
    demo.launch(
        share=False,
        server_name="0.0.0.0",
        server_port=7860,
        show_error=True
    )
# asistente-ia-local
Interfaz web para interactuar con modelos de lenguaje a través de Ollama, construida con Gradio.

Estructura del proyecto

asistente-ia-local/
├── asistente_ia.py      # Código principal de la aplicación
├── requirements.txt     # Dependencias de Python
├── README.md           # Este archivo
└── chat_history.db     # Base de datos (se crea automáticamente)

## Características

- Interfaz web amigable con Gradio
- Historial de conversaciones persistente en SQLite
- Soporte para diferentes modelos de Ollama
- Ajuste de parámetros como temperatura
- Visualización del historial de conversaciones

## Instalación

1. Clona el repositorio:
```bash
git clone https://github.com/charran78/asistente-ia-local.git
cd asistente-ia-local

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


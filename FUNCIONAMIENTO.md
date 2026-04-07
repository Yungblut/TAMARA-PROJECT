# TAMARA - Flujo de Funcionamiento

## Inicio del Sistema

```
server.py (FastAPI + lifespan)
    |
    +---> src/logging.py     (Configura structlog)
    |
    +---> src/config.py      (Pydantic Settings: config.yaml + .env)
    |
    +---> src/tts_engine.py  (Kokoro TTS en hilo de fondo)
    |
    +---> database/client.py (Conecta a MariaDB si esta habilitado)
    |
    +---> tools/registry.py  (Registra herramientas de Tool Calling)
```

---

## Flujo de Comunicacion en Tiempo Real

```
USUARIO (Browser)
    |
    |  WebSocket /ws
    v
websocket_handler.py (Recibe mensajes del cliente)
    |
    |  Mensaje de texto
    v
llm_engine.py (Procesa con Ollama + Tool Calling)
    |
    +---> registry.py (Obtiene herramientas disponibles)
    |       |
    |       +---> tools.py (Ejecuta query_database, list_tables, etc.)
    |               |
    |               +---> client.py (Consultas seguras en MariaDB)
    |
    |  Respuesta de texto (streaming token a token)
    v
tts_engine.py (Convierte texto a audio con Kokoro + Misaki)
    |
    |  Audio Base64 WAV
    v
websocket_handler.py (Envia audio + tokens al cliente via WebSocket)
    |
    v
USUARIO (Escucha respuesta + lee texto en tiempo real)
```

---

## Descripcion de Archivos

| Archivo | Funcion |
|---------|---------|
| `server.py` | FastAPI con lifespan async, monta rutas HTTP y WebSocket |
| `src/config.py` | Pydantic Settings: carga config.yaml + env vars con validacion |
| `src/logging.py` | Configuracion de structlog (consola dev / JSON prod) |
| `src/websocket_handler.py` | Maneja conexiones WebSocket, orquesta LLM y TTS |
| `src/llm_engine.py` | Cliente Ollama con streaming y Tool Calling |
| `src/tts_engine.py` | Motor TTS: Kokoro-82M ONNX + Misaki G2P |
| `src/tools/base.py` | Clases base abstractas para definir herramientas |
| `src/tools/registry.py` | Registro central de herramientas con structlog |
| `src/tools/database/client.py` | Cliente seguro MariaDB (solo SELECT por defecto) |
| `src/tools/database/tools.py` | 4 herramientas de BD para Ollama Function Calling |

---

## Herramientas Disponibles (Tool Calling)

| Herramienta | Descripcion |
|-------------|-------------|
| `list_database_tables` | Lista las tablas de la base de datos |
| `describe_table` | Describe la estructura (columnas, tipos) de una tabla |
| `query_database` | Ejecuta consultas SELECT seguras con validacion |
| `get_table_count` | Obtiene el numero de filas de una tabla |

---

## Stack Tecnologico

| Capa | Tecnologia | Proposito |
|------|-----------|-----------|
| Web Framework | FastAPI | Servidor async con WebSocket |
| LLM | Ollama + Qwen2.5-32B | Inferencia local en GPU |
| TTS | Kokoro-82M + Misaki | Voz neural en espanol |
| Base de datos | MariaDB | Consultas via Tool Calling |
| Config | Pydantic Settings | Validacion de tipos + env vars |
| Logging | structlog | Logs estructurados JSON |
| Paquetes | UV + pyproject.toml | Gestion moderna de dependencias |
| Linting | Ruff | Linter + formatter unificado |

---

## Resumen del Flujo

1. **Usuario envia texto** via WebSocket
2. **LLM analiza** el mensaje y decide si usar herramientas
3. **Si necesita datos** ejecuta herramientas de BD automaticamente
4. **LLM genera respuesta** con streaming token a token
5. **TTS convierte a audio** en limites de oracion (Kokoro + Misaki)
6. **Usuario recibe** texto + audio en tiempo real

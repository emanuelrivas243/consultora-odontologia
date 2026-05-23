# 🦷 Consultora Odontología — Backend

Este directorio contiene el backend de la aplicación, desarrollado con **FastAPI**, **SQLModel** (PostgreSQL) y **Supabase** para la autenticación y manejo de roles.

---

## 🚀 Instrucciones para Levantar el Servidor

Sigue estos pasos detallados para configurar y ejecutar el entorno de desarrollo local.

---

### 📍 1. Ubicación en la Terminal

Para ejecutar los comandos del backend, **debes estar parado en la raíz del proyecto** (donde se encuentra la carpeta `backend/` y el archivo `.env.example`).

> 💡 Si estás dentro de la carpeta `backend/`, sal un nivel ejecutando `cd ..`

---

### ⚙️ 2. Configuración del Entorno de Desarrollo

**Paso 1 — Crear el entorno virtual** (si no lo tienes aún):

```bash
python -m venv .venv
```

**Paso 2 — Activar el entorno virtual:**

| Sistema operativo | Comando |
|---|---|
| Windows (Git Bash) | `source .venv/Scripts/activate` |
| Windows (PowerShell) | `.\.venv\Scripts\Activate.ps1` |
| Mac / Linux | `source .venv/bin/activate` |

**Paso 3 — Instalar las dependencias:**

```bash
pip install -r backend/requirements.txt
```

**Paso 4 — Variables de entorno:**

Crea un archivo `.env` en la raíz del proyecto basándote en `.env.example`:

```bash
cp .env.example .env
```

> ⚠️ Abre el archivo `.env` y rellena las variables con las credenciales reales de tu base de datos y Supabase.

---

### 🏃 3. Ejecutar la Aplicación

Con el entorno virtual activo y desde la **raíz del proyecto**, ejecuta:

```bash
uvicorn backend.app.main:app --reload
```

---

## 📑 Documentación de la API

Una vez que el servidor esté corriendo, accede a la documentación interactiva en:

| Interfaz | URL |
|---|---|
| Swagger UI | http://127.0.0.1:8000/docs |
| Redoc | http://127.0.0.1:8000/redoc |


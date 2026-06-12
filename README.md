### CON DOCKER
docker compose up --build
Frontend → http://localhost (puerto 80)
Backend → http://localhost:8000 (también accesible directamente)
Puntos importantes:

El private.key no se copia a la imagen — se monta como volumen de solo lectura (:ro). Así el secreto nunca queda embebido en la imagen.
El .env se inyecta con env_file en runtime, tampoco entra al build.
nginx hace proxy de /contracts, /templates, /webhooks, /health al servicio backend usando la red interna de Docker — el frontend no necesita saber el IP del backend.
El .dockerignore excluye .venv, .env, private.key y node_modules para que los builds sean rápidos y seguros.



### ANTES DE DOCKER

Backend — nuevo endpoint GET /contracts que lista los envelopes de los últimos 30 días desde DocuSign.

Frontend (frontend/) — React + Vite + Tailwind con 3 páginas:

Página	Ruta	Descripción
Dashboard	/	Tabla de contratos con estado, fechas y link a detalle
Enviar Contrato	/send	Formulario completo: cliente, tipo, template ID, campos custom
Detalle	/contracts/:id	Estado del envelope + botón de descarga cuando está completed
Para correr ambos servicios:


# Terminal 1 — Backend
uvicorn main:app --reload

# Terminal 2 — Frontend
cd frontend && npm run dev
Abre http://localhost:5173. El proxy de Vite redirige /contracts al backend en :8000 automáticamente, sin necesidad de configurar CORS extra.
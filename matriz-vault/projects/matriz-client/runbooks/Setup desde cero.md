---
last_verified: 2026-04-16
tags: [runbook, matriz-client]
---

# Runbook: Setup del proyecto desde cero

## Pre-requisitos

- [ ] Python 3.12+ instalado
- [ ] `uv` instalado (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- [ ] Credenciales de la Primary API (usuario y password)

## Pasos

### 1. Clonar el repo
```bash
git clone [repo-url]
cd matriz-client
```

### 2. Instalar dependencias
```bash
uv sync
```

### 3. Configurar variables de entorno
```bash
cp .env.example .env
# Editar .env con tus credenciales:
# PRIMARY_USER=tu_usuario
# PRIMARY_PASSWORD=tu_password
# PRIMARY_BASE_URL=https://api.remarkets.primary.com.ar
```

### 4. Verificar que funciona
```bash
uv run python main.py
```

Deberías ver la lista de instrumentos o datos de mercado (depende de lo que haga `main.py` actualmente).

## Verificación

- El script corre sin errores de autenticación
- Se ven datos de la API en stdout

## Problemas comunes

- **`AuthenticationError`**: verificar usuario/password en `.env`. Las credenciales son distintas para demo vs producción.
- **Timeout**: la API de remarkets puede ser lenta en horarios de alta demanda. Probar fuera de horario de mercado.

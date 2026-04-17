---
last_verified: 2026-04-17
tags: [runbook, release]
---

# Runbook: Cortar un release de matriz-client

## Cuándo usar

Cuando hay cambios mergeados a `main` listos para publicar como GitHub Release. La distribución va por GitHub Releases (no PyPI). El workflow `.github/workflows/release.yml` (BEC-12) construye y publica wheel + sdist al pushear un tag `v*`.

## Pre-requisitos

- [ ] Permisos de push y de tag en `sebadlf/matriz-client`.
- [ ] CI verde en `main` para el commit a taggear.
- [ ] Cambios de breaking que requieran sección "Migrating from X.Y" en el README ya documentados.

## Pasos

### 1. Bumpear versión en `pyproject.toml`

```bash
# editar manualmente:
# project.version = "0.X.Y" → "0.X+1.0" (minor) o "0.X.Y+1" (patch)
uv sync   # regenera uv.lock con la nueva versión del paquete editable
```

Convención: bumps de breaking change → minor (estamos en `0.x`); bumps de feature aditiva o fix → patch.

### 2. Validar el build localmente

```bash
uv build
uv run --with twine twine check dist/*
```

Ambos checks (`wheel` + `sdist`) deben dar `PASSED`.

### 3. Verificar suite completa

```bash
uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run pytest -q
```

### 4. PR a main

Branch `sebadlf-bec-{n}-chore-bump-...`, commit `chore: bump matriz_client to X.Y.Z (BEC-NN)`, PR con checklist. Esperar CI verde y mergear con squash.

### 5. Tag y push

Una vez mergeado, en `main` actualizado:

```bash
git checkout main && git pull origin main
git tag vX.Y.Z
git push origin vX.Y.Z
```

El workflow `release.yml` se dispara con el push del tag. **Validación interna del workflow**: confirma que el tag matchea `project.version` del commit; si no, falla y no sube nada.

### 6. Smoke install

En venv limpio, instalar desde el wheel publicado:

```bash
python3.12 -m venv /tmp/matriz-smoke
/tmp/matriz-smoke/bin/pip install \
  https://github.com/sebadlf/matriz-client/releases/download/vX.Y.Z/matriz_client-X.Y.Z-py3-none-any.whl
/tmp/matriz-smoke/bin/python -c "import matriz_client; print(matriz_client.MarketDataSnapshot.empty())"
```

## Verificación

- [ ] GitHub Release `vX.Y.Z` listado con dos artefactos (`.whl` + `.tar.gz`).
- [ ] Smoke install funciona en venv limpio.
- [ ] Linear ticket cerrado.

## Rollback

Los GitHub Releases se pueden borrar (UI o `gh release delete vX.Y.Z`). El tag se borra con `git push origin :refs/tags/vX.Y.Z` y `git tag -d vX.Y.Z` localmente. Como el wheel ya pudo haberse instalado por terceros, lo recomendable es publicar `vX.Y.Z+1` con el fix en lugar de revertir.

## Historial

| Fecha | Quién | Notas |
|-------|-------|-------|
| 2026-04-17 | Sebastián | v0.2.0 — cierre del ciclo safe-access (BEC-26..30). |

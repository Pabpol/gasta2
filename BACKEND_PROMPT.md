# Backend Unificado de Gastos — Prompt para Copilot

Este documento sirve como **prompt maestro** para usar con GitHub Copilot en VS Code.  
Contiene todas las especificaciones necesarias para que Copilot genere un backend completo en Python/FastAPI para la gestión de gastos con integración vía MacroDroid, categorización, Telegram, Excel y conciliación de ingresos/reembolsos.

---

## 🎯 Objetivo
Generar un backend en Python 3.10+ con **FastAPI** que procese gastos capturados por MacroDroid (notificaciones bancarias), enriquezca con interacción **inmediata por Telegram** (categoría + compartido), registre **ingresos/reembolsos** y actualice un Excel con resúmenes.

**Tecnologías:** FastAPI, Pydantic v2, pandas, pyarrow, openpyxl, httpx, scikit-learn (opcional ML).

---

## 📂 Estructura esperada
```
backend_gastos/
├─ app.py
├─ requirements.txt
├─ core/
│  ├─ __init__.py
│  ├─ paths.py
│  ├─ storage.py
│  ├─ categorize.py
│  └─ reconcile.py
├─ integrations/
│  ├─ __init__.py
│  └─ messenger.py
├─ data/               # se crea en runtime
├─ models/             # opcional para ML
├─ merchant_map.csv    # opcional
├─ config.yaml         # opcional
└─ Presupuesto_Auto.xlsx  # colocar aquí manualmente
```

---

## 📦 1) requirements.txt
```
fastapi==0.111.0
uvicorn==0.30.1
pydantic==2.8.2
pandas==2.2.2
pyarrow==16.1.0
openpyxl==3.1.2
httpx==0.27.0
scikit-learn==1.5.1
joblib==1.4.2
python-multipart==0.0.9
```

---

## ⚙️ 2) core/paths.py
Define rutas y archivos principales:
- `DATA_DIR`
- `PARQUET` = `data/movimientos_normalizados.parquet`
- `EXCEL` = `Presupuesto_Auto.xlsx`
- `MERCHANT_MAP`
- `CONFIG_YAML`
- `MODEL_PATH`

---

## 📊 3) core/storage.py
Esquema de columnas (DataFrame parquet):
```
["id","fecha","descripcion","monto_clp","moneda","medio",
 "compartido_con","porcentaje_compartido","mcc","categoria",
 "subcategoria","etiquetas","estado","fuente","ml_confidence",
 "tipo","parent_id","monto_tu_parte","monto_tercero","settlement_status"]
```

Funciones clave:
- `upsert_row(row: dict) -> dict`
- `save_row(row: dict)`
- `get(id: str) -> dict|None`
- `list_pendientes() -> list[dict]`
- `list_receivables() -> list[dict]`
- `sync_excel()` → actualiza Excel con:
  - **MOVIMIENTOS**
  - **RESUMEN_AUTO** (gastos netos por categoría usando `monto_tu_parte`)
  - **RESUMEN_CASHFLOW** (ingresos/gastos/neto por mes)

---

## 🧾 4) core/categorize.py
Incluye:
- `normalize_text(s)`
- Clase `Categorizer(threshold=0.8)` con:
  - Carga de `merchant_map.csv` y `config.yaml`
  - Soporte opcional de modelo ML (`models/clf.joblib`)
  - `add_merchant_alias(...)`
  - `categorize_one(gasto: dict)` → retorna `(categoria, subcategoria, estado, confianza)`

Orden: merchant_map → reglas → ML → pendiente.

---

## 🔗 5) core/reconcile.py
Heurísticas de match para reembolsos ↔ gastos compartidos por cobrar:
- `within_tolerance(in_amt, exp_amt)` → $1.000 CLP o ±5% si >100k
- `try_auto_match(income_row, pendientes, prefer_name=None, days_window=10)`

---

## 💬 6) integrations/messenger.py (Telegram)
- Configura con `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID`.
- Funciones:
  - `send_category_prompt(gasto, alias_hint="")`
  - `send_share_prompt(gasto)`
  - `handle_telegram_update(update, storage, categorizer)` → procesa botones/callbacks y texto libre:
    - Categoría (`cat:<gid>:<categoria>`)
    - Compartido (`share:*` o `id <gid> con <Nombre> % <n>`)
- Usa `httpx` async para llamadas a `sendMessage` y `editMessageText`.

---

## 🚀 7) app.py (FastAPI)
Modelos Pydantic:
- `GastoIn`
- `IngresoIn`
- `MatchIn`

Endpoints:
- `POST /api/gasto`
- `GET /api/pendientes`
- `POST /api/ingreso`
- `POST /api/reembolso/match`
- `GET /api/receivables`
- `POST /telegram/webhook`

---

## ✅ 8) Criterios de aceptación
- Gasto TC sin categoría → Telegram envía botones.
- Selección de categoría → actualiza Excel, luego pregunta si fue compartido.
- Compartido 50% → calcula `monto_tu_parte/monto_tercero`, setea `receivable_pending`.
- Ingreso (transfer_in con `contraparte`) → auto-match con gasto compartido pendiente.
- Transferencia fija (ej. arriendo) → entra como `transfer_out` y se categoriza por reglas.

---

## 🧪 9) Ejecución
```bash
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN="..."
export TELEGRAM_CHAT_ID="..."
uvicorn app:app --reload --port 8000
```

Configura webhook de Telegram:
```
https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook?url=https://TU_HOST/telegram/webhook
```

---

## 📝 Notas finales
- Coloca `Presupuesto_Auto.xlsx` en la raíz del proyecto.
- `merchant_map.csv` y `config.yaml` mejoran la clasificación.
- El modelo ML es opcional.
- Manejar errores: si no hay Excel aún, `sync_excel()` no debe fallar.

---

## 👩‍💻 Uso con Copilot
Pega este prompt en VS Code y pídele a Copilot:
- “Genera el contenido completo de `core/paths.py`”
- “Genera `core/storage.py` con todas las funciones de sync_excel”
- “Crea `integrations/messenger.py` con los botones y el handler de Telegram”
- “Rellena `app.py` con los endpoints y modelos Pydantic”


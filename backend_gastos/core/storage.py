"""
Data storage management using parquet files and Excel synchronization.
Handles all CRUD operations and maintains data consistency.
"""
import pandas as pd
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

from .paths import PARQUET, EXCEL, DATA_DIR

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# DataFrame schema definition
SCHEMA_COLUMNS = [
    "id", "fecha", "descripcion", "monto_clp", "moneda", "medio",
    "compartido_con", "porcentaje_compartido", "mcc", "categoria",
    "subcategoria", "etiquetas", "estado", "fuente", "ml_confidence",
    "tipo", "parent_id", "monto_tu_parte", "monto_tercero", "settlement_status"
]

def _ensure_schema(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure DataFrame has all required columns with proper types"""
    for col in SCHEMA_COLUMNS:
        if col not in df.columns:
            if col in ["monto_clp", "porcentaje_compartido", "ml_confidence", "monto_tu_parte", "monto_tercero"]:
                df[col] = 0.0
            elif col in ["fecha"]:
                df[col] = pd.NaT
            else:
                df[col] = ""
    
    # Ensure proper order
    df = df[SCHEMA_COLUMNS]
    
    # Convert types
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df["monto_clp"] = pd.to_numeric(df["monto_clp"], errors="coerce").fillna(0.0)
    df["porcentaje_compartido"] = pd.to_numeric(df["porcentaje_compartido"], errors="coerce").fillna(0.0)
    df["ml_confidence"] = pd.to_numeric(df["ml_confidence"], errors="coerce").fillna(0.0)
    df["monto_tu_parte"] = pd.to_numeric(df["monto_tu_parte"], errors="coerce").fillna(0.0)
    df["monto_tercero"] = pd.to_numeric(df["monto_tercero"], errors="coerce").fillna(0.0)
    
    return df

def _load_data() -> pd.DataFrame:
    """Load data from parquet file or create empty DataFrame"""
    try:
        if PARQUET.exists():
            df = pd.read_parquet(PARQUET)
            return _ensure_schema(df)
        else:
            logger.info("Parquet file doesn't exist, creating empty DataFrame")
            return _ensure_schema(pd.DataFrame())
    except Exception as e:
        logger.error(f"Error loading parquet: {e}")
        return _ensure_schema(pd.DataFrame())

def _save_data(df: pd.DataFrame):
    """Save DataFrame to parquet file"""
    try:
        DATA_DIR.mkdir(exist_ok=True)
        df = _ensure_schema(df)
        df.to_parquet(PARQUET, index=False)
        logger.info(f"Data saved to {PARQUET}")
    except Exception as e:
        logger.error(f"Error saving parquet: {e}")
        raise

def upsert_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Insert or update a row in the dataset"""
    df = _load_data()
    
    # Generate ID if not provided
    if not row.get("id"):
        row["id"] = str(uuid.uuid4())
    
    # Set default fecha if not provided
    if not row.get("fecha"):
        row["fecha"] = datetime.now()
    
    # Calculate monto_tu_parte and monto_tercero
    monto_clp = float(row.get("monto_clp", 0))
    porcentaje = float(row.get("porcentaje_compartido", 0))
    
    if porcentaje > 0:
        row["monto_tu_parte"] = monto_clp * (porcentaje / 100)
        row["monto_tercero"] = monto_clp * ((100 - porcentaje) / 100)
    else:
        row["monto_tu_parte"] = monto_clp
        row["monto_tercero"] = 0.0
    
    # Check if row exists
    existing_idx = df[df["id"] == row["id"]].index
    
    if len(existing_idx) > 0:
        # Update existing row
        for key, value in row.items():
            if key in SCHEMA_COLUMNS:
                df.loc[existing_idx[0], key] = value
        logger.info(f"Updated row with id: {row['id']}")
    else:
        # Insert new row
        new_row = pd.DataFrame([row])
        new_row = _ensure_schema(new_row)
        df = pd.concat([df, new_row], ignore_index=True)
        logger.info(f"Inserted new row with id: {row['id']}")
    
    _save_data(df)
    return row

def save_row(row: Dict[str, Any]):
    """Save a single row (alias for upsert_row)"""
    return upsert_row(row)

def get(id: str) -> Optional[Dict[str, Any]]:
    """Get a row by ID"""
    df = _load_data()
    matching_rows = df[df["id"] == id]
    
    if len(matching_rows) > 0:
        return matching_rows.iloc[0].to_dict()
    return None

def list_pendientes() -> List[Dict[str, Any]]:
    """List all pending (uncategorized) expenses"""
    df = _load_data()
    pendientes = df[df["estado"] == "pendiente"]
    return pendientes.to_dict("records")

def list_receivables() -> List[Dict[str, Any]]:
    """List all shared expenses pending settlement"""
    df = _load_data()
    receivables = df[
        (df["porcentaje_compartido"] > 0) & 
        (df["settlement_status"].isin(["", "pending"]) | df["settlement_status"].isna())
    ]
    return receivables.to_dict("records")

def sync_excel():
    """Synchronize data with Excel file"""
    try:
        df = _load_data()
        
        if df.empty:
            logger.warning("No data to sync to Excel")
            return
        
        if not EXCEL.exists():
            logger.warning(f"Excel file {EXCEL} doesn't exist, skipping sync")
            return
        
        # Load existing Excel
        with pd.ExcelWriter(EXCEL, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            
            # Sheet 1: MOVIMIENTOS - All movements
            movements_df = df.copy()
            movements_df["fecha"] = movements_df["fecha"].dt.strftime("%Y-%m-%d")
            movements_df.to_excel(writer, sheet_name="MOVIMIENTOS", index=False)
            
            # Sheet 2: RESUMEN_AUTO - Net expenses by category using monto_tu_parte
            expenses_df = df[df["tipo"] != "transfer_in"].copy()
            if not expenses_df.empty:
                resumen_auto = expenses_df.groupby("categoria").agg({
                    "monto_tu_parte": "sum",
                    "id": "count"
                }).reset_index()
                resumen_auto.columns = ["Categoria", "Monto_Neto", "Cantidad"]
                resumen_auto = resumen_auto.sort_values("Monto_Neto", ascending=False)
                resumen_auto.to_excel(writer, sheet_name="RESUMEN_AUTO", index=False)
            
            # Sheet 3: RESUMEN_CASHFLOW - Income/expenses/net by month
            df_copy = df.copy()
            df_copy["mes"] = df_copy["fecha"].dt.to_period("M")
            
            cashflow_data = []
            for mes in df_copy["mes"].dropna().unique():
                mes_data = df_copy[df_copy["mes"] == mes]
                
                ingresos = mes_data[mes_data["tipo"] == "transfer_in"]["monto_clp"].sum()
                gastos = mes_data[mes_data["tipo"] != "transfer_in"]["monto_tu_parte"].sum()
                neto = ingresos - gastos
                
                cashflow_data.append({
                    "Mes": str(mes),
                    "Ingresos": ingresos,
                    "Gastos": gastos,
                    "Neto": neto
                })
            
            if cashflow_data:
                cashflow_df = pd.DataFrame(cashflow_data)
                cashflow_df.to_excel(writer, sheet_name="RESUMEN_CASHFLOW", index=False)
        
        logger.info("Excel sync completed successfully")
        
    except Exception as e:
        logger.error(f"Error syncing Excel: {e}")
        # Don't raise the exception to avoid breaking the flow

def get_all_data() -> pd.DataFrame:
    """Get all data as DataFrame"""
    return _load_data()

def update_settlement_status(expense_id: str, status: str):
    """Update settlement status for an expense"""
    row = get(expense_id)
    if row:
        row["settlement_status"] = status
        upsert_row(row)
        logger.info(f"Updated settlement status for {expense_id} to {status}")

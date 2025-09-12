"""
FastAPI backend for unified expense management system.
Handles expense processing, categorization, Telegram integration, and reconciliation.
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import asyncio

from core import storage
from core.categorize import Categorizer
from core import reconcile
from integrations.messenger import handle_telegram_update, messenger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Expense Management Backend",
    description="Unified backend for expense processing with Telegram integration",
    version="1.0.0"
)

# Initialize categorizer
categorizer = Categorizer()

# Pydantic models
class GastoIn(BaseModel):
    descripcion: str = Field(..., description="Expense description")
    monto_clp: float = Field(..., description="Amount in CLP")
    fecha: Optional[str] = Field(None, description="Date in ISO format")
    moneda: str = Field("CLP", description="Currency")
    medio: str = Field("TC", description="Payment method (TC, TD, Cash, etc.)")
    mcc: Optional[str] = Field(None, description="Merchant Category Code")
    fuente: str = Field("macrodroid", description="Data source")
    tipo: str = Field("expense", description="Transaction type")

class IngresoIn(BaseModel):
    descripcion: str = Field(..., description="Income description")
    monto_clp: float = Field(..., description="Amount in CLP")
    fecha: Optional[str] = Field(None, description="Date in ISO format")
    contraparte: Optional[str] = Field(None, description="Counterpart name for matching")
    tipo: str = Field("transfer_in", description="Transaction type")
    fuente: str = Field("manual", description="Data source")

class MatchIn(BaseModel):
    income_id: str = Field(..., description="Income transaction ID")
    expense_id: str = Field(..., description="Expense transaction ID")

class CategoryUpdate(BaseModel):
    gasto_id: str = Field(..., description="Expense ID")
    categoria: str = Field(..., description="Category")
    subcategoria: Optional[str] = Field("", description="Subcategory")

class ShareUpdate(BaseModel):
    gasto_id: str = Field(..., description="Expense ID")
    compartido_con: str = Field(..., description="Person shared with")
    porcentaje_compartido: float = Field(..., description="Percentage shared with other person")

# API Endpoints

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Expense Management Backend",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/gasto")
async def create_gasto(gasto: GastoIn, background_tasks: BackgroundTasks):
    """
    Process a new expense from MacroDroid or manual entry.
    Automatically attempts categorization and sends Telegram prompt if needed.
    """
    try:
        # Convert to dict and add metadata
        gasto_dict = gasto.dict()
        gasto_dict["fecha"] = gasto_dict.get("fecha") or datetime.now().isoformat()
        
        # Attempt automatic categorization
        categoria, subcategoria, estado, confidence = categorizer.categorize_one(gasto_dict)
        
        gasto_dict.update({
            "categoria": categoria,
            "subcategoria": subcategoria,
            "estado": estado,
            "ml_confidence": confidence,
            "porcentaje_compartido": 0,
            "compartido_con": "",
            "settlement_status": ""
        })
        
        # Save expense
        saved_gasto = storage.upsert_row(gasto_dict)
        
        # Determine flow based on categorization state and confidence
        if estado == "pendiente":
            # No categorization found - send manual prompt
            background_tasks.add_task(
                send_telegram_categorization_prompt,
                saved_gasto,
                categoria if categoria else ""
            )
        elif estado == "categorizado" and confidence < 0.8:
            # Low confidence auto-categorization - ask for confirmation
            background_tasks.add_task(
                send_telegram_confirmation_prompt,
                saved_gasto,
                confidence
            )
        else:
            # High confidence auto-categorization - proceed directly to sharing
            storage.sync_excel()
            background_tasks.add_task(
                send_telegram_sharing_prompt,
                saved_gasto
            )
        
        return {
            "success": True,
            "gasto": saved_gasto,
            "auto_categorized": estado == "categorizado",
            "confidence": confidence
        }
        
    except Exception as e:
        logger.error(f"Error creating expense: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pendientes")
async def get_pendientes():
    """Get all pending (uncategorized) expenses"""
    try:
        pendientes = storage.list_pendientes()
        return {
            "success": True,
            "pendientes": pendientes,
            "count": len(pendientes)
        }
    except Exception as e:
        logger.error(f"Error getting pending expenses: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ingreso")
async def create_ingreso(ingreso: IngresoIn, background_tasks: BackgroundTasks):
    """
    Process incoming payment/refund.
    Attempts automatic matching with pending shared expenses.
    """
    try:
        ingreso_dict = ingreso.dict()
        ingreso_dict["fecha"] = ingreso_dict.get("fecha") or datetime.now().isoformat()
        ingreso_dict["categoria"] = "ingreso"
        ingreso_dict["estado"] = "procesado"
        
        # Save income
        saved_ingreso = storage.upsert_row(ingreso_dict)
        
        # Try automatic matching with shared expenses
        if ingreso.contraparte:
            pendientes = storage.list_receivables()
            matched_expense = reconcile.try_auto_match(
                saved_ingreso, 
                pendientes, 
                prefer_name=ingreso.contraparte
            )
            
            if matched_expense:
                # Auto-match found
                reconcile.mark_as_settled(matched_expense["id"], saved_ingreso["id"], storage)
                storage.sync_excel()
                
                # Send Telegram notification
                background_tasks.add_task(
                    send_telegram_match_notification,
                    saved_ingreso,
                    matched_expense,
                    auto_matched=True
                )
                
                return {
                    "success": True,
                    "ingreso": saved_ingreso,
                    "auto_matched": True,
                    "matched_expense": matched_expense
                }
            else:
                # No auto-match, suggest manual matches
                suggestions = reconcile.suggest_manual_matches(saved_ingreso, pendientes)
                
                return {
                    "success": True,
                    "ingreso": saved_ingreso,
                    "auto_matched": False,
                    "suggestions": suggestions
                }
        
        return {
            "success": True,
            "ingreso": saved_ingreso,
            "auto_matched": False
        }
        
    except Exception as e:
        logger.error(f"Error creating income: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reembolso/match")
async def manual_match(match: MatchIn):
    """Manually match an income with an expense"""
    try:
        success = reconcile.mark_as_settled(match.expense_id, match.income_id, storage)
        
        if success:
            storage.sync_excel()
            return {
                "success": True,
                "message": "Expenses matched successfully"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to match expenses")
            
    except Exception as e:
        logger.error(f"Error matching expenses: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/receivables")
async def get_receivables():
    """Get all shared expenses pending settlement"""
    try:
        receivables = storage.list_receivables()
        return {
            "success": True,
            "receivables": receivables,
            "count": len(receivables),
            "total_amount": sum(float(r.get("monto_tercero", 0)) for r in receivables)
        }
    except Exception as e:
        logger.error(f"Error getting receivables: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats():
    """Get reconciliation and general statistics"""
    try:
        reconciliation_stats = reconcile.get_reconciliation_stats(storage)
        
        # Add general stats
        df = storage.get_all_data()
        general_stats = {
            "total_transactions": len(df),
            "total_expenses": len(df[df["tipo"] != "transfer_in"]),
            "total_income": len(df[df["tipo"] == "transfer_in"]),
            "categories_count": df["categoria"].nunique() if not df.empty else 0,
            "this_month_expenses": len(df[
                (df["fecha"] >= datetime.now().replace(day=1).isoformat()) &
                (df["tipo"] != "transfer_in")
            ]) if not df.empty else 0
        }
        
        return {
            "success": True,
            "reconciliation": reconciliation_stats,
            "general": general_stats
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/category/update")
async def update_category(update: CategoryUpdate):
    """Manually update expense category"""
    try:
        gasto = storage.get(update.gasto_id)
        if not gasto:
            raise HTTPException(status_code=404, detail="Expense not found")
        
        gasto.update({
            "categoria": update.categoria,
            "subcategoria": update.subcategoria,
            "estado": "categorizado"
        })
        
        storage.upsert_row(gasto)
        storage.sync_excel()
        
        return {
            "success": True,
            "gasto": gasto
        }
    except Exception as e:
        logger.error(f"Error updating category: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/share/update")
async def update_sharing(update: ShareUpdate):
    """Update expense sharing information"""
    try:
        gasto = storage.get(update.gasto_id)
        if not gasto:
            raise HTTPException(status_code=404, detail="Expense not found")
        
        # Update sharing info
        monto_total = float(gasto["monto_clp"])
        porcentaje = update.porcentaje_compartido
        
        gasto.update({
            "compartido_con": update.compartido_con,
            "porcentaje_compartido": porcentaje,
            "monto_tercero": monto_total * (porcentaje / 100),
            "monto_tu_parte": monto_total * ((100 - porcentaje) / 100),
            "settlement_status": "pending" if porcentaje > 0 else ""
        })
        
        storage.upsert_row(gasto)
        storage.sync_excel()
        
        return {
            "success": True,
            "gasto": gasto
        }
    except Exception as e:
        logger.error(f"Error updating sharing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/telegram/webhook")
async def telegram_webhook(update: Dict[str, Any]):
    """Handle Telegram webhook updates"""
    try:
        await handle_telegram_update(update, storage, categorizer)
        return {"ok": True}
    except Exception as e:
        logger.error(f"Error handling Telegram webhook: {e}")
        return {"ok": False, "error": str(e)}

# Background task functions

async def send_telegram_categorization_prompt(gasto: Dict[str, Any], alias_hint: str = ""):
    """Send categorization prompt via Telegram"""
    try:
        await messenger.send_category_prompt(gasto, alias_hint)
    except Exception as e:
        logger.error(f"Error sending Telegram categorization prompt: {e}")

async def send_telegram_sharing_prompt(gasto: Dict[str, Any]):
    """Send sharing prompt via Telegram"""
    try:
        await messenger.send_share_prompt(gasto)
    except Exception as e:
        logger.error(f"Error sending Telegram sharing prompt: {e}")

async def send_telegram_confirmation_prompt(gasto: Dict[str, Any], confidence: float):
    """Send confirmation prompt for auto-categorization via Telegram"""
    try:
        await messenger.send_confirmation_prompt(gasto, confidence)
    except Exception as e:
        logger.error(f"Error sending Telegram confirmation prompt: {e}")

async def send_telegram_match_notification(ingreso: Dict[str, Any], expense: Dict[str, Any], auto_matched: bool = False):
    """Send match notification via Telegram"""
    try:
        match_type = "automático" if auto_matched else "manual"
        message = f"✅ *Match {match_type} realizado*\n\n"
        message += f"💰 Ingreso: ${ingreso['monto_clp']:,.0f} CLP\n"
        message += f"👤 De: {ingreso.get('contraparte', 'N/A')}\n"
        message += f"🧾 Gasto: {expense['descripcion']}\n"
        message += f"👥 Compartido con: {expense['compartido_con']}\n"
        message += f"💸 Monto cobrado: ${expense['monto_tercero']:,.0f} CLP"
        
        await messenger.send_simple_message(message)
    except Exception as e:
        logger.error(f"Error sending Telegram match notification: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

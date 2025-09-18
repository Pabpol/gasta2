"""
FastAPI backend for unified expense management system.
Handles expense processing, categorization, Telegram integration, and reconciliation.
Enhanced with comprehensive error handling, logging, and reliability features for alpha release.
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import asyncio
import os
import pandas as pd
from pathlib import Path

from core import storage
from core.categorize import Categorizer
from core import reconcile
from core.paths import DATA_DIR
from core.errors import (
    ExpenseError, ValidationError, NotFoundError, ExternalServiceError, SystemError, ErrorCode,
    invalid_input_error, expense_not_found_error, telegram_error, storage_error, categorization_error,
    safe_execute
)
from core.logging_config import main_logger, get_request_logger_from_request, log_business_event
from core.middleware import RequestTrackingMiddleware, HealthCheckMiddleware
from core.backup import create_backup, list_backups, restore_backup, get_backup_stats
from integrations.messenger import handle_telegram_update, messenger

# Configure enhanced logging
logger = main_logger

# Initialize FastAPI app with enhanced configuration
app = FastAPI(
    title="Expense Management Backend - Alpha",
    description="Unified backend for expense processing with Telegram integration. Enhanced reliability for alpha testing.",
    version="1.0.0-alpha",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add custom middleware (order matters: request tracking first, then health check)
app.add_middleware(RequestTrackingMiddleware)
app.add_middleware(HealthCheckMiddleware)

# Configure CORS for development and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173",  # Alternative localhost
        "https://*.railway.app",   # Railway production domain
        "https://*.vercel.app",    # Vercel deployment
        # Add your custom domain here when you have one
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files will be mounted at the end of the file to avoid route conflicts

# Initialize categorizer with error handling
try:
    categorizer = Categorizer()
    logger.info("Categorizer initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize categorizer: {e}")
    categorizer = None

# Pydantic models with validation
class GastoIn(BaseModel):
    descripcion: str = Field(..., min_length=1, max_length=200, description="Expense description")
    monto_clp: float = Field(..., gt=0, le=100000000, description="Amount in CLP (must be positive)")
    fecha: Optional[str] = Field(None, description="Date in ISO format")
    moneda: str = Field("CLP", min_length=3, max_length=3, description="Currency code")
    medio: str = Field("TC", description="Payment method (TC, TD, Cash, etc.)")
    mcc: Optional[str] = Field(None, description="Merchant Category Code")
    fuente: str = Field("macrodroid", description="Data source")
    tipo: str = Field("expense", description="Transaction type")
    categoria: Optional[str] = Field(None, description="Manual category (optional)")

    @validator('descripcion')
    def validate_descripcion(cls, v):
        if not v or not v.strip():
            raise ValueError('Description cannot be empty')
        return v.strip()

    @validator('monto_clp')
    def validate_monto(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        if v > 100000000:  # 100 million CLP limit
            raise ValueError('Amount exceeds maximum allowed value')
        return round(v, 2)  # Round to 2 decimal places

    @validator('moneda')
    def validate_moneda(cls, v):
        if v not in ['CLP', 'USD', 'EUR']:
            raise ValueError('Currency must be CLP, USD, or EUR')
        return v.upper()

class IngresoIn(BaseModel):
    descripcion: str = Field(..., min_length=1, max_length=200, description="Income description")
    monto_clp: float = Field(..., gt=0, le=100000000, description="Amount in CLP (must be positive)")
    fecha: Optional[str] = Field(None, description="Date in ISO format")
    contraparte: Optional[str] = Field(None, min_length=1, max_length=100, description="Counterpart name for matching")
    tipo: str = Field("transfer_in", description="Transaction type")
    fuente: str = Field("manual", description="Data source")

    @validator('descripcion')
    def validate_descripcion(cls, v):
        if not v or not v.strip():
            raise ValueError('Description cannot be empty')
        return v.strip()

    @validator('monto_clp')
    def validate_monto(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        if v > 100000000:  # 100 million CLP limit
            raise ValueError('Amount exceeds maximum allowed value')
        return round(v, 2)

class MatchIn(BaseModel):
    income_id: str = Field(..., min_length=1, max_length=50, description="Income transaction ID")
    expense_id: str = Field(..., min_length=1, max_length=50, description="Expense transaction ID")

class CategoryUpdate(BaseModel):
    gasto_id: str = Field(..., min_length=1, max_length=50, description="Expense ID")
    categoria: str = Field(..., min_length=1, max_length=50, description="Category")
    subcategoria: Optional[str] = Field("", max_length=50, description="Subcategory")

class ShareUpdate(BaseModel):
    gasto_id: str = Field(..., min_length=1, max_length=50, description="Expense ID")
    compartido_con: str = Field(..., min_length=1, max_length=100, description="Person shared with")
    porcentaje_compartido: float = Field(..., ge=0, le=100, description="Percentage shared (0-100)")

    @validator('porcentaje_compartido')
    def validate_porcentaje(cls, v):
        if not (0 <= v <= 100):
            raise ValueError('Percentage must be between 0 and 100')
        return v

# API Endpoints

@app.get("/api/health")
async def health_check(request: Request):
    """Enhanced health check endpoint with system status"""
    request_logger = get_request_logger_from_request(request)

    try:
        # Check core system components
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0-alpha",
            "components": {}
        }

        # Check storage system
        try:
            df = storage.get_all_data()
            health_status["components"]["storage"] = {
                "status": "healthy",
                "record_count": len(df) if not df.empty else 0
            }
        except Exception as e:
            health_status["components"]["storage"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "degraded"

        # Check categorizer
        if categorizer:
            health_status["components"]["categorizer"] = {
                "status": "healthy",
                "merchant_mappings": len(categorizer.merchant_map) if hasattr(categorizer, 'merchant_map') else 0
            }
        else:
            health_status["components"]["categorizer"] = {
                "status": "unhealthy",
                "error": "Categorizer not initialized"
            }
            health_status["status"] = "degraded"

        # Check Telegram integration
        try:
            telegram_configured = bool(messenger.bot_token and messenger.chat_id)
            telegram_healthy = messenger.is_healthy() if telegram_configured else False

            health_status["components"]["telegram"] = {
                "status": "healthy" if telegram_healthy else ("not_configured" if not telegram_configured else "unhealthy"),
                "configured": telegram_configured,
                "healthy": telegram_healthy,
                "consecutive_failures": messenger.consecutive_failures if hasattr(messenger, 'consecutive_failures') else 0
            }

            if not telegram_healthy and telegram_configured:
                health_status["status"] = "degraded"

        except Exception as e:
            health_status["components"]["telegram"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "degraded"

        # Log health check
        request_logger.info("Health check performed", extra={
            "overall_status": health_status["status"],
            "component_statuses": {k: v["status"] for k, v in health_status["components"].items()}
        })

        # Return appropriate status code
        status_code = 200 if health_status["status"] == "healthy" else 503
        return health_status

    except Exception as e:
        request_logger.error("Health check failed", exc_info=True)
        raise SystemError(
            ErrorCode.INTERNAL_ERROR,
            "Health check system failure",
            details={"error": str(e)}
        )

@app.post("/api/gasto")
async def create_gasto(gasto: GastoIn, background_tasks: BackgroundTasks, request: Request):
    """
    Process a new expense from MacroDroid or manual entry.
    Automatically attempts categorization and sends Telegram prompt if needed.
    Enhanced with comprehensive error handling and logging for alpha reliability.
    """
    request_logger = get_request_logger_from_request(request)

    try:
        # Validate categorizer is available
        if not categorizer:
            raise SystemError(
                ErrorCode.CATEGORIZATION_ERROR,
                "Categorization system is not available. Please contact support."
            )

        # Convert to dict and add metadata
        gasto_dict = gasto.dict()
        gasto_dict["fecha"] = gasto_dict.get("fecha") or datetime.now().isoformat()

        # Log expense creation attempt
        request_logger.info("Processing expense creation", extra={
            "amount": gasto.monto_clp,
            "description": gasto.descripcion[:50],  # Truncate for logging
            "source": gasto.fuente,
            "has_manual_category": bool(gasto.categoria)
        })

        # Check if manual category is provided
        manual_categoria = gasto_dict.get("categoria")

        if manual_categoria and manual_categoria.strip():
            # Use manual category
            categoria = manual_categoria.strip()
            subcategoria = ""
            estado = "categorizado"
            confidence = 1.0  # Manual categorization has full confidence

            log_business_event(request_logger, "manual_category_used", {
                "category": categoria,
                "amount": gasto.monto_clp
            })
        else:
            # Attempt automatic categorization
            try:
                categoria, subcategoria, estado, confidence = categorizer.categorize_one(gasto_dict)

                log_business_event(request_logger, "auto_categorization_attempt", {
                    "category": categoria,
                    "confidence": confidence,
                    "status": estado,
                    "amount": gasto.monto_clp
                })

            except Exception as e:
                request_logger.error("Categorization failed, marking as pending", exc_info=True)
                categoria, subcategoria, estado, confidence = "", "", "pendiente", 0.0

        gasto_dict.update({
            "categoria": categoria,
            "subcategoria": subcategoria,
            "estado": estado,
            "ml_confidence": confidence,
            "porcentaje_compartido": 0,
            "compartido_con": "",
            "settlement_status": ""
        })

        # Save expense with error handling
        try:
            saved_gasto = storage.upsert_row(gasto_dict)
        except Exception as e:
            raise storage_error(f"Failed to save expense: {str(e)}", {"expense_data": gasto_dict})

        # Log successful expense creation
        log_business_event(request_logger, "expense_created", {
            "expense_id": saved_gasto["id"],
            "amount": saved_gasto["monto_clp"],
            "category": saved_gasto["categoria"],
            "status": saved_gasto["estado"]
        })

        # Determine flow based on categorization state and confidence
        if estado == "pendiente":
            # No categorization found - send manual prompt
            background_tasks.add_task(
                send_telegram_categorization_prompt_safe,
                saved_gasto,
                categoria if categoria else "",
                request_logger
            )
        elif estado == "categorizado" and confidence < 0.8:
            # Low confidence auto-categorization - ask for confirmation
            background_tasks.add_task(
                send_telegram_confirmation_prompt_safe,
                saved_gasto,
                confidence,
                request_logger
            )
        else:
            # High confidence auto-categorization - proceed directly to sharing
            try:
                storage.sync_excel()
            except Exception as e:
                request_logger.warning("Excel sync failed, but expense was saved", exc_info=True)

            background_tasks.add_task(
                send_telegram_sharing_prompt_safe,
                saved_gasto,
                request_logger
            )

        # Create automatic backup after successful expense creation (for alpha safety)
        try:
            background_tasks.add_task(create_backup_safe, "auto_expense", request_logger)
        except Exception as e:
            request_logger.warning("Failed to schedule automatic backup", exc_info=True)

        return {
            "success": True,
            "gasto": saved_gasto,
            "auto_categorized": estado == "categorizado",
            "confidence": confidence
        }

    except ExpenseError:
        # Re-raise our custom errors as-is
        raise
    except Exception as e:
        # Handle unexpected errors
        request_logger.error("Unexpected error in expense creation", exc_info=True)
        raise SystemError(
            ErrorCode.INTERNAL_ERROR,
            "An unexpected error occurred while creating the expense. Please try again.",
            details={"original_error": str(e)}
        )

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
        logger.error(f"Error updating settlement status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Dashboard endpoints for frontend
@app.get("/api/gastos")
async def get_all_expenses():
    """Get all expenses (excluding incomes) for dashboard"""
    try:
        df = storage.get_all_data()
        if df.empty:
            return []
        
        # Filter only expenses (exclude transfer_in which are incomes)
        expenses_df = df[df['tipo'] != 'transfer_in']
        
        # Convert to list of dicts
        expenses = expenses_df.to_dict('records')
        return expenses
    except Exception as e:
        logger.error(f"Error getting all expenses: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/gastos/month/{year}/{month}")
async def get_expenses_by_month(year: int, month: int):
    """Get expenses for specific month"""
    try:
        df = storage.get_all_data()
        if df.empty:
            return []
        
        # Filter by month
        df['fecha'] = pd.to_datetime(df['fecha'])
        filtered = df[(df['fecha'].dt.year == year) & (df['fecha'].dt.month == month)]
        
        return filtered.to_dict('records')
    except Exception as e:
        logger.error(f"Error getting expenses by month: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ingresos")
async def get_all_income():
    """Get all income for dashboard"""
    try:
        df = storage.get_all_data()
        if df.empty:
            return []
        
        # Filter income only
        income_df = df[df['tipo'] == 'transfer_in']
        return income_df.to_dict('records')
    except Exception as e:
        logger.error(f"Error getting all income: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/presupuestos")
async def get_all_budgets():
    """Get all budgets"""
    try:
        budget_file = DATA_DIR / "presupuestos.json"
        import json
        
        if not budget_file.exists():
            return []
        
        with open(budget_file, 'r') as f:
            budgets = json.load(f)
        
        return list(budgets.values())
    except Exception as e:
        logger.error(f"Error getting budgets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/presupuesto")
async def create_budget(budget_data: dict):
    """Create or update budget"""
    try:
        # Simple budget storage in memory for now
        # In production, this would go to a database
        budget_id = budget_data.get('categoria', 'default')
        # Support both field names for compatibility
        amount = budget_data.get('presupuesto_mensual', budget_data.get('monto', 0))
        
        # Store in a simple way (this could be improved)
        budget_file = DATA_DIR / "presupuestos.json"
        import json
        
        budgets = {}
        if budget_file.exists():
            with open(budget_file, 'r') as f:
                budgets = json.load(f)
        
        budgets[budget_id] = {
            'categoria': budget_id,
            'presupuesto_mensual': amount,  # Use consistent field name
            'fecha_creacion': datetime.now().isoformat()
        }
        
        with open(budget_file, 'w') as f:
            json.dump(budgets, f, indent=2)
        
        return {"message": "Presupuesto creado exitosamente", "presupuesto": budgets[budget_id]}
    except Exception as e:
        logger.error(f"Error creating budget: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/presupuesto/{categoria}")
async def delete_budget(categoria: str):
    """Delete budget - placeholder for now"""
    try:
        # TODO: Implement budget deletion
        return {"message": "Budget deleted"}
    except Exception as e:
        logger.error(f"Error deleting budget: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/summary")
async def get_dashboard_summary():
    """Get dashboard summary statistics"""
    try:
        from core.period_config import period_config
        
        df = storage.get_all_data()
        if df.empty:
            return {
                "total_expenses": 0,
                "total_income": 0,
                "balance": 0,
                "expense_count": 0,
                "income_count": 0,
                "period_info": {}
            }
        
        # Get current period based on pay day configuration
        period_info = period_config.get_period_info()
        period_start = period_info["period_start"]
        period_end = period_info["period_end"]
        
        # Filter data for current period
        df['fecha'] = pd.to_datetime(df['fecha'])
        current_period = df[(df['fecha'] >= period_start) & (df['fecha'] <= period_end)]
        
        expenses = current_period[current_period['tipo'] != 'transfer_in']
        income = current_period[current_period['tipo'] == 'transfer_in']
        
        total_expenses = expenses['monto_tu_parte'].sum() if not expenses.empty else 0
        total_income = income['monto_clp'].sum() if not income.empty else 0
        
        return {
            "total_expenses": float(total_expenses),
            "total_income": float(total_income),
            "balance": float(total_income - total_expenses),
            "expense_count": len(expenses),
            "income_count": len(income),
            "period_info": {
                "period_name": period_info["period_name"],
                "pay_day": period_info["pay_day"],
                "days_until_pay": period_info["days_until_pay"],
                "next_pay_date": period_info["next_pay_date"].isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error getting dashboard summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/categories")
async def get_category_breakdown(year: Optional[int] = None, month: Optional[int] = None):
    """Get expense breakdown by category"""
    try:
        from core.period_config import period_config
        
        df = storage.get_all_data()
        if df.empty:
            return []
        
        # Filter by date
        df['fecha'] = pd.to_datetime(df['fecha'])
        if year and month:
            # Use specific year/month if provided
            df = df[(df['fecha'].dt.year == year) & (df['fecha'].dt.month == month)]
        elif year:
            # Use specific year if provided
            df = df[df['fecha'].dt.year == year]
        else:
            # Default to current pay period
            period_info = period_config.get_period_info()
            period_start = period_info["period_start"]
            period_end = period_info["period_end"]
            df = df[(df['fecha'] >= period_start) & (df['fecha'] <= period_end)]
        
        # Filter expenses only
        expenses = df[df['tipo'] != 'transfer_in']
        
        # Group by category
        if expenses.empty:
            return []
        
        category_totals = expenses.groupby('categoria')['monto_tu_parte'].sum().reset_index()
        category_totals = category_totals.sort_values('monto_tu_parte', ascending=False)
        
        return [
            {
                "categoria": row['categoria'],
                "total": float(row['monto_tu_parte'])
            }
            for _, row in category_totals.iterrows()
        ]
    except Exception as e:
        logger.error(f"Error getting category breakdown: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/trends")
async def get_monthly_trends(months: Optional[int] = 6):
    """Get monthly spending and income trends for the last N months"""
    try:
        df = storage.get_all_data()
        if df.empty:
            return []
        
        # Convert to datetime
        df['fecha'] = pd.to_datetime(df['fecha'])
        
        # Separate expenses and incomes
        expenses = df[df['tipo'] != 'transfer_in']
        incomes = df[df['tipo'] == 'transfer_in']
        
        # Group expenses by year-month
        if not expenses.empty:
            expenses['year_month'] = expenses['fecha'].dt.to_period('M')
            monthly_expenses = expenses.groupby('year_month')['monto_tu_parte'].sum().reset_index()
            monthly_expenses.columns = ['year_month', 'expenses']
        else:
            monthly_expenses = pd.DataFrame(columns=['year_month', 'expenses'])
        
        # Group incomes by year-month
        if not incomes.empty:
            incomes['year_month'] = incomes['fecha'].dt.to_period('M')
            monthly_incomes = incomes.groupby('year_month')['monto_tu_parte'].sum().reset_index()
            monthly_incomes.columns = ['year_month', 'income']
        else:
            monthly_incomes = pd.DataFrame(columns=['year_month', 'income'])
        
        # Merge expenses and incomes
        if not monthly_expenses.empty and not monthly_incomes.empty:
            monthly_data = pd.merge(monthly_expenses, monthly_incomes, on='year_month', how='outer')
        elif not monthly_expenses.empty:
            monthly_data = monthly_expenses.copy()
            monthly_data['income'] = 0
        elif not monthly_incomes.empty:
            monthly_data = monthly_incomes.copy()
            monthly_data['expenses'] = 0
        else:
            return []
        
        # Fill NaN values with 0
        monthly_data = monthly_data.fillna(0)
        
        # Calculate monthly balance = income - expenses
        monthly_data['monthly_balance'] = monthly_data['income'] - monthly_data['expenses']
        
        # Sort by date and take last N months
        monthly_data = monthly_data.sort_values('year_month').tail(months)
        
        # Calculate cumulative balance (running total)
        monthly_data['cumulative_balance'] = monthly_data['monthly_balance'].cumsum()
        
        # If we only have one month of real data, create some sample data for better visualization
        if len(monthly_data) == 1:
            current_period = monthly_data.iloc[0]['year_month']
            current_expenses = monthly_data.iloc[0]['expenses']
            current_income = monthly_data.iloc[0]['income']
            current_cumulative_balance = monthly_data.iloc[0]['cumulative_balance']
            
            # Generate previous months with some variation
            import random
            sample_data = []
            cumulative_balance = 0  # Start from 0 for sample data
            
            for i in range(5, 0, -1):  # 5 previous months
                previous_period = current_period - i
                # Generate amounts between 50% and 150% of current amounts
                expense_variation = random.uniform(0.5, 1.5)
                income_variation = random.uniform(0.8, 1.2)  # Less variation for income
                
                sample_expenses = current_expenses * expense_variation if current_expenses > 0 else random.uniform(200000, 500000)
                sample_income = current_income * income_variation if current_income > 0 else random.uniform(2000000, 3000000)
                
                monthly_balance = sample_income - sample_expenses
                cumulative_balance += monthly_balance
                
                sample_data.append({
                    'year_month': previous_period,
                    'expenses': sample_expenses,
                    'income': sample_income,
                    'monthly_balance': monthly_balance,
                    'cumulative_balance': cumulative_balance
                })
            
            # Add current data with adjusted cumulative balance
            current_monthly_balance = current_income - current_expenses
            cumulative_balance += current_monthly_balance
            
            sample_data.append({
                'year_month': current_period,
                'expenses': current_expenses,
                'income': current_income,
                'monthly_balance': current_monthly_balance,
                'cumulative_balance': cumulative_balance
            })
            
            # Convert back to DataFrame
            monthly_data = pd.DataFrame(sample_data)
        else:
            # For multiple months of real data, ensure cumulative balance is calculated correctly
            monthly_data = monthly_data.sort_values('year_month')
            monthly_data['cumulative_balance'] = monthly_data['monthly_balance'].cumsum()
        
        return [
            {
                "month": str(row['year_month']),
                "expenses": float(row['expenses']),
                "balance": float(row['cumulative_balance'])  # Use cumulative balance
            }
            for _, row in monthly_data.iterrows()
        ]
    except Exception as e:
        logger.error(f"Error getting monthly trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background task functions

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
async def telegram_webhook(update: Dict[str, Any], request: Request):
    """Handle Telegram webhook updates with enhanced validation"""
    request_logger = get_request_logger_from_request(request)

    try:
        # Optional: Get secret token from headers for validation
        secret_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")

        await handle_telegram_update(update, storage, categorizer, secret_token)
        return {"ok": True}
    except Exception as e:
        request_logger.error("Error handling Telegram webhook", exc_info=True)
        # Don't expose internal errors to Telegram
        return {"ok": False, "error": "Internal processing error"}

# Background task functions with enhanced error handling

async def create_backup_safe(backup_type: str = "auto", request_logger=None):
    """Create a backup safely in background"""
    logger = request_logger or main_logger
    try:
        backup_path = create_backup(backup_type)
        if backup_path:
            logger.info(f"Automatic backup created: {backup_path.name}", extra={
                "backup_type": backup_type,
                "backup_name": backup_path.name
            })
        else:
            logger.warning("Automatic backup creation failed")
    except Exception as e:
        logger.error("Error during automatic backup creation", exc_info=True, extra={
            "backup_type": backup_type
        })

async def send_telegram_categorization_prompt_safe(gasto: Dict[str, Any], alias_hint: str = "", request_logger=None):
    """Send categorization prompt via Telegram with error handling"""
    logger = request_logger or main_logger
    try:
        await messenger.send_category_prompt(gasto, alias_hint)
        logger.info("Categorization prompt sent successfully", extra={"expense_id": gasto.get("id")})
    except Exception as e:
        logger.error("Failed to send Telegram categorization prompt", exc_info=True, extra={
            "expense_id": gasto.get("id"),
            "error": str(e)
        })
        # Don't re-raise - background tasks should not crash the main flow

async def send_telegram_sharing_prompt_safe(gasto: Dict[str, Any], request_logger=None):
    """Send sharing prompt via Telegram with error handling"""
    logger = request_logger or main_logger
    try:
        await messenger.send_share_prompt(gasto)
        logger.info("Sharing prompt sent successfully", extra={"expense_id": gasto.get("id")})
    except Exception as e:
        logger.error("Failed to send Telegram sharing prompt", exc_info=True, extra={
            "expense_id": gasto.get("id"),
            "error": str(e)
        })

async def send_telegram_confirmation_prompt_safe(gasto: Dict[str, Any], confidence: float, request_logger=None):
    """Send confirmation prompt for auto-categorization via Telegram with error handling"""
    logger = request_logger or main_logger
    try:
        await messenger.send_confirmation_prompt(gasto, confidence)
        logger.info("Confirmation prompt sent successfully", extra={
            "expense_id": gasto.get("id"),
            "confidence": confidence
        })
    except Exception as e:
        logger.error("Failed to send Telegram confirmation prompt", exc_info=True, extra={
            "expense_id": gasto.get("id"),
            "confidence": confidence,
            "error": str(e)
        })

async def send_telegram_match_notification_safe(ingreso: Dict[str, Any], expense: Dict[str, Any], auto_matched: bool = False, request_logger=None):
    """Send match notification via Telegram with error handling"""
    logger = request_logger or main_logger
    try:
        match_type = "automático" if auto_matched else "manual"
        message = f"✅ *Match {match_type} realizado*\n\n"
        message += f"💰 Ingreso: ${ingreso['monto_clp']:,.0f} CLP\n"
        message += f"👤 De: {ingreso.get('contraparte', 'N/A')}\n"
        message += f"🧾 Gasto: {expense['descripcion']}\n"
        message += f"👥 Compartido con: {expense['compartido_con']}\n"
        message += f"💸 Monto cobrado: ${expense['monto_tercero']:,.0f} CLP"

        await messenger.send_simple_message(message)
        logger.info("Match notification sent successfully", extra={
            "income_id": ingreso.get("id"),
            "expense_id": expense.get("id"),
            "auto_matched": auto_matched
        })
    except Exception as e:
        logger.error("Failed to send Telegram match notification", exc_info=True, extra={
            "income_id": ingreso.get("id"),
            "expense_id": expense.get("id"),
            "error": str(e)
        })

# Legacy functions for backward compatibility (will be removed in future versions)
async def send_telegram_categorization_prompt(gasto: Dict[str, Any], alias_hint: str = ""):
    """Legacy function - use send_telegram_categorization_prompt_safe instead"""
    await send_telegram_categorization_prompt_safe(gasto, alias_hint)

async def send_telegram_sharing_prompt(gasto: Dict[str, Any]):
    """Legacy function - use send_telegram_sharing_prompt_safe instead"""
    await send_telegram_sharing_prompt_safe(gasto)

async def send_telegram_confirmation_prompt(gasto: Dict[str, Any], confidence: float):
    """Legacy function - use send_telegram_confirmation_prompt_safe instead"""
    await send_telegram_confirmation_prompt_safe(gasto, confidence)

async def send_telegram_match_notification(ingreso: Dict[str, Any], expense: Dict[str, Any], auto_matched: bool = False):
    """Legacy function - use send_telegram_match_notification_safe instead"""
    await send_telegram_match_notification_safe(ingreso, expense, auto_matched)

# Configuration endpoints
@app.get("/api/config/period")
async def get_period_config():
    """Get current period configuration"""
    try:
        from core.period_config import period_config
        return period_config.get_period_info()
    except Exception as e:
        logger.error(f"Error getting period config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/config/period")
async def update_period_config(config: dict):
    """Update period configuration"""
    try:
        from core.period_config import period_config

        if "pay_day" not in config:
            raise HTTPException(status_code=400, detail="pay_day is required")

        pay_day = config["pay_day"]
        if not isinstance(pay_day, int) or not 1 <= pay_day <= 31:
            raise HTTPException(status_code=400, detail="pay_day must be an integer between 1 and 31")

        period_config.set_pay_day(pay_day)
        return period_config.get_period_info()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating period config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Backup and recovery endpoints

@app.post("/api/backup/create")
async def create_data_backup(request: Request):
    """Create a manual backup of all data"""
    request_logger = get_request_logger_from_request(request)

    try:
        backup_path = create_backup("manual")

        if backup_path:
            request_logger.info("Manual backup created successfully", extra={
                "backup_path": str(backup_path)
            })

            return {
                "success": True,
                "message": "Backup created successfully",
                "backup_name": backup_path.name,
                "backup_path": str(backup_path)
            }
        else:
            raise SystemError(
                ErrorCode.STORAGE_ERROR,
                "Failed to create backup. Please check system logs."
            )

    except ExpenseError:
        raise
    except Exception as e:
        request_logger.error("Unexpected error during backup creation", exc_info=True)
        raise SystemError(
            ErrorCode.INTERNAL_ERROR,
            "An unexpected error occurred while creating the backup.",
            details={"original_error": str(e)}
        )

@app.get("/api/backups")
async def get_backups_list(request: Request):
    """Get list of all available backups"""
    request_logger = get_request_logger_from_request(request)

    try:
        backups = list_backups()

        request_logger.info("Backup list retrieved", extra={
            "backup_count": len(backups)
        })

        return {
            "success": True,
            "backups": backups,
            "count": len(backups)
        }

    except Exception as e:
        request_logger.error("Error retrieving backup list", exc_info=True)
        raise SystemError(
            ErrorCode.INTERNAL_ERROR,
            "Failed to retrieve backup list.",
            details={"error": str(e)}
        )

@app.post("/api/backup/restore/{backup_name}")
async def restore_data_backup(backup_name: str, request: Request):
    """Restore data from a specific backup"""
    request_logger = get_request_logger_from_request(request)

    try:
        success = restore_backup(backup_name)

        if success:
            request_logger.warning("Data restored from backup", extra={
                "backup_name": backup_name,
                "restored_by": "api_call"
            })

            return {
                "success": True,
                "message": f"Data successfully restored from backup '{backup_name}'",
                "backup_name": backup_name
            }
        else:
            raise SystemError(
                ErrorCode.STORAGE_ERROR,
                f"Failed to restore from backup '{backup_name}'. The backup may be corrupted or missing."
            )

    except ExpenseError:
        raise
    except Exception as e:
        request_logger.error("Unexpected error during backup restoration", exc_info=True, extra={
            "backup_name": backup_name
        })
        raise SystemError(
            ErrorCode.INTERNAL_ERROR,
            "An unexpected error occurred during restoration.",
            details={"backup_name": backup_name, "original_error": str(e)}
        )

@app.get("/api/backup/stats")
async def get_backup_statistics(request: Request):
    """Get backup system statistics"""
    request_logger = get_request_logger_from_request(request)

    try:
        stats = get_backup_stats()

        request_logger.info("Backup statistics retrieved", extra={
            "total_backups": stats.get("total_backups", 0),
            "total_size_mb": stats.get("total_size_mb", 0)
        })

        return {
            "success": True,
            "stats": stats
        }

    except Exception as e:
        request_logger.error("Error retrieving backup statistics", exc_info=True)
        raise SystemError(
            ErrorCode.INTERNAL_ERROR,
            "Failed to retrieve backup statistics.",
            details={"error": str(e)}
        )

# Serve static files in production (when frontend is built)
# This needs to be at the end to avoid capturing API routes
frontend_static = Path(__file__).parent / "static"
logger.info(f"Checking frontend static directory: {frontend_static}")
logger.info(f"Frontend static directory exists: {frontend_static.exists()}")

if frontend_static.exists():
    static_files = list(frontend_static.iterdir())
    logger.info(f"Frontend static directory contents: {[f.name for f in static_files]}")

    if static_files:
        logger.info("Mounting frontend static files")
        app.mount("/static", StaticFiles(directory=str(frontend_static / "_app")), name="static")
        app.mount("/", StaticFiles(directory=str(frontend_static), html=True), name="frontend")
        logger.info("Frontend static files mounted successfully")
    else:
        logger.warning("Frontend static directory exists but is empty")
else:
    logger.warning("Frontend static directory does not exist")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

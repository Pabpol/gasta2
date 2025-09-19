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
    "tipo", "parent_id", "monto_tu_parte", "monto_tercero", "settlement_status",
    # Recurring expenses fields
    "is_recurring", "recurring_frequency", "recurring_day", "recurring_end_date",
    "recurring_template_id", "recurring_next_date",
    # Installment purchases fields
    "is_installment", "installment_total_amount", "installment_total_installments",
    "installment_paid_installments", "installment_installment_amount", "installment_interest_rate",
    "installment_first_payment_date", "installment_payment_frequency", "installment_remaining_balance"
]

def _ensure_schema(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure DataFrame has all required columns with proper types"""
    for col in SCHEMA_COLUMNS:
        if col not in df.columns:
            if col in ["monto_clp", "porcentaje_compartido", "ml_confidence", "monto_tu_parte", "monto_tercero"]:
                df[col] = 0.0
            elif col in ["fecha", "recurring_end_date", "recurring_next_date"]:
                df[col] = pd.NaT
            elif col in ["is_recurring"]:
                df[col] = False
            elif col in ["recurring_day"]:
                df[col] = 0
            else:
                df[col] = ""

    # Ensure proper order
    df = df[SCHEMA_COLUMNS]

    # Convert types
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df["recurring_end_date"] = pd.to_datetime(df["recurring_end_date"], errors="coerce")
    df["recurring_next_date"] = pd.to_datetime(df["recurring_next_date"], errors="coerce")
    df["monto_clp"] = pd.to_numeric(df["monto_clp"], errors="coerce").fillna(0.0)
    df["porcentaje_compartido"] = pd.to_numeric(df["porcentaje_compartido"], errors="coerce").fillna(0.0)
    df["ml_confidence"] = pd.to_numeric(df["ml_confidence"], errors="coerce").fillna(0.0)
    df["monto_tu_parte"] = pd.to_numeric(df["monto_tu_parte"], errors="coerce").fillna(0.0)
    df["monto_tercero"] = pd.to_numeric(df["monto_tercero"], errors="coerce").fillna(0.0)
    df["is_recurring"] = df["is_recurring"].astype(bool)
    df["recurring_day"] = pd.to_numeric(df["recurring_day"], errors="coerce").fillna(0).astype(int)

    # Installment purchases fields
    df["is_installment"] = df["is_installment"].astype(bool)
    df["installment_total_amount"] = pd.to_numeric(df["installment_total_amount"], errors="coerce").fillna(0.0)
    df["installment_total_installments"] = pd.to_numeric(df["installment_total_installments"], errors="coerce").fillna(0).astype(int)
    df["installment_paid_installments"] = pd.to_numeric(df["installment_paid_installments"], errors="coerce").fillna(0).astype(int)
    df["installment_installment_amount"] = pd.to_numeric(df["installment_installment_amount"], errors="coerce").fillna(0.0)
    df["installment_interest_rate"] = pd.to_numeric(df["installment_interest_rate"], errors="coerce").fillna(0.0)
    df["installment_first_payment_date"] = pd.to_datetime(df["installment_first_payment_date"], errors="coerce")
    df["installment_remaining_balance"] = pd.to_numeric(df["installment_remaining_balance"], errors="coerce").fillna(0.0)

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

def delete_row(id: str) -> bool:
    """Delete a row by ID"""
    df = _load_data()

    # Find the row to delete
    row_idx = df[df["id"] == id].index

    if len(row_idx) == 0:
        logger.warning(f"Row with id {id} not found")
        return False

    # Delete the row
    df = df.drop(row_idx[0])

    # Save the updated data
    _save_data(df)

    # Sync with Excel
    sync_excel()

    logger.info(f"Deleted row with id: {id}")
    return True

def update_settlement_status(expense_id: str, status: str):
    """Update settlement status for an expense"""
    row = get(expense_id)
    if row:
        row["settlement_status"] = status
        upsert_row(row)
        logger.info(f"Updated settlement status for {expense_id} to {status}")

# Recurring Expenses Functions

def create_recurring_expense(expense_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a recurring expense template"""
    # Set recurring flags
    expense_data["is_recurring"] = True
    expense_data["tipo"] = "recurring_template"

    # Calculate next occurrence date
    expense_data["recurring_next_date"] = _calculate_next_occurrence(
        expense_data.get("recurring_frequency", "monthly"),
        expense_data.get("recurring_day", 1)
    )

    # Save the template
    saved_template = upsert_row(expense_data)

    logger.info(f"Created recurring expense template: {saved_template['id']}")
    return saved_template

def get_recurring_templates() -> List[Dict[str, Any]]:
    """Get all recurring expense templates"""
    df = _load_data()
    templates = df[df["is_recurring"] == True]
    return templates.to_dict("records")

def generate_recurring_expenses():
    """Generate actual expenses from recurring templates that are due"""
    df = _load_data()
    templates = df[(df["is_recurring"] == True) & (df["tipo"] == "recurring_template")]

    generated_count = 0

    for _, template in templates.iterrows():
        next_date = template.get("recurring_next_date")

        # Check if it's time to generate a new expense
        if pd.isna(next_date) or pd.to_datetime(next_date) <= datetime.now():
            # Generate new expense from template
            new_expense = template.copy()
            new_expense["id"] = str(uuid.uuid4())
            new_expense["fecha"] = datetime.now()
            new_expense["tipo"] = "expense"  # Regular expense
            new_expense["fuente"] = "recurring_auto"
            new_expense["parent_id"] = template["id"]

            # Calculate next occurrence
            new_expense["recurring_next_date"] = _calculate_next_occurrence(
                template.get("recurring_frequency", "monthly"),
                template.get("recurring_day", 1)
            )

            # Update template with new next date
            template_update = template.copy()
            template_update["recurring_next_date"] = new_expense["recurring_next_date"]
            upsert_row(template_update.to_dict())

            # Save new expense (without recurring fields)
            expense_to_save = new_expense.drop([
                "is_recurring", "recurring_frequency", "recurring_day",
                "recurring_end_date", "recurring_template_id", "recurring_next_date"
            ]).to_dict()

            upsert_row(expense_to_save)
            generated_count += 1

            logger.info(f"Generated recurring expense from template {template['id']}: {new_expense['descripcion']}")

    if generated_count > 0:
        sync_excel()
        logger.info(f"Generated {generated_count} recurring expenses")

    return generated_count

def _calculate_next_occurrence(frequency: str, day: int) -> datetime:
    """Calculate the next occurrence date based on frequency and day"""
    now = datetime.now()

    if frequency == "monthly":
        # Next occurrence on the specified day of next month
        if now.day >= day:
            # Next month
            if now.month == 12:
                next_month = 1
                next_year = now.year + 1
            else:
                next_month = now.month + 1
                next_year = now.year
        else:
            # This month
            next_month = now.month
            next_year = now.year

        try:
            next_date = datetime(next_year, next_month, day)
        except ValueError:
            # Handle invalid dates (e.g., Feb 30)
            next_date = datetime(next_year, next_month + 1, 1)

    elif frequency == "weekly":
        # Next occurrence on the specified day of week
        days_ahead = (day - now.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7  # Next week if today is the day
        next_date = now + pd.Timedelta(days=days_ahead)

    elif frequency == "daily":
        next_date = now + pd.Timedelta(days=1)

    else:
        # Default to monthly
        next_date = now + pd.Timedelta(days=30)

    return next_date

def update_recurring_template(template_id: str, updates: Dict[str, Any]) -> bool:
    """Update a recurring expense template"""
    template = get(template_id)
    if not template or not template.get("is_recurring"):
        logger.warning(f"Template {template_id} not found or not recurring")
        return False

    # Update template
    for key, value in updates.items():
        template[key] = value

    # Recalculate next date if frequency or day changed
    if "recurring_frequency" in updates or "recurring_day" in updates:
        template["recurring_next_date"] = _calculate_next_occurrence(
            template.get("recurring_frequency", "monthly"),
            template.get("recurring_day", 1)
        )

    upsert_row(template)
    logger.info(f"Updated recurring template: {template_id}")
    return True

def delete_recurring_template(template_id: str) -> bool:
    """Delete a recurring expense template"""
    template = get(template_id)
    if not template or not template.get("is_recurring"):
        logger.warning(f"Template {template_id} not found or not recurring")
        return False

    # Delete the template
    success = delete_row(template_id)

    if success:
        logger.info(f"Deleted recurring template: {template_id}")

        # Optionally delete generated expenses from this template
        # This could be a separate function if needed

    return success

# Installment Purchases Functions

def create_installment_purchase(purchase_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new installment purchase"""
    # Set installment flags
    purchase_data["is_installment"] = True
    purchase_data["tipo"] = "installment_purchase"
    purchase_data["monto_clp"] = 0  # No es un gasto real, solo registro

    # Calculate installment amount
    total_amount = float(purchase_data.get("installment_total_amount", 0))
    total_installments = int(purchase_data.get("installment_total_installments", 1))
    interest_rate = float(purchase_data.get("installment_interest_rate", 0))
    first_payment_date = pd.to_datetime(purchase_data.get("installment_first_payment_date"))

    # Calculate installment amount with interest
    if interest_rate > 0:
        # Simple interest calculation
        total_with_interest = total_amount * (1 + (interest_rate / 100))
        installment_amount = total_with_interest / total_installments
    else:
        installment_amount = total_amount / total_installments

    purchase_data["installment_installment_amount"] = installment_amount

    # Calculate how many installments should have been paid by now (for historical purchases)
    now = pd.Timestamp.now()
    payment_frequency = purchase_data.get("installment_payment_frequency", "monthly")

    if not pd.isna(first_payment_date) and first_payment_date < now:
        if payment_frequency == "monthly":
            months_elapsed = (now.year - first_payment_date.year) * 12 + (now.month - first_payment_date.month)
            # If we're past the payment day in the current month, count this month too
            if now.day >= first_payment_date.day:
                months_elapsed += 1
            paid_installments = min(months_elapsed, total_installments)
        elif payment_frequency == "weekly":
            weeks_elapsed = (now - first_payment_date).days // 7
            paid_installments = min(weeks_elapsed, total_installments)
        else:
            paid_installments = 0

        # Calculate remaining balance based on paid installments
        remaining_balance = total_amount - (paid_installments * installment_amount)
    else:
        paid_installments = 0
        remaining_balance = total_amount

    purchase_data["installment_paid_installments"] = paid_installments
    purchase_data["installment_remaining_balance"] = max(0, remaining_balance)

    # Save the installment purchase
    saved_purchase = upsert_row(purchase_data)

    logger.info(f"Created installment purchase: {saved_purchase['id']} - {total_installments} installments of {installment_amount}, {paid_installments} already paid")
    return saved_purchase

def get_installment_purchases() -> List[Dict[str, Any]]:
    """Get all installment purchases"""
    df = _load_data()
    purchases = df[df["is_installment"] == True]
    return purchases.to_dict("records")

def record_installment_payment(purchase_id: str, payment_amount: float, payment_date: Optional[str] = None) -> bool:
    """Record a payment for an installment purchase"""
    purchase = get(purchase_id)
    if not purchase or not purchase.get("is_installment"):
        logger.warning(f"Installment purchase {purchase_id} not found")
        return False

    # Update paid installments and remaining balance
    paid_installments = int(purchase.get("installment_paid_installments", 0)) + 1
    remaining_balance = float(purchase.get("installment_remaining_balance", 0)) - payment_amount

    # Update purchase
    purchase["installment_paid_installments"] = paid_installments
    purchase["installment_remaining_balance"] = max(0, remaining_balance)  # Don't go negative

    # Create payment record
    payment_record = {
        "id": str(uuid.uuid4()),
        "fecha": payment_date or datetime.now().isoformat(),
        "descripcion": f"Pago cuota {paid_installments} - {purchase.get('descripcion', '')}",
        "monto_clp": payment_amount,
        "categoria": purchase.get("categoria", "deudas"),
        "medio": purchase.get("medio", "TC"),
        "tipo": "installment_payment",
        "parent_id": purchase_id,
        "fuente": "manual",
        "estado": "categorizado"
    }

    # Save payment and update purchase
    upsert_row(payment_record)
    upsert_row(purchase)

    logger.info(f"Recorded installment payment: {payment_amount} for purchase {purchase_id} (installment {paid_installments})")
    return True

def get_upcoming_installment_payments(days_ahead: int = 30) -> List[Dict[str, Any]]:
    """Get upcoming installment payments within the specified days"""
    df = _load_data()
    purchases = df[(df["is_installment"] == True) & (df["installment_remaining_balance"] > 0)]

    upcoming_payments = []

    for _, purchase in purchases.iterrows():
        first_payment_date = purchase.get("installment_first_payment_date")
        if pd.isna(first_payment_date):
            continue

        first_date = pd.to_datetime(first_payment_date)
        paid_installments = int(purchase.get("installment_paid_installments", 0))
        total_installments = int(purchase.get("installment_total_installments", 1))
        payment_frequency = purchase.get("installment_payment_frequency", "monthly")

        # Calculate next payment date
        if payment_frequency == "monthly":
            next_payment_date = first_date + pd.DateOffset(months=paid_installments)
        elif payment_frequency == "weekly":
            next_payment_date = first_date + pd.DateOffset(weeks=paid_installments)
        else:
            next_payment_date = first_date + pd.DateOffset(months=paid_installments)

        # Check if payment is due within the specified days
        days_until_due = (next_payment_date - pd.Timestamp.now()).days

        if 0 <= days_until_due <= days_ahead and paid_installments < total_installments:
            upcoming_payments.append({
                "purchase_id": purchase["id"],
                "descripcion": purchase.get("descripcion", ""),
                "next_payment_date": next_payment_date.isoformat(),
                "days_until_due": days_until_due,
                "installment_amount": float(purchase.get("installment_installment_amount", 0)),
                "installment_number": paid_installments + 1,
                "total_installments": total_installments,
                "remaining_balance": float(purchase.get("installment_remaining_balance", 0))
            })

    return upcoming_payments

def get_installment_purchase_summary() -> Dict[str, Any]:
    """Get summary of all installment purchases"""
    df = _load_data()
    purchases = df[df["is_installment"] == True]

    total_debt = purchases["installment_remaining_balance"].sum()
    total_purchases = len(purchases)
    active_purchases = len(purchases[purchases["installment_remaining_balance"] > 0])

    # Calculate monthly payment commitment
    monthly_commitment = 0.0
    for _, purchase in purchases.iterrows():
        if purchase["installment_remaining_balance"] > 0:
            frequency = purchase.get("installment_payment_frequency", "monthly")
            if frequency == "monthly":
                monthly_commitment += float(purchase.get("installment_installment_amount", 0))

    return {
        "total_debt": float(total_debt),
        "total_purchases": total_purchases,
        "active_purchases": active_purchases,
        "monthly_commitment": monthly_commitment,
        "upcoming_payments": get_upcoming_installment_payments(7)  # Next 7 days
    }

def update_installment_purchase(purchase_id: str, updates: Dict[str, Any]) -> bool:
    """Update an installment purchase"""
    purchase = get(purchase_id)
    if not purchase or not purchase.get("is_installment"):
        logger.warning(f"Installment purchase {purchase_id} not found")
        return False

    # Update fields
    for key, value in updates.items():
        if key in SCHEMA_COLUMNS:
            purchase[key] = value

    # Recalculate installment amount if relevant fields changed
    if any(key in updates for key in ["installment_total_amount", "installment_total_installments", "installment_interest_rate"]):
        total_amount = float(purchase.get("installment_total_amount", 0))
        total_installments = int(purchase.get("installment_total_installments", 1))
        interest_rate = float(purchase.get("installment_interest_rate", 0))

        if interest_rate > 0:
            total_with_interest = total_amount * (1 + (interest_rate / 100))
            installment_amount = total_with_interest / total_installments
        else:
            installment_amount = total_amount / total_installments

        purchase["installment_installment_amount"] = installment_amount
        purchase["installment_remaining_balance"] = total_amount - (float(purchase.get("installment_paid_installments", 0)) * installment_amount)

    upsert_row(purchase)
    logger.info(f"Updated installment purchase: {purchase_id}")
    return True

def delete_installment_purchase(purchase_id: str) -> bool:
    """Delete an installment purchase"""
    purchase = get(purchase_id)
    if not purchase or not purchase.get("is_installment"):
        logger.warning(f"Installment purchase {purchase_id} not found")
        return False

    # Delete the purchase
    success = delete_row(purchase_id)

    if success:
        logger.info(f"Deleted installment purchase: {purchase_id}")

        # Optionally delete related payment records
        # This could be implemented if needed

    return success

def generate_installment_expenses():
    """Generate automatic expenses for current month installment payments only"""
    df = _load_data()
    purchases = df[(df["is_installment"] == True) & (df["installment_remaining_balance"] > 0)]

    generated_count = 0
    now = pd.Timestamp.now()

    for _, purchase in purchases.iterrows():
        first_payment_date = purchase.get("installment_first_payment_date")
        if pd.isna(first_payment_date):
            continue

        first_date = pd.to_datetime(first_payment_date)
        paid_installments = int(purchase.get("installment_paid_installments", 0))
        total_installments = int(purchase.get("installment_total_installments", 1))
        payment_frequency = purchase.get("installment_payment_frequency", "monthly")
        installment_amount = float(purchase.get("installment_installment_amount", 0))

        # Only generate expense for the current month installment
        current_installment_num = paid_installments + 1

        # Check if we still have installments to pay
        if current_installment_num > total_installments:
            continue

        # Calculate payment date for current installment
        if payment_frequency == "monthly":
            payment_date = first_date + pd.DateOffset(months=current_installment_num - 1)
        elif payment_frequency == "weekly":
            payment_date = first_date + pd.DateOffset(weeks=current_installment_num - 1)
        else:
            payment_date = first_date + pd.DateOffset(months=current_installment_num - 1)

        # Only generate if this installment is due this month (or within the next 30 days)
        if payment_date.year == now.year and payment_date.month == now.month:
            # Generate for current month
            pass
        elif (payment_date - now).days <= 30 and payment_date > now:
            # Generate for upcoming installments within 30 days
            pass
        else:
            # Skip installments that are not due soon
            continue
            # Check if expense already exists for this installment
            existing_expenses = df[
                (df["parent_id"] == purchase["id"]) &
                (df["tipo"] == "installment_expense") &
                (df["descripcion"].str.contains(f"Cuota {current_installment_num}"))
            ]

            if len(existing_expenses) == 0:
                # Generate expense for this installment
                expense_data = {
                    "id": str(uuid.uuid4()),
                    "fecha": payment_date.isoformat(),
                    "descripcion": f"Cuota {current_installment_num} - {purchase.get('descripcion', '')}",
                    "monto_clp": installment_amount,
                    "categoria": purchase.get("categoria", "deudas"),
                    "medio": purchase.get("medio", "TC"),
                    "tipo": "installment_expense",
                    "parent_id": purchase["id"],
                    "fuente": "installment_auto",
                    "estado": "categorizado",
                    "is_installment": False  # This is the actual expense, not the purchase record
                }

                upsert_row(expense_data)
                generated_count += 1

                logger.info(f"Generated current month installment expense: {expense_data['descripcion']} for purchase {purchase['id']}")

    if generated_count > 0:
        sync_excel()
        logger.info(f"Generated {generated_count} current month installment expenses")

    return generated_count

def cleanup_duplicate_installment_expenses():
    """Clean up duplicate installment expenses from previous months"""
    df = _load_data()
    now = pd.Timestamp.now()

    # Find installment expenses from previous months that shouldn't be there
    duplicate_expenses = df[
        (df["tipo"] == "installment_expense") &
        (df["fuente"] == "installment_auto") &
        (pd.to_datetime(df["fecha"]).dt.year < now.year) |
        ((pd.to_datetime(df["fecha"]).dt.year == now.year) &
         (pd.to_datetime(df["fecha"]).dt.month < now.month))
    ]

    deleted_count = 0
    for _, expense in duplicate_expenses.iterrows():
        delete_row(expense["id"])
        deleted_count += 1
        logger.info(f"Cleaned up duplicate installment expense: {expense['descripcion']}")

    if deleted_count > 0:
        sync_excel()
        logger.info(f"Cleaned up {deleted_count} duplicate installment expenses")

    return deleted_count

def record_historical_installment_payment(purchase_id: str, installment_number: int, payment_amount: float, payment_date: str) -> bool:
    """Record a historical payment for a specific installment number"""
    purchase = get(purchase_id)
    if not purchase or not purchase.get("is_installment"):
        logger.warning(f"Installment purchase {purchase_id} not found")
        return False

    paid_installments = int(purchase.get("installment_paid_installments", 0))
    total_installments = int(purchase.get("installment_total_installments", 1))
    remaining_balance = float(purchase.get("installment_remaining_balance", 0))

    # Validate installment number
    if installment_number < 1 or installment_number > total_installments:
        logger.warning(f"Invalid installment number {installment_number} for purchase {purchase_id}")
        return False

    # If this installment number is greater than currently paid installments, update accordingly
    if installment_number > paid_installments:
        # Calculate how many installments we're catching up
        installments_to_add = installment_number - paid_installments
        amount_to_subtract = payment_amount  # For this specific payment

        # Update purchase record
        purchase["installment_paid_installments"] = installment_number
        purchase["installment_remaining_balance"] = max(0, remaining_balance - amount_to_subtract)

        upsert_row(purchase)

    # Create payment record
    payment_record = {
        "id": str(uuid.uuid4()),
        "fecha": payment_date,
        "descripcion": f"Pago cuota {installment_number} - {purchase.get('descripcion', '')}",
        "monto_clp": payment_amount,
        "categoria": purchase.get("categoria", "deudas"),
        "medio": purchase.get("medio", "TC"),
        "tipo": "installment_payment",
        "parent_id": purchase_id,
        "fuente": "manual",
        "estado": "categorizado"
    }

    upsert_row(payment_record)

    logger.info(f"Recorded historical installment payment: {payment_amount} for installment {installment_number} of purchase {purchase_id}")
    return True

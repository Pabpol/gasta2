"""
Reconciliation system for matching income/refunds with shared expenses.
Implements heuristic matching based on amounts, dates, and names.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def within_tolerance(income_amount: float, expected_amount: float) -> bool:
    """
    Check if income amount is within acceptable tolerance of expected amount.
    Tolerance: $1,000 CLP or ±5% if amount > 100k CLP
    """
    diff = abs(income_amount - expected_amount)
    
    if expected_amount > 100000:  # More than 100k CLP
        tolerance = expected_amount * 0.05  # 5%
    else:
        tolerance = 1000  # $1,000 CLP
    
    return diff <= tolerance

def try_auto_match(
    income_row: Dict[str, Any], 
    pendientes: List[Dict[str, Any]], 
    prefer_name: Optional[str] = None, 
    days_window: int = 10
) -> Optional[Dict[str, Any]]:
    """
    Try to automatically match an income with pending shared expenses.
    
    Args:
        income_row: The incoming payment/refund
        pendientes: List of pending shared expenses waiting for settlement
        prefer_name: Preferred name to match against compartido_con
        days_window: Days window for date matching
    
    Returns:
        Matched expense dict or None if no match found
    """
    income_amount = float(income_row.get('monto_clp', 0))
    income_date = income_row.get('fecha')
    income_contraparte = str(income_row.get('contraparte', '')).lower().strip()
    
    if not income_amount or not income_date:
        logger.warning("Income missing amount or date")
        return None
    
    # Convert income_date to datetime if it's a string
    if isinstance(income_date, str):
        try:
            income_date = datetime.fromisoformat(income_date.replace('Z', '+00:00'))
        except:
            logger.error(f"Could not parse income date: {income_date}")
            return None
    
    best_match = None
    best_score = 0
    
    for expense in pendientes:
        score = 0
        
        # Skip if already settled
        if expense.get('settlement_status') == 'settled':
            continue
        
        # Check amount tolerance
        expected_amount = float(expense.get('monto_tercero', 0))
        if not within_tolerance(income_amount, expected_amount):
            continue
        
        # Amount match score (higher is better)
        amount_diff = abs(income_amount - expected_amount)
        if expected_amount > 0:
            amount_score = max(0, 1 - (amount_diff / expected_amount))
            score += amount_score * 40  # 40% weight for amount
        
        # Date proximity score
        expense_date = expense.get('fecha')
        if expense_date:
            if isinstance(expense_date, str):
                try:
                    expense_date = datetime.fromisoformat(expense_date.replace('Z', '+00:00'))
                except:
                    expense_date = None
            
            if expense_date:
                days_diff = abs((income_date - expense_date).days)
                if days_diff <= days_window:
                    date_score = max(0, 1 - (days_diff / days_window))
                    score += date_score * 30  # 30% weight for date
        
        # Name matching score
        compartido_con = str(expense.get('compartido_con', '')).lower().strip()
        
        if prefer_name:
            prefer_name_lower = prefer_name.lower().strip()
            if prefer_name_lower in compartido_con or compartido_con in prefer_name_lower:
                score += 20  # 20% weight for preferred name match
        
        if income_contraparte and compartido_con:
            # Check for partial name matches
            contraparte_words = income_contraparte.split()
            compartido_words = compartido_con.split()
            
            name_matches = 0
            for word1 in contraparte_words:
                for word2 in compartido_words:
                    if len(word1) > 2 and len(word2) > 2:  # Skip very short words
                        if word1 in word2 or word2 in word1:
                            name_matches += 1
            
            if name_matches > 0:
                name_score = min(1.0, name_matches / max(len(contraparte_words), len(compartido_words)))
                score += name_score * 10  # 10% weight for name similarity
        
        # Update best match if this score is higher
        if score > best_score and score >= 50:  # Minimum threshold of 50%
            best_score = score
            best_match = expense
            logger.info(f"Found potential match with score {score:.1f}: {expense.get('id')}")
    
    if best_match:
        logger.info(f"Best match found with score {best_score:.1f}")
        return best_match
    else:
        logger.info("No suitable match found")
        return None

def suggest_manual_matches(
    income_row: Dict[str, Any], 
    all_expenses: List[Dict[str, Any]], 
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Suggest possible manual matches for an income that couldn't be auto-matched.
    Returns expenses sorted by relevance.
    """
    income_amount = float(income_row.get('monto_clp', 0))
    income_date = income_row.get('fecha')
    
    suggestions = []
    
    for expense in all_expenses:
        # Only consider shared expenses
        if float(expense.get('porcentaje_compartido', 0)) <= 0:
            continue
        
        # Skip already settled
        if expense.get('settlement_status') == 'settled':
            continue
        
        suggestion = expense.copy()
        suggestion['match_score'] = 0
        suggestion['match_reasons'] = []
        
        # Amount similarity
        expected_amount = float(expense.get('monto_tercero', 0))
        if expected_amount > 0:
            if within_tolerance(income_amount, expected_amount):
                suggestion['match_score'] += 50
                suggestion['match_reasons'].append('Amount matches')
            else:
                # Partial points for similar amounts
                ratio = min(income_amount, expected_amount) / max(income_amount, expected_amount)
                if ratio > 0.7:
                    suggestion['match_score'] += 25
                    suggestion['match_reasons'].append('Similar amount')
        
        # Date proximity (within 30 days gets some points)
        if income_date and expense.get('fecha'):
            try:
                if isinstance(income_date, str):
                    income_dt = datetime.fromisoformat(income_date.replace('Z', '+00:00'))
                else:
                    income_dt = income_date
                
                expense_date = expense.get('fecha')
                if isinstance(expense_date, str):
                    expense_dt = datetime.fromisoformat(expense_date.replace('Z', '+00:00'))
                else:
                    expense_dt = expense_date
                
                days_diff = abs((income_dt - expense_dt).days)
                if days_diff <= 30:
                    proximity_score = max(0, 30 - days_diff)
                    suggestion['match_score'] += proximity_score
                    suggestion['match_reasons'].append(f'{days_diff} days apart')
            except:
                pass
        
        if suggestion['match_score'] > 0:
            suggestions.append(suggestion)
    
    # Sort by score and return top suggestions
    suggestions.sort(key=lambda x: x['match_score'], reverse=True)
    return suggestions[:limit]

def mark_as_settled(expense_id: str, income_id: str, storage_module):
    """
    Mark an expense as settled and link it with the income.
    """
    try:
        # Update expense
        expense = storage_module.get(expense_id)
        if expense:
            expense['settlement_status'] = 'settled'
            expense['settled_with'] = income_id
            expense['settled_date'] = datetime.now().isoformat()
            storage_module.upsert_row(expense)
        
        # Update income
        income = storage_module.get(income_id)
        if income:
            income['matched_expense'] = expense_id
            income['settlement_status'] = 'matched'
            storage_module.upsert_row(income)
        
        logger.info(f"Marked expense {expense_id} as settled with income {income_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error marking as settled: {e}")
        return False

def get_reconciliation_stats(storage_module) -> Dict[str, Any]:
    """
    Get reconciliation statistics.
    """
    try:
        df = storage_module.get_all_data()
        
        # Shared expenses
        shared_expenses = df[df['porcentaje_compartido'] > 0]
        pending_settlement = shared_expenses[
            shared_expenses['settlement_status'].isin(['', 'pending']) | 
            shared_expenses['settlement_status'].isna()
        ]
        settled = shared_expenses[shared_expenses['settlement_status'] == 'settled']
        
        # Income/refunds
        incomes = df[df['tipo'] == 'transfer_in']
        matched_incomes = incomes[incomes['settlement_status'] == 'matched']
        unmatched_incomes = incomes[
            incomes['settlement_status'].isin(['', 'unmatched']) | 
            incomes['settlement_status'].isna()
        ]
        
        stats = {
            'total_shared_expenses': len(shared_expenses),
            'pending_settlement': len(pending_settlement),
            'settled_expenses': len(settled),
            'pending_amount': pending_settlement['monto_tercero'].sum(),
            'settled_amount': settled['monto_tercero'].sum(),
            'total_incomes': len(incomes),
            'matched_incomes': len(matched_incomes),
            'unmatched_incomes': len(unmatched_incomes),
            'unmatched_amount': unmatched_incomes['monto_clp'].sum()
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting reconciliation stats: {e}")
        return {}

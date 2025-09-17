"""
Period Configuration Module
Handles pay period calculations based on configurable pay day
"""

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import Tuple, Dict, Any
import json
import os
from pathlib import Path

class PeriodConfig:
    """Manages pay period configuration and calculations"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or Path(__file__).parent.parent / "config" / "period_config.json"
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        default_config = {
            "pay_day": 25,  # Day of month when salary is paid
            "last_updated": datetime.now().isoformat()
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    # Ensure required keys exist
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
        except Exception:
            pass
        
        # Create config directory if it doesn't exist
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        # Save default config
        self._save_config(default_config)
        return default_config
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Could not save period config: {e}")
    
    def get_pay_day(self) -> int:
        """Get the configured pay day"""
        return self.config.get("pay_day", 25)
    
    def set_pay_day(self, day: int) -> None:
        """Set the pay day (1-31)"""
        if not 1 <= day <= 31:
            raise ValueError("Pay day must be between 1 and 31")
        
        self.config["pay_day"] = day
        self.config["last_updated"] = datetime.now().isoformat()
        self._save_config(self.config)
    
    def get_current_period(self, reference_date: datetime = None) -> Tuple[datetime, datetime]:
        """
        Get the current pay period based on the configured pay day
        
        Args:
            reference_date: Date to calculate period for (default: today)
            
        Returns:
            Tuple of (period_start, period_end) as datetime objects
        """
        if reference_date is None:
            reference_date = datetime.now()
        
        pay_day = self.get_pay_day()
        
        # If today is before this month's pay day, we're in the previous period
        current_month_pay_date = reference_date.replace(day=pay_day, hour=0, minute=0, second=0, microsecond=0)
        
        if reference_date < current_month_pay_date:
            # We're in the previous period
            period_end = current_month_pay_date - timedelta(days=1)
            period_start = (period_end.replace(day=pay_day) - relativedelta(months=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            # We're in the current period
            period_start = current_month_pay_date
            next_month_pay_date = (current_month_pay_date + relativedelta(months=1))
            period_end = next_month_pay_date - timedelta(days=1)
        
        # Set end time to end of day
        period_end = period_end.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        return period_start, period_end
    
    def get_period_info(self, reference_date: datetime = None) -> Dict[str, Any]:
        """
        Get comprehensive period information
        
        Returns:
            Dictionary with period details
        """
        period_start, period_end = self.get_current_period(reference_date)
        
        # Calculate next pay date
        next_pay_date = period_end.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        
        # Calculate days until next pay
        today = reference_date or datetime.now()
        days_until_pay = (next_pay_date.date() - today.date()).days
        
        return {
            "pay_day": self.get_pay_day(),
            "period_start": period_start,
            "period_end": period_end,
            "next_pay_date": next_pay_date,
            "days_until_pay": max(0, days_until_pay),
            "period_name": f"{period_start.strftime('%d %b')} - {period_end.strftime('%d %b')}"
        }

# Global instance
period_config = PeriodConfig()

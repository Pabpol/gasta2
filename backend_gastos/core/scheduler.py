"""
Scheduler for automatic recurring expense generation.
This module handles the periodic generation of expenses from recurring templates.
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Optional
import threading

from .storage import generate_recurring_expenses, generate_installment_expenses, get_upcoming_installment_payments, get_installment_purchase_summary

logger = logging.getLogger(__name__)

def format_currency(amount: float) -> str:
    """Format amount as Chilean Peso currency"""
    try:
        return f"${amount:,.0f}".replace(",", ".")
    except (ValueError, TypeError):
        return f"${amount}"

class RecurringExpenseScheduler:
    """Scheduler for automatic recurring expense generation"""

    def __init__(self, check_interval_minutes: int = 60):
        """
        Initialize the scheduler

        Args:
            check_interval_minutes: How often to check for due recurring expenses (default: 1 hour)
        """
        self.check_interval = check_interval_minutes * 60  # Convert to seconds
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.last_run: Optional[datetime] = None

    def start(self):
        """Start the scheduler in a background thread"""
        if self.running:
            logger.warning("Scheduler is already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()

        logger.info(f"Recurring expense scheduler started (check interval: {self.check_interval}s)")

    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Recurring expense scheduler stopped")

    def _run_scheduler(self):
        """Main scheduler loop"""
        while self.running:
            try:
                # Check if it's time to generate expenses
                now = datetime.now()

                # Generate expenses if we haven't run in the last check interval
                if (self.last_run is None or
                    (now - self.last_run).total_seconds() >= self.check_interval):

                    logger.info("Checking for due recurring expenses and installment payments...")
                    generated_count = generate_recurring_expenses()

                    if generated_count > 0:
                        logger.info(f"Generated {generated_count} recurring expenses")
                    else:
                        logger.debug("No recurring expenses due at this time")

                    # Generate installment expenses
                    installment_generated_count = generate_installment_expenses()

                    if installment_generated_count > 0:
                        logger.info(f"Generated {installment_generated_count} installment expenses")
                    else:
                        logger.debug("No installment expenses due at this time")

                    # Check for upcoming installment payments
                    self._check_installment_payment_reminders()

                    self.last_run = now

            except Exception as e:
                logger.error(f"Error in recurring expense scheduler: {e}", exc_info=True)

            # Wait before next check
            time.sleep(min(300, self.check_interval))  # Sleep for 5 minutes or check interval, whichever is smaller

    def _check_installment_payment_reminders(self):
        """Check for upcoming installment payments and log reminders"""
        try:
            # Check for upcoming payments (within 7 days)
            upcoming = get_upcoming_installment_payments(7)

            if upcoming:
                logger.info(f"📊 Found {len(upcoming)} upcoming installment payments due within 7 days")

                overdue_count = 0
                due_today_count = 0
                due_soon_count = 0

                for payment in upcoming:
                    days = payment['days_until_due']
                    amount = payment['installment_amount']
                    description = payment['descripcion']
                    installment_num = payment['installment_number']
                    total_installments = payment['total_installments']

                    if days < 0:
                        # Overdue payments - CRITICAL
                        overdue_count += 1
                        logger.warning(
                            f"🚨 OVERDUE PAYMENT: {description} - "
                            f"Installment {installment_num}/{total_installments} - "
                            f"{format_currency(amount)} - "
                            f"Overdue by {abs(days)} days"
                        )
                    elif days == 0:
                        # Due today - HIGH PRIORITY
                        due_today_count += 1
                        logger.warning(
                            f"⚠️ DUE TODAY: {description} - "
                            f"Installment {installment_num}/{total_installments} - "
                            f"{format_currency(amount)}"
                        )
                    elif days <= 3:
                        # Due within 3 days - MEDIUM PRIORITY
                        due_soon_count += 1
                        logger.info(
                            f"📅 DUE SOON: {description} - "
                            f"Installment {installment_num}/{total_installments} - "
                            f"{format_currency(amount)} - "
                            f"Due in {days} days"
                        )
                    else:
                        # Due within 7 days - LOW PRIORITY
                        logger.info(
                            f"📆 UPCOMING: {description} - "
                            f"Installment {installment_num}/{total_installments} - "
                            f"{format_currency(amount)} - "
                            f"Due in {days} days"
                        )

                # Summary log for important notifications
                if overdue_count > 0 or due_today_count > 0 or due_soon_count > 0:
                    logger.warning(
                        f"💰 PAYMENT SUMMARY: {overdue_count} overdue, "
                        f"{due_today_count} due today, {due_soon_count} due soon"
                    )

            # Check for high debt levels
            summary = get_installment_purchase_summary()

            if summary['total_debt'] > 1000000:  # More than 1M CLP debt
                logger.warning(
                    f"💰 HIGH DEBT ALERT: Total installment debt is {format_currency(summary['total_debt'])} "
                    f"across {summary['active_purchases']} purchases"
                )

            if summary['monthly_commitment'] > 500000:  # More than 500K CLP monthly
                logger.warning(
                    f"📊 HIGH MONTHLY COMMITMENT: {format_currency(summary['monthly_commitment'])} "
                    f"monthly installment payments"
                )

        except Exception as e:
            logger.error(f"Error checking installment payment reminders: {e}", exc_info=True)

    def run_once(self):
        """Run the recurring expense generation once (for manual triggering)"""
        try:
            logger.info("Manually triggering recurring expense and installment generation...")
            generated_count = generate_recurring_expenses()
            installment_generated_count = generate_installment_expenses()

            total_generated = generated_count + installment_generated_count

            if generated_count > 0:
                logger.info(f"Manually generated {generated_count} recurring expenses")
            else:
                logger.info("No recurring expenses were due")

            if installment_generated_count > 0:
                logger.info(f"Manually generated {installment_generated_count} installment expenses")
            else:
                logger.info("No installment expenses were due")

            self.last_run = datetime.now()
            return total_generated

        except Exception as e:
            logger.error(f"Error in manual expense generation: {e}", exc_info=True)
            return 0

# Global scheduler instance
scheduler = RecurringExpenseScheduler()

def start_scheduler():
    """Start the global recurring expense scheduler"""
    scheduler.start()

def stop_scheduler():
    """Stop the global recurring expense scheduler"""
    scheduler.stop()

def run_scheduler_once():
    """Run the scheduler once for manual triggering"""
    return scheduler.run_once()

if __name__ == "__main__":
    # For testing the scheduler
    logging.basicConfig(level=logging.INFO)

    print("Starting recurring expense scheduler...")
    print("Press Ctrl+C to stop")

    scheduler = RecurringExpenseScheduler(check_interval_minutes=1)  # Check every minute for testing
    scheduler.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping scheduler...")
        scheduler.stop()
        print("Scheduler stopped")
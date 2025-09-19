"""
Scheduler for automatic recurring expense generation.
This module handles the periodic generation of expenses from recurring templates.
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Optional
import threading

from .storage import generate_recurring_expenses

logger = logging.getLogger(__name__)

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

                    logger.info("Checking for due recurring expenses...")
                    generated_count = generate_recurring_expenses()

                    if generated_count > 0:
                        logger.info(f"Generated {generated_count} recurring expenses")
                    else:
                        logger.debug("No recurring expenses due at this time")

                    self.last_run = now

            except Exception as e:
                logger.error(f"Error in recurring expense scheduler: {e}", exc_info=True)

            # Wait before next check
            time.sleep(min(300, self.check_interval))  # Sleep for 5 minutes or check interval, whichever is smaller

    def run_once(self):
        """Run the recurring expense generation once (for manual triggering)"""
        try:
            logger.info("Manually triggering recurring expense generation...")
            generated_count = generate_recurring_expenses()

            if generated_count > 0:
                logger.info(f"Manually generated {generated_count} recurring expenses")
            else:
                logger.info("No recurring expenses were due")

            self.last_run = datetime.now()
            return generated_count

        except Exception as e:
            logger.error(f"Error in manual recurring expense generation: {e}", exc_info=True)
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
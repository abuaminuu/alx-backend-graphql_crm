# crm/management/commands/test_heartbeat.py
from django.core.management.base import BaseCommand
from crm.cron import log_crm_heartbeat

class Command(BaseCommand):
    help = 'Test the CRM heartbeat function'
    
    def handle(self, *args, **options):
        self.stdout.write("Testing CRM heartbeat...")
        
        success = log_crm_heartbeat()
        
        if success:
            self.stdout.write(self.style.SUCCESS("✓ Heartbeat logged successfully"))
        else:
            self.stdout.write(self.style.ERROR("✗ Heartbeat failed"))
        
        # Show log file
        try:
            with open('/tmp/crm_heartbeat_log.txt', 'r') as f:
                lines = f.readlines()
                if lines:
                    self.stdout.write("\nLast 3 log entries:")
                    for line in lines[-3:]:
                        self.stdout.write(f"  {line.strip()}")
        except FileNotFoundError:
            self.stdout.write("Log file not found")

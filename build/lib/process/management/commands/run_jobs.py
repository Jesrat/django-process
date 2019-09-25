import time
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError

from ._actions import configure_env, run_jobs, run_awaiting_tasks, finish_jobs


class Command(BaseCommand):
    help = 'Run All Jobs'

    def handle(self, *args, **options):
        configure_env()
        try:
            while True:
                time.sleep(1)
                if datetime.now().second == 0:
                    run_jobs()
                run_awaiting_tasks()
                finish_jobs()
        except KeyboardInterrupt:
            pass

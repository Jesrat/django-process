import time
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError

from ._actions import configure_env, run_jobs, run_awaiting_tasks, finish_jobs


class Command(BaseCommand):
    help = 'Run All Jobs'

    def handle(self, *args, **options):
        configure_env()
        try:
            # This var will prevent many jobs started from the same process in the 0 second
            jobs_start_unlocked = False
            while True:
                time.sleep(0.1)

                now = datetime.now()
                if now.second == 0 and jobs_start_unlocked:
                    jobs_start_unlocked = False
                    run_jobs(now)
                elif now.second != 0:
                    jobs_start_unlocked = True

                run_awaiting_tasks()
                finish_jobs()

        except KeyboardInterrupt:
            pass

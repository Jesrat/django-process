import time
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone

from ._actions import configure_env, run_jobs, run_awaiting_tasks, finish_jobs

logger = logging.getLogger('django-process')


class Command(BaseCommand):
    help = 'Run All Jobs'

    def handle(self, *args, **options):
        logger.info('django-process run_jobs started')
        configure_env()
        try:
            # This var will prevent many jobs started from the same process in the 0 second
            jobs_start_unlocked = False
            while True:
                time.sleep(0.1)

                now = timezone.now()
                if now.second == 0 and jobs_start_unlocked:
                    jobs_start_unlocked = False
                    run_jobs(now)
                elif now.second != 0:
                    jobs_start_unlocked = True

                run_awaiting_tasks()
                finish_jobs()

        except KeyboardInterrupt:
            pass

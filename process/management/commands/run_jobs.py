import time
import logging
from threading import Thread
from datetime import datetime
from django.core.management.base import BaseCommand
from process.models import Process, Job, JobTask
from django.db.models import ObjectDoesNotExist

logger = logging.getLogger('django-process')


class TaskThreaded(Thread):
    def __init__(self, obj, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.obj = obj

    def run(self):
        self.obj.dt_start = datetime.now()
        self.obj.status = JobTask.initialized
        self.obj.save()
        try:
            response = {}
            exec(self.obj.task.code, globals(), response)
            # if no observations returned always save a string in attribute
            self.obj.observations = response.get('observations', '')
            if response.get('error'):
                raise Exception('task response with error')
            self.obj.status = JobTask.finished
        except Exception as e:
            self.obj.observations += f'exception when running task {e}'
            self.obj.status = JobTask.error
            self.obj.job.status = Job.error
            logger.error(f'task {self.obj} finished with error {self.obj.observations}')
            self.obj.job.save()

        self.obj.dt_end = datetime.now()
        self.obj.save()


def run_jobs():
    """
    Start Job and it's tasks
    """
    for pr in Process.objects.filter(is_active=True):
        must_run = pr.must_run()
        logger.debug(f'process {pr} must run {must_run}')
        if must_run:
            try:
                last_job = Job.objects.filter(process=pr).latest('id')
            except ObjectDoesNotExist:
                # job for the process have never run before set an empty job instance
                # and set status to finished otherwise the overlap validation will avoid
                # a new instance to start
                last_job = Job()
                last_job.status = Job.finished

            if not pr.run_if_err and last_job.status == Job.error:
                logger.error(f'job {pr} will not run because previous job status its error')
                return

            if not pr.run_overlap and last_job.status == Job.initialized:
                logger.error(f'job {pr} will not run because previous job has not finished '
                             f'and this job does not allow overlap')
                return

            job, tasks = Job.create(pr)
            for instance in tasks:
                if instance.task.parents.count() == 0:
                    TaskThreaded(instance).start()


def run_awaiting_tasks():
    """
    Run all pending tasks if their status is pending and their parent tasks are finished
    """
    for task in JobTask.objects.filter(status__in=JobTask.run_status):
        if task.ready_to_run:
            TaskThreaded(task).start()


def finish_jobs():
    """
    select all initialized(unfinished) jobs if all it's tasks are finished then finish it self
    """
    def custom_all(plist):
        """
        all() builtin function will return True if an empty list is passed
        :param plist:
        """
        if not plist:
            return False
        return all(plist)
    jobs = Job.objects.filter(status__in=Job.unfinished).prefetch_related()
    for job in jobs:
        if custom_all([i.status in JobTask.ok_status for i in job.tasks.all()]):
            job.status = Job.finished
            job.dt_end = datetime.now()
            job.save()


class Command(BaseCommand):
    help = 'Run All Jobs'

    def handle(self, *args, **options):
        while True:
            time.sleep(1)
            if datetime.now().second == 0:
                run_jobs()
            run_awaiting_tasks()
            finish_jobs()

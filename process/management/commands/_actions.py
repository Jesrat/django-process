import os
import json
import logging
import importlib
from django.conf import settings
from django.db.models import ObjectDoesNotExist
from django.utils import timezone

from process.models import Process, Job, JobTask
from ._task import TaskThreaded

logger = logging.getLogger('django-process')


def configure_env():
    # noinspection PyUnresolvedReferences
    module = importlib.util.find_spec('process')
    mod_location = os.path.dirname(module.origin)
    env_file = os.path.join(mod_location, 'env_conf.json')
    environment = {
        'project_path': settings.BASE_DIR,
        'project_settings': os.environ.get('DJANGO_SETTINGS_MODULE')
    }
    try:
        with open(env_file, 'w') as f:
            json.dump(environment, f)
    except Exception as e:
        logger.exception(f'django-process environment could not be configured due to =>\n{e}')
        logger.debug('configuring to current working directory instead')
        with open(os.path.join(os.getcwd(), 'env_conf.json'), 'w') as f:
            json.dump(environment, f)


def run_jobs(date):
    """
    Start Job and it's tasks
    """
    for pr in Process.objects.filter(is_active=True):
        must_run = pr.must_run(date)
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
                continue

            if not pr.run_overlap and last_job.status == Job.initialized:
                logger.error(f'job {pr} will not run because previous job has not finished '
                             f'and this job does not allow overlap')
                continue

            __, __ = Job.create(pr)


def run_awaiting_tasks():
    """
    Run all pending tasks if their status is pending and their parent tasks are finished
    """
    for task in JobTask.objects.filter(status__in=JobTask.run_status):
        if task.ready_to_run:
            # mark task instance as initialized
            task.set_status(JobTask.initialized)
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
            job.dt_end = timezone.now()
            job.save()

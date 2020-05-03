import os
import sys
import logging
import subprocess
from threading import Thread
from django.utils import timezone

from process.conf import get_conf
from process.models import Job, JobTask
logger = logging.getLogger('django-process')


class TaskThreaded(Thread):
    def __init__(self, obj, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.obj = obj

    def run(self):
        try:
            try:
                # get interpreter the default is the one used to run django
                if not self.obj.task.interpreter:
                    cmd = [sys.executable]
                else:
                    cmd = self.obj.task.interpreter.split()

                # noinspection SpellCheckingInspection
                if self.obj.task.code.file.__class__.__name__ == 'S3Boto3StorageFile':
                    if not os.path.isdir('/tmp/dj_process_tasks'):
                        os.makedirs('/tmp/dj_process_tasks')
                    file_path = os.path.join('/tmp', self.obj.task.code.file.name)
                    if not os.path.isfile(file_path):
                        with open(file_path, 'wb') as code:
                            code.write(self.obj.task.code.file.read())
                else:
                    file_path = self.obj.task.code.path

                # append task file path and arguments if they exists
                cmd.append(file_path)
                if self.obj.task.arguments:
                    cmd += self.obj.task.arguments.split()

                logger.info(f'command to execute {cmd}')

                p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = p.communicate()
                # return code must be 0 for success
                self.obj.observations = stdout.decode('utf-8')
                if p.returncode:
                    raise Exception(stderr.decode('utf-8'))

                self.obj.set_status(JobTask.finished)

            except Exception as e:
                # if error then send to logger and also mark task and it's job as error
                self.obj.observations += f"\nexception when running task {e}"
                self.obj.set_status(JobTask.error)
                self.obj.job.status = Job.error
                logger.error(f'task {self.obj} finished with error {self.obj.observations}')
                self.obj.job.save()
                # if there is a custom handler send task id and exception to it
                error_handler_func = get_conf('task__error_handler')
                logger.info(f'sending info to handler {error_handler_func.__name__}')
                error_handler_func(self.obj, e)

            self.obj.dt_end = timezone.now()
            self.obj.save()
        except Exception as e:
            logger.exception(f'error {e} when processing task {self.obj}')

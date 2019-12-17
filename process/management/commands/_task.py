import sys
import logging
import subprocess
from datetime import datetime
from threading import Thread

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

                # append task file path and arguments if they exists
                cmd.append(self.obj.task.code.path)
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
                get_conf('task__error_handler')(self.obj, e)

            self.obj.dt_end = datetime.now()
            self.obj.save()
        except Exception as e:
            logger.exception(f'error {e} when processing task {self.obj}')

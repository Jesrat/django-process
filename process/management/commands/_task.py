import sys
import logging
import subprocess
from datetime import datetime
from threading import Thread

from process.models import Job, JobTask
logger = logging.getLogger('django-process')


class TaskThreaded(Thread):
    def __init__(self, obj, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.obj = obj

    def run(self):
        try:
            try:
                if not self.obj.task.interpreter:
                    cmd = [sys.executable]
                else:
                    cmd = self.obj.task.interpreter.split()

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
                # if error send to logger and also mark task and it's job as error
                self.obj.observations += f"\nexception when running task {e}"
                self.obj.set_status(JobTask.error)
                self.obj.job.status = Job.error
                logger.error(f'task {self.obj} finished with error {self.obj.observations}')
                self.obj.job.save()

            self.obj.dt_end = datetime.now()
            self.obj.save()
        except Exception as e:
            logger.exception(f'error {e} when processing task {self.obj}')

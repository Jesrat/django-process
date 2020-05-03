import re
import os
import logging
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, FileExtensionValidator
from django.db import models, transaction, DatabaseError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


from process.exceptions import ProcessException
logger = logging.getLogger('django-process')


# noinspection SpellCheckingInspection
class Process(models.Model):
    """
    The Process class this will define the execute options for the process
    """
    name = models.CharField(_("name"), max_length=20, unique=True)
    description = models.CharField(_("description"), max_length=200, unique=True)
    is_active = models.BooleanField(_("active"), default=True)
    run_if_err = models.BooleanField(_("run again if previously execution status is error"), default=False)
    run_overlap = models.BooleanField(_("run if previous still is executing"), default=False)
    minute = models.CharField(_("minute"), max_length=50)
    hour = models.CharField(_("hour"), max_length=50)
    day_of_month = models.CharField(_("day of month"), max_length=50)
    month = models.CharField(_("month"), max_length=50)
    day_of_week = models.CharField(_("day of week"), max_length=50)
    objects = models.Manager()

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'pr_processes'
        verbose_name = _('process')
        verbose_name_plural = _('processes')
        ordering = ['-id']
        permissions = (
            ("view_processes", "Can view processes"),
            ("manage_processes", "Can manage processes"),
        )

    def clean(self):
        super().clean()
        _ = self._expanded(self.minute, 'minute')
        _ = self._expanded(self.hour, 'hour')
        _ = self._expanded(self.day_of_month, 'day_of_month')
        _ = self._expanded(self.month, 'month')
        _ = self._expanded(self.day_of_week, 'day_of_week')

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    @staticmethod
    def _expanded(var, type_val):
        """
        gets an crontab like string and expands all items example
        '1,2,3,7,4-9' will be expanded to '1,2,3,4,5,6,7,8,9'
        :param var:
        :return: string of unique items expanded
        """
        def item_validator(item):
            val_range = [0, 0]
            if type_val == 'minute':
                val_range = [0, 59]
            if type_val == 'hour':
                val_range = [0, 23]
            elif type_val == 'day_of_month':
                val_range = [1, 31]
            elif type_val == 'month':
                val_range = [1, 12]
            elif type_val == 'day_of_week':
                val_range = [0, 6]

            if not val_range[0] <= int(item) <= val_range[1]:
                raise ValueError
            return int(item)
            
        # if content it is a star it is ok means all
        if var == '*':
            return []

        n3 = []
        ranges = []
        # separate ranged values and not ranged values to be validated
        for i in var.split(','):
            if i.find('-') > -1 and len(re.findall('-', i)) == 1:
                ranges.append(i.split('-'))
            elif i.find('-') == -1:
                try:
                    n3.append(item_validator(i))
                except ValueError:
                    raise ValidationError(_(f'{i} is not a valid value'))
            else:
                raise ValidationError(_(f'{i} is not a valid range value'))

        # the set now contents individual values
        n3 = set(n3)

        # review range values must have only one hypen second value must be greater than first
        for i in ranges:
            try:
                if item_validator(i[0]) >= item_validator(i[1]):
                    raise ValidationError(_(f'{i[1]} must be greater than {i[0]}'))
            except ValueError:
                raise ValidationError(_(f"{'-'.join(i)} is not a valid range value"))

            for x in range(int(i[0]), int(i[1]) + 1):
                n3.add(x)
        
        # the set is complete
        return n3

    def _minute(self):
        return any([self.minute == '*', self.current_time.minute in self._expanded(self.minute, 'minute')])

    def _hour(self):
        return any([self.hour == '*', self.current_time.hour in self._expanded(self.hour, 'hour')])

    def _day_of_month(self):
        return any([self.day_of_month == '*',
                    self.current_time.day in self._expanded(self.day_of_month, 'day_of_month')])

    def _month(self):
        return any([self.month == '*', self.current_time.month in self._expanded(self.month, 'month')])

    def _day_of_week(self):
        return any([self.day_of_week == '*',
                    self.current_time.isoweekday() in self._expanded(self.day_of_week, 'day_of_week')])

    def must_run(self, date):
        """
        This method is used to check if the Job should be executed by time
        :return: Boolean
        """
        self.current_time = date
        return all([self._minute(), self._hour(), self._day_of_month(), self._month(), self._day_of_week()])


# noinspection SpellCheckingInspection
class Task(models.Model):
    """
    Task class contains the code that will be executed in each task of the process
    """
    offset_validator = RegexValidator(
        r'^-?[0-9]{0,3}%$',
        _('wrong value for offset it mus be positive 1% or negative -1% max 3 digits')
    )
    process = models.ForeignKey(Process, on_delete=models.CASCADE, verbose_name=_("process"), related_name='tasks')
    name = models.CharField(_("name"), max_length=20, unique=True)
    description = models.CharField(_("description"), max_length=200, unique=True)
    is_active = models.BooleanField(_("active"), default=True)
    level = models.PositiveIntegerField(_("diagram level"), default=0)
    offset = models.CharField(_("diagram offset"), max_length=5, default='0%', validators=[offset_validator])
    interpreter = models.CharField(_("interpreter"), max_length=50, blank=True, null=True)
    arguments = models.CharField(_("arguments"), max_length=100, blank=True, null=True)
    code = models.FileField(
        _("code file"),
        upload_to='dj_process_tasks/',
        validators=[FileExtensionValidator(allowed_extensions=['py', 'sh', 'pl'])]
    )
    objects = models.Manager()

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'pr_tasks'
        verbose_name = _('task')
        verbose_name_plural = _('tasks')
        ordering = ['-id']
        permissions = (
            ("view_tasks", "Can view tasks"),
            ("manage_tasks", "Can manage tasks"),
        )

    @property
    def file_extension(self):
        name, extension = os.path.splitext(self.code.name)
        return extension.lstrip('.')


# noinspection SpellCheckingInspection
class TaskDependence(models.Model):
    """
    Identifies the relationship between tasks
    """
    parent = models.ForeignKey(Task, on_delete=models.CASCADE, verbose_name=_("parent task"), related_name='childs')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, verbose_name=_("child task"), related_name='parents')
    objects = models.Manager()

    def __str__(self):
        return f'{self.parent.name}->{self.task.name}'

    class Meta:
        db_table = 'pr_task_dependencies'
        verbose_name = _('task dependence')
        verbose_name_plural = _('task dependencies')
        unique_together = ('parent', 'task')
        ordering = ['-id']
        permissions = (
            ("view_tasks_dependencies", "Can view tasks dependencies"),
        )

    def clean(self):
        super().clean()

        def parent_recursive(task, parent):
            if parent == task:
                raise ValidationError(_('cyclic relation detected'))
            for p in parent.parents.all():
                parent_recursive(task, p.parent)

        parent_recursive(self.task, self.parent)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


# noinspection SpellCheckingInspection
class Job(models.Model):
    """
    A Job is an instance of a Process that has been executed
    """
    initialized = 'initialized'
    finished = 'finished'
    cancelled = 'cancelled'
    error = 'error'
    cancelable = [initialized, error]
    unfinished = [initialized, error]
    status_choices = (
        (initialized, 'initialized'),
        (finished, 'finished'),
        (cancelled, 'cancelled'),
        (error, 'error'),
    )
    process = models.ForeignKey(
        Process,
        on_delete=models.CASCADE,
        verbose_name=_("process"),
        related_name='jobs'
    )
    status = models.CharField(_("status"), db_index=True, max_length=20, choices=status_choices, default=initialized)
    dt_start = models.DateTimeField(_("start date"), blank=True, null=True, auto_now_add=True)
    dt_end = models.DateTimeField(_("end date"), blank=True, null=True)
    observations = models.CharField(_("observations"), max_length=500, blank=True, null=True)
    objects = models.Manager()

    def __str__(self):
        return f'{self.process.name} [{self.dt_start}][{self.status}]'

    class Meta:
        db_table = 'pr_jobs'
        verbose_name = _('job')
        verbose_name_plural = _('jobs')
        ordering = ['-id']
        permissions = (
            ("view_jobs", "Can view job executions"),
            ("run_jobs", "Can run job"),
            ("cancel_jobs", "Can cancel job"),
        )

    @classmethod
    def create(cls, process, *args, **kwargs):
        """
        this method creates a job-process instance and all its tasks, however if the job its created as finished it will
        not create any task, example the time has come for start a job but a previous instance is still running and the
        process its configured for not overlap the new instance will be created as finished
        """
        job = cls(process=process, *args, **kwargs)
        job.save()
        ret_tasks = []
        if job.status != 'finished':
            tasks = Task.objects.filter(is_active=True, process=process)
            ret_tasks = [JobTask.create(job, t) for t in tasks]
        return job, ret_tasks

    def cancel(self):
        try:
            if self.status not in Job.cancelable:
                raise ProcessException('job status is not initialized')
            with transaction.atomic():
                self.status = Job.cancelled
                # noinspection PyUnresolvedReferences
                self.tasks.filter(status__in=JobTask.can_cancel).update(status=JobTask.cancelled)
                self.save()
        except DatabaseError as e:
            raise ProcessException(e)


# noinspection SpellCheckingInspection
class JobTask(models.Model):
    """
    A JobTask its an instance of a Task that has been executed ant its related to the Job Instance
    """
    initialized = 'initialized'
    awaiting = 'awaiting'
    reopened = 'reopened'
    retry = 'retry'
    finished = 'finished'
    cancelled = 'cancelled'
    forced = 'forced'
    error = 'error'

    can_force = [error]
    can_retry = [error]
    can_reopen = [finished, cancelled, forced]
    can_cancel = [awaiting, error]

    run_status = [awaiting, reopened, retry]
    ok_status = [finished, cancelled, forced]

    trunc_end_dt = [initialized, awaiting, reopened, retry]
    set_end_dt = [finished, cancelled, forced, error]

    status_choices = (
        (awaiting, 'awaiting'),
        (initialized, 'initialized'),
        (finished, 'finished'),
        (cancelled, 'cancelled'),
        (reopened, 'reopened'),
        (forced, 'forced'),
        (retry, 'retry'),
        (error, 'error'),
    )

    # action, requirements, status
    management = (
        ('Force', can_force, forced),
        ('Retry', can_retry, retry),
        ('Reopen', can_reopen, reopened),
        ('Cancel', can_cancel, cancelled),
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        verbose_name=_("job"),
        related_name='tasks'
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        verbose_name=_("task"),
        related_name='logs'
    )
    status = models.CharField(_("status"), db_index=True, max_length=20, choices=status_choices, default=awaiting)
    dt_created = models.DateTimeField(_("created date"), blank=True, null=True, auto_now_add=True)
    dt_start = models.DateTimeField(_("start date"), blank=True, null=True)
    dt_end = models.DateTimeField(_("end date"), blank=True, null=True)
    observations = models.TextField(_("observations"), blank=True, null=True)
    objects = models.Manager()

    def __str__(self):
        return f'{self.job}[{self.task.name}][{self.status}]'

    class Meta:
        db_table = 'pr_job_tasks'
        verbose_name = _('task instance')
        verbose_name_plural = _('task instances')
        ordering = ['-id']
        permissions = (
            ("view_job_tasks", "Can view tasks executions"),
            ("manage_job_tasks", "Can manage tasks executions"),
        )

    @property
    def title(self):
        return f'{self.status}<br>start: {self.dt_start}<br> end: {self.dt_end}'

    @property
    def info(self):
        if self.status == JobTask.error:
            return f'{self.observations}'
        elif self.status == JobTask.awaiting:
            parents = ', '.join([p.task.name for p in self.get_parents() if p.status != 'finished'])
            return f'waiting for parent(s) {parents}'
        else:
            return self.task.description

    @property
    def ready_to_run(self):
        return all([p.status in JobTask.ok_status for p in self.get_parents()])

    @classmethod
    def create(cls, job, task):
        task = cls(job=job, task=task)
        task.save()
        return task

    def get_childs(self):
        return JobTask.objects.filter(
            job=self.job,
            task__in=TaskDependence.objects.filter(parent=self.task).values('task')
        )

    def get_parents(self):
        return JobTask.objects.filter(
            job=self.job,
            task__in=TaskDependence.objects.filter(task=self.task).values('parent')
        )

    def reopen(self, main=None):
        if main and self.status not in JobTask.can_reopen:
            raise ProcessException(_(f"can't reopen current status not valid"))

        for child in self.get_childs():
            child.reopen()

        self.set_status(JobTask.reopened if main else JobTask.awaiting)

    def set_status(self, status):
        # check available status
        if status not in [i[0] for i in JobTask.status_choices]:
            raise ProcessException(_(f'status requested {status} not in status choices'))
        
        # check if new status is available for current status
        if status == JobTask.cancelled and self.status not in JobTask.can_cancel:
            raise ProcessException(_(f"can't cancel current status not valid"))
        elif status == JobTask.retry and self.status not in JobTask.can_retry:
            raise ProcessException(_(f"can't retry current status not valid"))
        elif status == JobTask.forced and self.status not in JobTask.can_force:
            raise ProcessException(_(f"can't retry current status not valid"))

        # if it will run then trunc observations
        if status in JobTask.run_status:
            self.observations = ''
            if self.job.status in [Job.error, Job.finished]:
                self.job.status = Job.initialized
                self.job.save()

        # DT_START
        if status == JobTask.initialized:
            self.dt_start = timezone.now()
            self.observations = ''

        # DT_END trunc or set
        if status in JobTask.trunc_end_dt:
            self.dt_end = None
        elif status in JobTask.set_end_dt:
            self.dt_end = timezone.now()

        self.status = status
        self.save()

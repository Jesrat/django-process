from django.db import models
from datetime import datetime
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


class Process(models.Model):
    """
    The Process class this will define the execute options for the process
    """
    name = models.CharField(_("name"), max_length=20, unique=True)
    description = models.CharField(_("description"), max_length=200, unique=True)
    is_active = models.BooleanField(_("active"), default=True)
    run_if_err = models.BooleanField(_("run again if previously result is error"), default=False)
    run_overlap = models.BooleanField(_("run if previous still is executing"), default=False)
    minute = models.CharField(_("minute"), max_length=50)
    hour = models.CharField(_("hour"), max_length=50)
    day_of_month = models.CharField(_("day_of_month"), max_length=50)
    month = models.CharField(_("month"), max_length=50)
    day_of_week = models.CharField(_("day_of_week"), max_length=50)
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

    @staticmethod
    def _expanded(var):
        """
        gets an crontab like string and expands all items example
        '1,2,3,7,4-9' will be expanded to '1,2,3,4,5,6,7,8,9'
        :param var:
        :return: string of unique items expanded
        """
        if var == '*':
            return []
        n = var.split(',')
        n2 = [i.split('-') for i in n if i.find('-') > -1]
        n3 = set([int(i) for i in n if i.find('-') == -1])
        for i in n2:
            for x in range(int(i[0]), int(i[1]) + 1):
                n3.add(x)
        return n3

    def _minute(self):
        return any([self.minute == '*', self.current_time.minute in self._expanded(self.minute)])

    def _hour(self):
        return any([self.hour == '*', self.current_time.hour in self._expanded(self.hour)])

    def _day_of_month(self):
        return any([self.day_of_month == '*', self.current_time.day in self._expanded(self.day_of_month)])

    def _month(self):
        return any([self.month == '*', self.current_time.month in self._expanded(self.month)])

    def _day_of_week(self):
        return any([self.day_of_week == '*', self.current_time.weekday() in self._expanded(self.day_of_week)])

    def must_run(self):
        """
        This method is used to check if the Job should be executed by time
        :return: Boolean
        """
        self.current_time = datetime.now()
        return all([self._minute(), self._hour(), self._day_of_month(), self._month(), self._day_of_week()])


class Task(models.Model):
    """
    Task class contains the code that will be executed in each task of the process
    """
    offset_validator = RegexValidator(
        r'^-?[0-9]{0,3}%$',
        _('wrong value for offset it mus be positive 1% or negative -1% max 3 digits')
    )
    process = models.ForeignKey(Process, on_delete=models.CASCADE, verbose_name=_("tasks"), related_name='tasks')
    name = models.CharField(_("name"), max_length=20, unique=True)
    description = models.CharField(_("description"), max_length=200, unique=True)
    is_active = models.BooleanField(_("active"), default=True)
    level = models.PositiveIntegerField(_("diagram level"), default=0)
    offset = models.CharField(_("diagram offset"), max_length=5, default='0%', validators=[offset_validator])
    log_file = models.CharField(_("log file"), max_length=20)
    code = models.TextField(_("code"))
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


class TaskDependence(models.Model):
    """
    Identifies the relationship between tasks
    """
    task = models.ForeignKey(Task, on_delete=models.CASCADE, verbose_name=_("child task"), related_name='parents')
    parent = models.ForeignKey(Task, on_delete=models.CASCADE, verbose_name=_("parent task"), related_name='childs')
    objects = models.Manager()

    def __str__(self):
        return f'{self.parent.name}->{self.task.name}'

    class Meta:
        db_table = 'pr_task_dependencies'
        verbose_name = _('task_dependence')
        verbose_name_plural = _('task_dependencies')
        ordering = ['-id']
        permissions = (
            ("view_tasks_dependencies", "Can view tasks dependencies"),
        )


class Job(models.Model):
    """
    A Job is an instance of a Process that has been executed
    """
    initialized = 'initialized'
    finished = 'finished'
    cancelled = 'cancelled'
    error = 'error'
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
        verbose_name=_("process logs"),
        related_name='jobs'
    )
    status = models.CharField(_("status"), max_length=20, choices=status_choices, default=initialized)
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

    run_status = [awaiting, reopened, retry]
    ok_status = [finished, cancelled, forced]

    status_color = {
        'default': '#41c0a4',
        initialized: '#419dc0',
        awaiting: 'gray',
        reopened: '#41c0a4',
        retry: '#41c0a4',
        finished: '#abd734',
        cancelled: '#d76034',
        forced: '#d734ab',
        error: 'red',
    }

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
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        verbose_name=_("job tasks logs"),
        related_name='tasks'
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        verbose_name=_("tasks logs"),
        related_name='logs'
    )
    status = models.CharField(_("status"), max_length=20, choices=status_choices, default=awaiting)
    dt_created = models.DateTimeField(_("created date"), blank=True, null=True, auto_now_add=True)
    dt_start = models.DateTimeField(_("start date"), blank=True, null=True)
    dt_end = models.DateTimeField(_("end date"), blank=True, null=True)
    observations = models.CharField(_("observations"), max_length=500, blank=True, null=True)
    objects = models.Manager()

    def __str__(self):
        return f'{self.job}[{self.task.name}][{self.status}]'

    class Meta:
        db_table = 'pr_job_tasks'
        verbose_name = _('task')
        verbose_name_plural = _('tasks')
        ordering = ['-id']
        permissions = (
            ("view_job_tasks", "Can view tasks executions"),
        )

    @property
    def info(self):
        if self.status == JobTask.error:
            return f'{self.dt_start} - </br>{self.observations}'
        elif self.status == JobTask.awaiting:
            parents = ', '.join([p.task.name for p in self.get_parents()])
            return f'waiting for parents {parents}'
        else:
            return f'{self.dt_start} - {self.dt_end}'

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

    @property
    def ready_to_run(self):
        return all([p.status in JobTask.ok_status for p in self.get_parents()])

    def reopen(self, main=None):
        for child in self.get_childs():
            child.reopen()
        self.status = JobTask.reopened if main else JobTask.awaiting
        self.save()

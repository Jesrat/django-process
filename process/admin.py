from .exceptions import ProcessException
from .forms import JobForm, JobTaskForm, TaskForm
from .models import Job, JobTask, Process, Task, TaskDependence
from django.contrib import admin, messages
from django.utils.translation import ngettext
from django.utils.translation import gettext_lazy as _


# Register your models here.
@admin.register(Process)
class ProcessAdmin(admin.ModelAdmin):
    actions = ['run_on_demand']
    list_display = ('__str__', 'description', 'is_active', 'recurrence')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')

    # noinspection PyMethodMayBeStatic
    def recurrence(self, process):
        return '|'.join([process.minute, process.hour, process.day_of_month, process.month, process.day_of_week])
    recurrence.short_description = 'recurrence'

    def run_on_demand(self, request, queryset):
        for process in queryset:
            __, __ = Job.create(process)
        self.message_user(request, ngettext(
            '%d process was successfully started.',
            '%d processes were successfully started.',
            len(queryset),
        ) % len(queryset), messages.SUCCESS)
    run_on_demand.short_description = _('run on demand')


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    form = TaskForm
    list_display = ('__str__', 'is_active', 'process')

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('process',)
        return self.readonly_fields


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    form = JobForm
    actions = ['cancel']
    list_display = ('__str__', 'dt_start', 'dt_end', 'observations')
    list_filter = ('status',)
    change_form_template = 'process/admin_change_job.html'

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status not in Job.cancelable:
            return 'process', 'status', 'dt_start', 'dt_end', 'observations'
        return 'process', 'dt_start', 'dt_end', 'observations'

    def get_queryset(self, request):
        qs = Job.objects.all().prefetch_related('process')
        # TODO: this should be handled by some parameter to the ChangeList.
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    # noinspection PyMethodMayBeStatic, PyUnusedLocal
    def has_add_permission(self, request):
        return False

    def cancel(self, request, queryset):
        # check cancelable
        not_cancelable = [j for j in queryset if j.status not in Job.cancelable]
        if not_cancelable:
            self.message_user(
                request,
                ngettext(
                    'following job is not in cancelable status: %(job)s',
                    'following jobs are not in cancelable status: %(job)s',
                    len(not_cancelable)
                ) % {'job': ', '.join([str(job) for job in not_cancelable])},
                messages.ERROR
            )
            return
        # attempt to cancel
        try:
            for job in queryset:
                job.cancel()
        except ProcessException as e:
            self.message_user(_('there was an exception when cancelling jobs %s') % e, messages.ERROR)
            return
        # success
        self.message_user(request, ngettext(
            '%d job was successfully canceled.',
            '%d jobs were successfully canceled.',
            len(queryset),
        ) % len(queryset), messages.SUCCESS)
    cancel.short_description = _('cancel')


@admin.register(JobTask)
class JobTaskAdmin(admin.ModelAdmin):
    form = JobTaskForm
    list_display = ('__str__', 'dt_start', 'dt_end', 'observations')

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('job', 'task', 'dt_start', 'dt_end', 'observations')
        return self.readonly_fields

    def get_queryset(self, request):
        qs = JobTask.objects.all().select_related('job', 'task', 'task__process', 'job__process')
        # TODO: this should be handled by some parameter to the ChangeList.
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    # noinspection PyMethodMayBeStatic, PyUnusedLocal
    def has_add_permission(self, request):
        return False

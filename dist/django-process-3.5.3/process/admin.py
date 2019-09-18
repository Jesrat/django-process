from django.contrib import admin
from .models import Process, Task, TaskDependence, Job, JobTask


# Register your models here.
@admin.register(Process)
class ProcessAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'is_active', 'minute', 'hour', 'day_of_month', 'month', 'day_of_week')


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'is_active', 'process')


@admin.register(TaskDependence)
class TaskDependenceAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'task', 'parent')


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'dt_start', 'dt_end', 'observations')


@admin.register(JobTask)
class JobTaskAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'dt_start', 'dt_end', 'observations')

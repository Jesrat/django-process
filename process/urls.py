from django.conf.urls import url
from process.models import Job, Process
from .views import process, task, job, jobtask, diagram

urlpatterns = [
    # Processes
    url(r'^processes/$', process.ProcessListView.as_view(), name='process-processes'),
    url(r'^processes/add/$', process.ProcessCreateView.as_view(), name='process-processes-add'),
    url(r'^processes/(?P<pk>[0-9]+)/$', process.ProcessUpdateView.as_view(), name='process-processes-update'),
    url(r'^processes/(?P<pk>[0-9]+)/delete/$', process.ProcessDeleteView.as_view(), name='process-processes-delete'),
    url(r'^processes/(?P<pk>[0-9]+)/diagram/$', diagram.DiagramView.as_view(model=Process),
        name='process-process-diagram'),
    # Tasks
    url(r'^tasks/$', task.TaskListView.as_view(), name='process-tasks'),
    url(r'^tasks/add/$', task.TaskCreateView.as_view(), name='process-tasks-add'),
    url(r'^tasks/(?P<pk>[0-9]+)/$', task.TaskUpdateView.as_view(), name='process-tasks-update'),
    url(r'^tasks/(?P<pk>[0-9]+)/delete/$', task.TaskDeleteView.as_view(), name='process-tasks-delete'),
    # Jobs
    url(r'^jobs/$', job.JobListView.as_view(), name='process-jobs'),
    url(r'^jobs/(?P<pk>[0-9]+)/delete/$', job.JobDeleteView.as_view(), name='process-jobs-delete'),
    url(r'^jobs/(?P<pk>[0-9]+)/diagram/$', diagram.DiagramView.as_view(model=Job), name='process-job-diagram'),
    # JobTasks
    url(r'^job-tasks/$', jobtask.JobTaskListView.as_view(), name='process-job-tasks'),
]

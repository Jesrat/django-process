from django.conf.urls import url
from process.models import Job, Process
from .views import ProcessListView, JobListView, DiagramView

urlpatterns = [
    url(r'^jobs/$', JobListView.as_view(), name='process-jobs'),
    url(r'^jobs/(?P<pk>[0-9]+)/diagram/$', DiagramView.as_view(model=Job), name='process-job-diagram'),
    url(r'^processes/$', ProcessListView.as_view(), name='process-processes'),
    url(r'^processes/(?P<pk>[0-9]+)/diagram/$', DiagramView.as_view(model=Process), name='process-process-diagram'),
]

import logging
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from process.conf import get_conf
from .generic_views import (
    View,
    ProcessSecurity,
    ProcessGenericListView,
    ProcessGenericDeleteView
)
from process.models import JobTask

logger = logging.getLogger('django-process')


class JobTaskDeleteView(ProcessGenericDeleteView):
    model = JobTask
    success_url = get_conf('views__jobtask__delete__success_url')
    success_message = get_conf('views__jobtask__delete__success_message')
    permissions = get_conf('views__jobtask__delete__permissions')


class JobTaskListView(ProcessGenericListView):
    model = JobTask
    title = 'JobTasks'
    filters = get_conf('views__jobtask__list__url_allow_filters')
    permissions = get_conf('views__jobtask__list__permissions')

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, args, kwargs)

    def post(self, request, *args, **kwargs):
        request = JobTaskManagementView.as_view()(request)
        return self.get(request, *args, **kwargs)


class JobTaskManagementView(ProcessSecurity, View):
    permissions = get_conf('views__jobtask__management__permissions')

    def post(self, request, *args, **kwargs):
        try:
            logger.debug(f'cancel job i got post request=> {self.request.POST}')
            task = get_object_or_404(JobTask, id=self.request.POST['task'])
            action = self.request.POST['action']
            if action == JobTask.reopened:
                task.reopen(main=True)
            else:
                task.set_status(action)

            messages.success(request, get_conf('views__jobtask__management__success_message').format(action=action))
        except Exception as e:
            messages.error(request, _(f'{e}'))
        finally:
            return request

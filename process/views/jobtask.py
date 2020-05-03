import logging
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from process.conf import get_conf
from .generic_views import (
    ProcessSecurity,
    ProcessGenericListView,
    ProcessGenericDeleteView
)
from process.models import JobTask

logger = logging.getLogger('django-process')


# noinspection SpellCheckingInspection
class JobTaskDeleteView(ProcessGenericDeleteView):
    model = JobTask
    success_url = get_conf('views__jobtask__delete__success_url')
    success_message = get_conf('views__jobtask__delete__success_message')
    permissions = get_conf('views__jobtask__delete__permissions')


# noinspection SpellCheckingInspection
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
        # noinspection PyTypeChecker
        return self.get(request, *args, **kwargs)


# noinspection SpellCheckingInspection
class JobTaskManagementView(ProcessSecurity, View):
    permissions = get_conf('views__jobtask__management__permissions')

    # noinspection PyUnusedLocal
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

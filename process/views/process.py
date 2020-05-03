from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views import View

from process.conf import get_conf
from .generic_views import (
    ProcessSecurity,
    ProcessGenericCreateView,
    ProcessGenericListView,
    ProcessGenericUpdateView,
    ProcessGenericDeleteView
)


from process.models import Process, Job


class ProcessCreateView(ProcessGenericCreateView):
    model = Process
    success_url = get_conf('views__process__create__success_url')
    success_message = get_conf('views__process__create__success_message')
    permissions = get_conf('views__process__create__permissions')


class ProcessListView(ProcessGenericListView):
    model = Process
    title = 'Processes'
    filters = get_conf('views__process__list__url_allow_filters')
    permissions = get_conf('views__process__list__permissions')

    def post(self, request, *args, **kwargs):
        request = ProcessRunOnDemandView.as_view()(request)
        # noinspection PyTypeChecker
        return self.get(request, *args, **kwargs)


class ProcessUpdateView(ProcessGenericUpdateView):
    model = Process
    success_url = get_conf('views__process__update__success_url')
    success_message = get_conf('views__process__update__success_message')
    permissions = get_conf('views__process__update__permissions')


class ProcessDeleteView(ProcessGenericDeleteView):
    model = Process
    success_url = get_conf('views__process__delete__success_url')
    success_message = get_conf('views__process__delete__success_message')
    permissions = get_conf('views__process__delete__permissions')


class ProcessRunOnDemandView(ProcessSecurity, View):
    permissions = get_conf('views__process__run__permissions')

    # noinspection PyUnusedLocal
    def post(self, request, *args, **kwargs):
        try:
            process = get_object_or_404(Process, id=self.request.POST['process'])
            __, __ = Job.create(process)
        except Exception as e:
            messages.error(request, _(f'{e}'))
        finally:
            return request

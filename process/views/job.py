import logging
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views import View

from process.conf import get_conf
from .generic_views import (
    ProcessSecurity,
    ProcessGenericListView,
    ProcessGenericDeleteView
)
from process.models import Job

logger = logging.getLogger('django-process')


class JobListView(ProcessGenericListView):
    model = Job
    title = 'Jobs'
    filters = get_conf('views__job__list__url_allow_filters')
    permissions = get_conf('views__job__list__permissions')

    def post(self, request, *args, **kwargs):
        request = JobCancelView.as_view()(request)
        # noinspection PyTypeChecker
        return self.get(request, *args, **kwargs)


class JobDeleteView(ProcessGenericDeleteView):
    model = Job
    success_url = get_conf('views__job__delete__success_url')
    success_message = get_conf('views__job__delete__success_message')
    permissions = get_conf('views__job__delete__permissions')


class JobCancelView(ProcessSecurity, View):
    permissions = get_conf('views__job__cancel__permissions')

    # noinspection PyUnusedLocal
    def post(self, request, *args, **kwargs):
        logger.debug(f'cancel job i got post request=> {self.request.POST}')
        try:
            job = get_object_or_404(Job, id=self.request.POST['job'])
        except KeyError:
            messages.error(request, _('job does not exists'))
            return request

        try:
            job.cancel()
            messages.success(request, get_conf('views__job__cancel__success_message'))
        except Exception as e:
            logger.exception(f"can't cancel job due to error=> {e}")
            messages.error(request, _(f'{e}'))

        return request

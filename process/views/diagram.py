import logging
from django.shortcuts import render
from django.views import View

from process.conf import get_conf
from .generic_views import ProcessSecurity


from process.models import Job

logger = logging.getLogger('django-process')


class DiagramView(ProcessSecurity, View):
    model = None
    template = get_conf('views__templates__object_diagram')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.permissions = ['process.view_jobs'] if self.model == Job else ['process.view_processes']

    # noinspection PyUnusedLocal
    def get(self, request, pk, *args, **kwargs):
        obj = self.model.objects.get(id=pk)
        return render(request, self.template, {'object': obj})

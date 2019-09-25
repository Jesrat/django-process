import logging
from django.shortcuts import render

from process.conf import get_conf
from .generic_views import View, ProcessSecurity


from process.models import Job

logger = logging.getLogger('django-process')


class DiagramView(ProcessSecurity, View):
    model = None
    template = get_conf('views__templates__object_diagram')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.permissions = ['view_jobs'] if self.model == Job else ['view_processes']

    def get(self, request, pk, *args, **kwargs):
        obj = self.model.objects.get(id=pk)
        return render(request, self.template, {'object': obj})

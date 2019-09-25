import logging
from django.shortcuts import render
from django.views.generic.list import View, ListView
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


from process.models import Job, Process

logger = logging.getLogger('django-process')


class ProcessSecurity(LoginRequiredMixin, UserPassesTestMixin):
    raise_exception = True

    def test_func(self):
        if hasattr(self, 'permissions'):
            usr = self.request.user
            [logger.debug(f'user {usr.username} permission {i} result {usr.has_perm(i)}') for i in self.permissions]
            return not any([not self.request.user.has_perm(i) for i in self.permissions])
        return True


class ProcessGenericListView(ProcessSecurity, ListView):
    title = ''
    permissions = []
    paginate_by = 20
    template_name = settings.DJANGO_PROCESS['templates']['objects_list']
    filters = {}
    filters_apply = {}

    def get_queryset(self):
        # convert set to python dict
        request_dict = {k: v for k, v in self.request.GET.lists()}

        logger.debug(f"i'll search filters => {self.filters}")
        logger.debug(f"in request => {request_dict}")

        # search filters in url if filters do exists change key add __in
        self.filters_apply = {}
        for k in self.filters.copy():
            self.filters[k] = request_dict.get(k)
            if self.filters[k]:
                self.filters_apply[f'{k}__in'] = self.filters[k]

        logger.debug(f'filters to apply => {self.filters_apply}')
        if self.filters:
            return self.model.objects.filter(**self.filters_apply)
        else:
            return self.model.objects.all()

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        return context


class ProcessListView(ProcessGenericListView):
    model = Process
    title = 'Processes'
    filters = {'id': []}


class JobListView(ProcessGenericListView):
    model = Job
    title = 'Jobs'
    filters = {'process__id': [], 'status': []}


class DiagramView(ProcessSecurity, View):
    model = None
    template = settings.DJANGO_PROCESS['templates']['object_diagram']
    permissions = ['view_jobs'] if model == Job else ['view_processes']

    def get(self, request, pk, *args, **kwargs):
        logger.debug(f'permissions needed {self.permissions}')
        obj = self.model.objects.get(id=pk)
        return render(request, self.template, {'object': obj})

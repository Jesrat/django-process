import logging
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic.list import ListView
from django.utils.translation import gettext_lazy as _
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic.edit import UpdateView, CreateView, DeleteView

from process.conf import get_conf

logger = logging.getLogger('django-process')


# noinspection PyUnresolvedReferences
class ProcessSecurity(LoginRequiredMixin, UserPassesTestMixin):
    raise_exception = get_conf('views__security_raise_exception')

    def test_func(self):
        if hasattr(self, 'permissions'):
            usr = self.request.user
            [logger.debug(f'user {usr.username} permission {i} result {usr.has_perm(i)}') for i in self.permissions]
            return not any([not self.request.user.has_perm(i) for i in self.permissions])
        return True


class ProcessGenericListView(ProcessSecurity, ListView):
    title = ''
    permissions = []
    paginate_by = get_conf('views__paginate')
    template_name = get_conf('views__templates__objects_list')
    filters = {}

    def get_filters_from_request(self):
        # convert set to python dict
        request_dict = {k: v for k, v in self.request.GET.lists()}
        # search filters in url if filters do exists change key add __in
        return {f'{k}__in': request_dict.get(k) for k in self.filters if request_dict.get(k)}

    def get_queryset(self):
        filters = self.get_filters_from_request()

        if filters:
            return self.model.objects.filter(**filters)
        else:
            return self.model.objects.all()

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        return context


# noinspection PyUnresolvedReferences
class ProcessGenericEditView(ProcessSecurity, SuccessMessageMixin):
    fields = '__all__'
    template_name = get_conf('views__templates__object_edit')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.success_url = reverse_lazy(self.success_url)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['operation'] = self.operation
        return context


class ProcessGenericUpdateView(ProcessGenericEditView, UpdateView):
    operation = _('Update')


class ProcessGenericCreateView(ProcessGenericEditView, CreateView):
    operation = _('Create')


class ProcessGenericDeleteView(ProcessSecurity, SuccessMessageMixin, DeleteView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.template_name = get_conf('views__templates__object_delete')
        self.success_url = reverse_lazy(self.success_url)

    def delete(self, request, *args, **kwargs):
        if hasattr(self, 'success_message'):
            messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)

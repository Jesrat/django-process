import logging
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.utils.translation import gettext_lazy as _

from process.conf import get_conf
from .generic_views import (
    ProcessGenericCreateView,
    ProcessGenericListView,
    ProcessGenericUpdateView,
    ProcessGenericDeleteView
)

from process.models import Task, TaskDependence

logger = logging.getLogger('django-process')


class TaskListView(ProcessGenericListView):
    model = Task
    title = 'Tasks'
    filters = get_conf('views__task__list__url_allow_filters')
    permissions = get_conf('views__task__list__permissions')


class TaskDeleteView(ProcessGenericDeleteView):
    model = Task
    success_url = get_conf('views__task__delete__success_url')
    success_message = get_conf('views__task__delete__success_message')
    permissions = get_conf('views__task__delete__permissions')


class TaskCreateView(ProcessGenericCreateView):
    model = Task
    success_url = get_conf('views__task__create__success_url')
    success_message = get_conf('views__task__create__success_message')
    permissions = get_conf('views__task__create__permissions')
    redirect_to_edit = get_conf('views__task__create__redirect_to_edit')

    # noinspection PyTypeChecker
    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = form_class(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save()
            messages.success(request, self.success_message)
            if not self.redirect_to_edit:
                return HttpResponseRedirect(self.get_success_url())
            else:
                return redirect('process-tasks-update', pk=obj.id)

        return self.render_to_response(self.get_context_data(form=form))


class TaskUpdateView(ProcessGenericUpdateView):
    model = Task
    template_name = get_conf('views__templates__task_edit')
    success_url = get_conf('views__task__update__success_url')
    success_message = get_conf('views__task__update__success_message')
    permissions = get_conf('views__task__update__permissions')
    fields = [
        'name',
        'description',
        'is_active',
        'level',
        'offset',
        'interpreter',
        'arguments',
        'code',
    ]

    # noinspection PyUnresolvedReferences
    def get_context_data(self, **kwargs):
        if 'form' not in kwargs:
            kwargs['form'] = self.get_form()

        if 'parents' not in kwargs:
            kwargs['parents'] = self.object.parents.all().\
                extra(select={"badge": "'primary'", 'is_new': "''"}).\
                values('parent__id', 'parent__name', 'badge', 'is_new')

        exclude_ids = [i['parent__id'] for i in kwargs['parents']]
        exclude_ids += [self.object.id]
        if 'new_parents' in kwargs:
            exclude_ids += [i['parent__id'] for i in kwargs['new_parents']]

        # we get the tasks which can be parent
        kwargs['parent_options'] = self.object.process.tasks.all(). \
            exclude(id__in=exclude_ids). \
            values('id', 'name')

        return super().get_context_data(**kwargs)

    # noinspection PyUnresolvedReferences
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()

        parents = self.object.parents.filter(parent__id__in=request.POST.getlist('parents')).\
            extra(select={"badge": "'primary'", 'is_new': "''"}).\
            values('parent__id', 'parent__name', 'badge', 'is_new')

        new_parents = Task.objects.filter(id__in=request.POST.getlist('new-parents')). \
            extra(select={'parent__id': 'id', 'parent__name': 'name', 'badge': "'info'", 'is_new': "'new-'"}). \
            values('parent__id', 'parent__name', 'badge', 'is_new')

        response = self.render_to_response(self.get_context_data(form=form, parents=parents, new_parents=new_parents))
        if not form.is_valid():
            return response

        try:
            with transaction.atomic():
                self.object = form.save()

                # get or create parent relation
                for new_parent in new_parents:
                    new_parent['badge'] = 'danger'
                    parent_task = get_object_or_404(Task, id=new_parent['parent__id'])
                    __, __ = TaskDependence.objects.get_or_create(task=self.object, parent=parent_task)
                    new_parent['badge'] = 'primary'

                for current in self.object.parents.all():
                    if current.parent.id not in [i['parent__id'] for i in parents] + \
                           [i['parent__id'] for i in new_parents]:
                        current.delete()
            messages.success(request, self.success_message)
            return redirect('process-tasks-update', pk=self.object.id)
        except ValidationError as e:
            for msg in e.messages:
                messages.error(request, _(f'{msg}'))
            return response
        except Exception as e:
            messages.error(request, _(f'{e}'))
            return response

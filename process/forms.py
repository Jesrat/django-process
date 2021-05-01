from .models import Job, JobTask, Task, TaskDependence
from django import forms
from django.db.models import Q


class JobForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        status = self.instance.status
        choices = (('cancelled', 'cancelled'), (status, status)) if status in Job.cancelable else []
        if self.fields.get('status'):
            self.fields['status'].choices = choices

    class Meta:
        model = Job
        fields = '__all__'

    # noinspection PyUnusedLocal,PyAttributeOutsideInit
    def save(self, **kwargs):
        self.save_m2m = self._save_m2m
        if self.instance.status == Job.cancelled:
            self.instance.refresh_from_db()
            if self.instance.status in Job.cancelable:
                self.instance.cancel()
        return self.instance


class TaskForm(forms.ModelForm):
    parents = forms.ModelMultipleChoiceField(queryset=Task.objects.filter(pk=0), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['parents'].queryset = self.instance.process.tasks.filter(~Q(pk=self.instance.pk))
            self.fields['parents'].initial = [d.parent for d in self.instance.parents.all()]

    class Meta:
        model = Task
        fields = '__all__'

    def _save_m2m(self):
        print(f'cleaned_data {self.cleaned_data}')
        current_queryset = self.instance.parents.all()
        for current in current_queryset:
            if current.parent not in self.cleaned_data['parents']:
                current.delete()
        for parent in self.cleaned_data['parents']:
            if parent not in [c.parent for c in current_queryset]:
                relation = TaskDependence(parent=parent, task=self.instance)
                relation.save()


class JobTaskForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            choices = [(stat, stat) for name, opt_list, stat in JobTask.management if self.instance.status in opt_list]
            choices.append((self.instance.status, self.instance.status))
            self.fields['status'].choices = choices

    class Meta:
        model = JobTask
        fields = '__all__'

    def save_m2m(self):
        pass

    def save(self, **kwargs):
        if self.instance.status == JobTask.reopened:
            self.instance.reopen(main=True)
        return self.instance

import logging
from django import template
from django.utils.safestring import mark_safe

from process.conf import get_conf
from process.models import JobTask

logger = logging.getLogger('django-process')

register = template.Library()


@register.filter(name='get_image', is_safe=True)
def get_image(extension):
    path = get_conf(f'views__templates__extension_images__{extension}')
    return path


@register.simple_tag(takes_context=True)
def keep_filters(context, **kwargs):
    d = context['request'].GET.copy()
    for k, v in kwargs.items():
        d[k] = v
    for k in [k for k, v in d.items() if not v]:
        del d[k]
    return d.urlencode()


@register.filter(name='parents_as_badges', is_safe=True)
def parents_as_badges(parents):
    parent_badge_html = """
        <div class="btn btn-{badge} d-flex justify-content-between mb-1" style="cursor: default;">
            <input type="hidden" name="{is_new}parents" value="{id}">
            <span>{name}</span>
            <span class="badge badge-light" style="cursor: pointer;" onclick="removeParentTask(this);">X</span>
        </div>
        """
    response = ''
    for parent in parents:
        response += parent_badge_html.format(
            badge=parent['badge'],
            id=parent['parent__id'],
            name=parent['parent__name'],
            is_new=parent['is_new']
        )
    return mark_safe(response)


# noinspection SpellCheckingInspection
@register.filter(name='available_actions', is_safe=True)
def available_actions(task):
    html = """
    <div class="nav-item dropdown">
        <a class="nav-link dropdown-toggle" href="#" id="object-task-actions" role="button"
           data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">Actions     </a>
        <div class="dropdown-menu" aria-labelledby="object-task-actions">
            {forms}
        </div>
    </div>
    """
    form = """    
    <form method="POST" class="m-0">
        <input type="hidden" name="task" value="{task}">
        <input type="hidden" name="action" value="{status}">
        <button type="submit" class="dropdown-item btn">{action}</button>
    </form>
    """
    actions = []

    for opt_name, opt_list, status in JobTask.management:
        if task.status in opt_list:
            action = form.\
                replace('{task}', str(task.id)).\
                replace('{action}', opt_name).\
                replace('{status}', status)
            actions.append(action)

    response = ''
    if actions:
        response = html.format(forms="\n".join(actions))
    return mark_safe(response)


# noinspection SpellCheckingInspection
@register.filter(name='textarea', is_safe=True)
def textarea(content):
    if not content:
        return content

    rows = len(content.split('\n'))
    return mark_safe(
        '<textarea readonly cols="90" rows="{rows}" style="border-color: #0000000a;">{content}</textarea>'.format(
            **{'content': content, 'rows': 20 if rows > 20 else rows}
        )
    )

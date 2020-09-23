import logging
from django.conf import settings
from django.utils.translation import gettext_lazy as _

"""
when the module is loaded it will search in django's settings the dictionary DJANGO_PROCESS = {}
if it founds it, then it will override defaults values so the get_conf function will read from
defaults values.
"""

loaded = False

logger = logging.getLogger('django-process')


def override(defaults, custom):
    try:
        for k, v in custom.items():
            if isinstance(v, dict):
                override(defaults[k], v)
            else:
                defaults[k] = v
    except KeyError as e:
        e.args = (f'The key you were trying to override "{e.args[0]}" does not exists in defaults',)
        raise


def get_conf(conf):
    conf_tree = []
    try:
        conf_tree = conf.split('__')
        conf_src = default_settings.copy()
        for conf in conf_tree:
            conf_src = conf_src[conf]
        return conf_src
    except KeyError as e:
        e.args = (f"configuration does not exists {'/'.join(conf_tree)}",)
        raise


# noinspection PyUnusedLocal
def dummy_task_error_handler(task_id, exception): pass


# noinspection SpellCheckingInspection
default_settings = {
    'task': {
        'error_handler': dummy_task_error_handler
    },
    'views': {
        'paginate': 20,
        'security_raise_exception': True,
        'templates': {
            'objects_list': 'process/objects_list.html',
            'object_edit': 'process/object_edit.html',
            'object_delete': 'process/object_delete.html',
            'object_diagram': 'process/object_diagram.html',
            'task_edit': 'process/task_edit.html',
            'extension_images': {
                'pl': 'process/images/perl.png',
                'py': 'process/images/python.png',
                'sh': 'process/images/bash.png',
            },
        },
        'process': {
            'run': {
                'permissions': [
                    'process.view_processes',
                    'process.manage_processes',
                    'process.view_jobs',
                    'process.run_jobs'
                ],
            },
            'create': {
                'success_url': 'process-processes',
                'success_message': _('process created successfully'),
                'permissions': ['process.view_processes', 'process.add_process'],
            },
            'list': {
                'url_allow_filters': {'id': []},
                'permissions': ['process.view_processes'],
            },
            'update': {
                'success_url': 'process-processes',
                'success_message': _('process updated successfully'),
                'permissions': ['process.view_processes', 'process.change_process'],
            },
            'delete': {
                'success_url': 'process-processes',
                'success_message': _('process deleted successfully'),
                'permissions': ['process.view_processes', 'process.delete_process'],
            },
        },
        'task': {
            'create': {
                'success_url': 'process-tasks',
                'success_message': _('task created successfully'),
                'redirect_to_edit': True,
                'permissions': ['process.view_tasks', 'process.add_task'],
            },
            'list': {
                'url_allow_filters': {'id': [], 'process__id': []},
                'permissions': ['process.view_tasks'],
            },
            'update': {
                'success_url': 'process-tasks',
                'success_message': _('task updated successfully'),
                'permissions': ['process.view_tasks', 'process.change_task'],
            },
            'delete': {
                'success_url': 'process-tasks',
                'success_message': _('task deleted successfully'),
                'permissions': ['process.view_tasks', 'process.delete_task'],
            },
        },
        'job': {
            'list': {
                'url_allow_filters': {'id': [], 'process__id': [], 'status': []},
                'permissions': ['process.view_jobs'],
            },
            'delete': {
                'success_url': 'process-jobs',
                'success_message': _('job deleted successfully'),
                'permissions': ['process.view_jobs', 'process.delete_job'],
            },
            'cancel': {
                'success_message': _('job cancelled successfully'),
                'permissions': ['process.cancel_jobs'],
            },
        },
        'jobtask': {
            'list': {
                'url_allow_filters': {'id': [], 'job__id': [],  'task__id': [], 'status': []},
                'permissions': ['process.view_job_tasks'],
            },
            'delete': {
                'success_url': 'process-job-tasks',
                'success_message': _('task deleted successfully'),
                'permissions': ['process.view_job_tasks', 'process.delete_jobtask'],
            },
            'management': {
                'success_message': _('task successfully {action}'),
                'permissions': ['process.view_job_tasks', 'process.manage_job_tasks'],
            }
        },
    },
    'diagram': {
        'chart_height': '600',
        'node_width': '75',
        'node_padding': '0',
        'link_radius': '55',
        'link_line_width': '4',
        'link_color': 'black',
        'tasks_color': {
            'default': '#41c0a4',
            'initialized': '#419dc0',
            'awaiting': 'gray',
            'reopened': '#41c0a4',
            'retry': '#41c0a4',
            'finished': '#abd734',
            'cancelled': '#d76034',
            'forced': '#d734ab',
            'error': 'red',
        }
    }
}

if not loaded:
    try:
        logger.debug('overriding default settings of django-process')
        custom_settings = settings.DJANGO_PROCESS
        override(default_settings, custom_settings)
        loaded = True
    except AttributeError:
        pass

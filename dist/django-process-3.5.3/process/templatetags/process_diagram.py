from django import template
from django.utils.safestring import mark_safe
from django.conf import settings

from ..models import Process, Job, JobTask

register = template.Library()

html = """
<div id="container-process-{id}"></div>
<script>
Highcharts.chart('container-process-{id}', {
  chart: {
    height: 600,
    inverted: true
  },
  title: {
    useHTML: true,
    text: '{name}'
  },
  series: [{
    type: 'organization',
    name: '{name}',
    keys: ['from', 'to'],
    data: {data},
    levels: [],
    linkRadius: 55,
    linkLineWidth: 4,
    linkColor: 'black',
    nodes: {nodes},
    showCheckbox: true,
    colorByPoint: false,
    color: '#007ad0',
    dataLabels: {
      color: 'white',
    },
    borderColor: 'white',
    nodeWidth: 75,
    nodePadding: 0
  }],
  tooltip: {
    outside: true,
    formatter: function() {
      //debugger;
      return this.point.info;
    }
  },
  exporting: {
    allowHTML: true,
    sourceWidth: 800,
    sourceHeight: 600
  }
});
</script>
"""

task_colors = getattr(settings, 'DJ_PROCESS_TASK_COLOR', JobTask.status_color)


def get_task_as_node(t):
    def get_color(key):
        try:
            return task_colors[key]
        except KeyError:
            return JobTask.status_color[key]

    job_task = True if isinstance(t, JobTask) else False
    node_task = t.task if job_task else t
    return {
        'id': node_task.name,
        'name': node_task.name,
        'title': t.info if job_task else node_task.description,
        'level': node_task.level,
        'offset': node_task.offset,
        'info': t.info if job_task else node_task.description,
        'color': get_color(t.status) if job_task else get_color('default'),
    }


@register.filter(name='diagram', is_safe=True)
def diagram(obj):
    try:
        assert isinstance(obj, Process), "err"
        process = obj
    except AssertionError:
        assert isinstance(obj, Job), "argument is not Process object either Job object"
        process = obj.process

    data = []
    nodes = []
    for task in obj.tasks.all():
        nodes.append(get_task_as_node(task))
        tk = task if isinstance(obj, Process) else task.task
        if tk.childs.all().count():
            for child in tk.childs.all():
                data.append([str(tk.name), str(child.task.name)])
        else:
            data.append([str(tk.name), str(tk.name)])

    data.sort()
    response = html.replace('{id}', str(process.id))
    response = response.replace('{name}', str(obj.__str__()))
    response = response.replace('{data}', str(data))
    response = response.replace('{nodes}', str(nodes))
    return mark_safe(response)

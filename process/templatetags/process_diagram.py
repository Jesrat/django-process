from django import template
from django.utils.safestring import mark_safe

from process.conf import get_conf
from ..models import Process, Job, JobTask

register = template.Library()

# noinspection SpellCheckingInspection
html = """
<div id="container-process-{id}"></div>
<script>
Highcharts.chart('container-process-{id}', {
  chart: {
    height: """ + get_conf('diagram__chart_height') + """,
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
    linkRadius: """ + get_conf('diagram__link_radius') + """,
    linkLineWidth: """ + get_conf('diagram__link_line_width') + """,
    linkColor: '""" + get_conf('diagram__link_color') + """',
    nodes: {nodes},
    showCheckbox: true,
    colorByPoint: false,
    color: '#007ad0',
    dataLabels: {
      color: 'white',
    },
    borderColor: 'white',
    nodeWidth: """ + get_conf('diagram__node_width') + """,
    nodePadding: """ + get_conf('diagram__node_padding') + """
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


def get_task_as_node(t):
    job_task = True if isinstance(t, JobTask) else False
    node_task = t.task if job_task else t
    color = get_conf(f'diagram__tasks_color__{t.status}') if job_task else get_conf('diagram__tasks_color__default')
    return {
        'id': node_task.name,
        'name': node_task.name,
        'title': t.title if job_task else node_task.description,
        'level': node_task.level,
        'offset': node_task.offset,
        'info': t.info if job_task else node_task.description,
        'color': color,
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
    # noinspection PyUnresolvedReferences
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

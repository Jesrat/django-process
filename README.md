
# Django Process

Its a reusable app for execute scrits in workflows with dependecies
NEW VERSION 4.6 it allows you to use the complete app from the admin site with the graphics and custom actions

## Table of Contents
* [usage](#usage)
* [tips](#tips)
    * [execution of the processes](#exec)
    * [frequency of the process](#freq)
    * [render job/process workflow](#render-diagram)
    * [task placement in diagram](#task-placement)
    * [start job on demand](#job-start)
    * [reopen task for execution in cascade](#task-reopen)
    * [access to django builtins](#access-django)


## Usage: <a name="usage"></a>
* pip install django-process
* add 'process' to installed apps
* makemigrations and migrate them
* create a Process and Tasks which belong to the process.
(The Job is an instance executed of the process, JobTask is an instance executed of the Task you must not create manually any of them !) 
* (optional) you can create dependencies of the tasks for they to run sequentially, if you don't create dependencies the tasks will start all at once
* execute python manage.py run_jobs 


# TIPS: <a name="tips"></a>
## execution of the processes <a name="exec"></a>
just as simple as
```pycon
>>> python manage.py run_jobs
```

## frequency of the process <a name="freq"></a>
The process have a crontab-like configuration for set the frequency.
Lets take the attribute minute for example. You can:
* use * for all minutes
* specify a list of minutes 1,3,5,8,25,59
* specify a range of minutes 1-30
* combine list and ranges example 1,3,5,8,4-9 will be expanded to: 1,3,4,5,6,7,8,9
* for the moment it doesnt accept fractions using the / char

you can use any of those above for the five attributes just like a crontab.
##### the start job process runs each minute while the tasks manager its always online.   


## render process or job object as an workflow diagram <a name="render-diagram"></a>
in your html code you can render a Process as an image workflow
* {% load process_diagram %} in your html for use the diagram templatetag
* {% include "process/dj-process.html" %} in your html for include the CSS and JS
* {{ object|diagram }} to render the object
```html
{% load process_diagram %}
<!DOCTYPE html>
<html lang="en">
<head>
    {% include "process/dj-process.html" %}
    <meta charset="UTF-8">
    <title>Title</title>
</head>
    <body>
        {{ object|diagram }}
    </body>
</html>
```
this will return an output like this:
<span align="center">
<pre>
<a href="https://github.com/Jesrat/django-process"><img src="https://raw.githubusercontent.com/Jesrat/django-process/master/ext/workflow.jpg" align="center" /></a>
</pre>
</span>

## placing a task in an workflow diagram <a name="task-placement"></a>
Task objects have two attributes: level & offset you can place a task in a workflow diagram using those attributes
levels are vertical placement while offset are horizontal placements
* level: the value for level starts on 0 you can create as many levels as you want in workflow diagram
* offset: its a percentaje 0% will place your task in the middle 25% places to the right while -25% place the task to the left


## starting a Job and its tasks on demand <a name="job-start"></a>
The job needs a Process parent to be instanced:
```pycon
>>> process = Process.objects.all()[0]
>>> job, tasks = Job.create(process)
```
this will create the job for the process and also the tasks if the runner is online it will execute immediate
all the tasks created sequentially if you have defined dependencies for them or all at once if you have not


## reopen task for execution in cascasde <a name="task-reopen"></a>
you can reopen a task that has been executed already:
```pycon
>>> task = JobTask.objects.all()[0]
>>> task.reopen(main=True)
```
this will reopen the job task for execution again and it will set status awaiting for the childs in CASCADE

## access to django builtins <a name="access-django"></a>
If you want to use django functions or access models and their methods in a task-script

you need first import process.env example:
```pycon
import process.env
from yourapp.models import CustomModel

objects = CustomModel.objects.all()
for obj in objects:
    print(obj)
```
if you do not import process.env you will get an error trying to access django

## this short tutorial does not covers all the power for the app. I will be adding more examples
## if you got doubts or questions don't hesitate send me a mail or create an issue im always online   
[mail the author](mailto:jgomez@jesrat.com)


'''
    ESSArch - ESSArch is an Electronic Archive system
    Copyright (C) 2010-2015  ES Solutions AB

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    Contact information:
    Web - http://www.essolutions.se
    Email - essarch@essolutions.se
'''
__majorversion__ = "2.5"
__revision__ = "$Revision$"
__date__ = "$Date$"
__author__ = "$Author$"
import re
__version__ = '%s.%s' % (__majorversion__,re.sub('[\D]', '',__revision__))
from celery import Task, shared_task

# Start worker: celery --app=earkweb.celeryapp:app worker

# Example:
#     from somemethod.tasks import add
#     result = add.delay(2,5)
#     result.status
#     result.result
# @shared_task()
# def add(x, y):
#     return x + y

# @shared_task()
# def fancyfunc(x, y):
#     return x + y
#
# @shared_task()
# def anotherreallyfancyfunction(x, y):
#     return x + y

# @shared_task()
# def scan(x, y):
#     return x + y
# {
# 	      "name": "SomeCreation",
# 	      "container": {
# 	   		"xtype": "WireIt.FormContainer",
# 	   		"title": "METS XML Validation",
# 	   		"icon": "../../res/icons/valid-xml.png",
# 	   		"collapsible": true,
# 			"drawingMethod": "arrows",
# 	   		"fields": [
# 				{"type":"string", "inputParams": {"label": "check well-formed", "name": "param"}},
# 	   		],
# 			"terminals": [
#                              {"name": "_INPUT", "direction": [0,0], "offsetPosition": {"left": 160, "top": -13 },"ddConfig": {"type": "input","allowedTypes": ["output"]}, "nMaxWires": 1,  "drawingMethod": "arrows" },
#                              {"name": "_OUTPUT", "direction": [0,0], "offsetPosition": {"left": 160, "bottom": -13 },"ddConfig": {"type": "output","allowedTypes": ["input"]}}
#                          ],
#
# 	   		"legend": "METS XML Validation",
# 			"drawingMethod": "arrows"
# 	   	}
# 	   },
class SomeCreation(Task):
# Example:
#     from somemethod.tasks import SomeCreation
#     result = SomeCreation().apply_async(('test',), queue='smdisk')
#     result.status
#     result.result
    def __init__(self):
        self.ignore_result = False

    def run(self, param1, param2, *args, **kwargs):
        """
        This function creates something
        @type       param1: string
        @param      param1: First parameter
        @type       param2: string
        @param      param2: Second parameter
        @rtype:     string
        @return:    Parameter
        """
        return "Parameter: " + param1 + param2

class OtherJob(Task):
# Example:
#     from somemethod.tasks import SomeCreation
#     result = SomeCreation().apply_async(('test',), queue='smdisk')
#     result.status
#     result.result
    def __init__(self):
        self.ignore_result = False

    def run(self, param, *args, **kwargs):
        """
        This is another job
        @type       param: string
        @param      param: This task takes only one parameter
        @rtype:     string
        @return:    Parameter
        """
        return "Parameter: " + param

class ANewJobThatINeededRightNow(Task):
# Example:
#     from somemethod.tasks import SomeCreation
#     result = SomeCreation().apply_async(('test',), queue='smdisk')
#     result.status
#     result.result
    def __init__(self):
        self.ignore_result = False

    def run(self, param, *args, **kwargs):
        """
        This is another job
        @type       param: string
        @param      param: This task takes only one parameter
        @rtype:     string
        @return:    Parameter
        """
        return "Parameter: " + param
# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2014 Argil Consulting - http://www.argil.mx
############################################################################
#    Coded by: Israel Cruz Argil (israel.cruz@argil.mx)
############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
{
    'name': 'Project Issue Technical Solution',
    'version': '1',
    "author" : "Argil Consulting",
    "category" : "Project",
    'description': """
Project Issue Technical Solution
================================

This adds two fields:
* Customer can see technical solution? 
* Text field to explain solution (sql script, .py file, patch, etc)

    """,
    "website" : "http://www.argil.mx",
    "license" : "AGPL-3",
    "depends" : ["project", "project_issue","portal"],
    "data" : ["project_view.xml"],
    "installable" : True,
    "active" : False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to Odoo, Open Source Management Solution
#
#    Copyright (c) 2015 Argil Consulting - http://www.argil.mx
############################################################################
#    Coded by: Israel Cruz (israel.cruz@argil.mx)
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
##############################################################################
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
{
    "name": "Purchase Order with Barcode Reader", 
    "version": "1.0", 
    "author": "Argil Consulting", 
    "category": "Purchase", 
    "description": """
Purchase Order with Barcode Reader
==================================

This module adds in Purchase Order Form View a new field to read Product EAN13
and adds such product as a Line in Purchase Order.
This module creates new Security Group, so only users in that Group will be able 
to use that field.
""", 
    "website": "http://www.argil.mx", 
    "depends": [
        "purchase"
    ], 
    "data": [
        "view/purchase_view.xml",
        "security/purchase_security.xml",
    ], 
    "test": [], 
    "js": [], 
    "css": [], 
    "qweb": [], 
    "installable": True, 
}
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
    "name": "Account per Warehouse", 
    "version": "1.1", 
    "author": "Argil Consulting", 
    "category": "Account", 
    "description": """
Account per Warehouse
=====================

This module allows to use different Stock Inventory Account per Warehouse.

Odoo's default behavior to create Account Entries related to Stock Moves 
is to use Account defined in Product Category. So this module shows 
field to define Account for Internal Stock Location related to Warehouse.
    """, 
    "website": "http://www.argil.mx", 
    "depends": [
        "stock_account"
    ], 
    "demo": [], 
    "data": [
        "view/stock_location_view.xml"
    ], 
    "test": [], 
    "js": [], 
    "css": [], 
    "qweb": [], 
    "installable": True, 
}
# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013 Vauxoo - http://www.vauxoo.com
#    All Rights Reserved.
#    info@vauxoo.com
############################################################################
#    Coded by: julio (julio@vauxoo.com)
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
    "name": "POS - Daily Invoice", 
    "version": "1.1", 
    "author": "Argil Consulting", 
    "category": "POS", 
    "description": """
POS - Daily Invoice
===================

In México, if you make sales without specific customer (Called: General Public),
then Company must create one Global Invoice per day. This module helps with this matter.


Also, when creating an Invoice from POS Orders, then account entries must be
deleted in order to avoid duplicity in account entries.


This module adds a check in Customer Form View to set if this customer is "General Public"
or not. So, if a customer is selected in POS Order and check is active, then POS Order
will be taken to create Global Invoice.
But it will deppend on wizard, which will list all POS Order to be invoiced, with a column
with a check already active, only POS Order with value in Customer column can be unchecked

    """, 
    "website": "http://www.argil.mx", 
    "license": "AGPL-3", 
    "depends": ["base_setup", 
                "product", 
		        "account",
                "point_of_sale"
            ], 
    "data": [
        "view/pos_invoice_view.xml"
    ], 
    "test": [], 
    "js": [], 
    "css": [], 
    "qweb": [], 
    "installable": True, 
    "auto_install": False, 
    "active": False
}
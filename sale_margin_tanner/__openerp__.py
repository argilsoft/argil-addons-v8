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
    "name": "Sale Margin Tanner", 
    "version": "1.1", 
    "author": "Argil Consulting", 
    "category": "Sale", 
    "description": """
Sale Margin Tanner
==================

This module extends sale_margin module to fit Tanner requirements to compute Sales Comissions.

This modules computes product cost based on Sale Pricelist origin (a Purchase Pricelist).

    """, 
    "website": "http://www.argil.mx", 
    "depends": [
        "sale_margin",
        "tanner_desarrollo",
    ], 
    "demo": [], 
    "data": [
        "view/sale_margin_view.xml"
    ], 
    "test": [], 
    "js": [], 
    "css": [], 
    "qweb": [], 
    "installable": True, 
}
# -*- encoding: utf-8 -*-
###########################################################################
#
#    Copyright (c) 2015 Argil Consulting - http://www.argil.mx
#    All Rights Reserved.
############################################################################
#    Coded by: Israel CA (israel.cruz@argil.mx)
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
{
    "name": "Fixes Odoo addons v8", 
    "version": "1.0", 
    "author": "Argil", 
    "category": "Fixes", 
    "description": """

Fixes
=====

This module have several fixes for some modules.

* Base => 
res_currency => Currency Rate was miscalculated because of rate date
res_currency => Added some Fields for rate if Currency Tree and Form views


* Account => Account Invoice Analysis

Added colums:
    - Rate2 => This 
    - Residual in Invoice Currency
    - Invoice Number


You must run SQL query after installing this module:

update res_currency_rate set rate2=1/rate where rate <> 0;

    """, 
    "website": "http://www.argil.mx/", 
    "license": "AGPL-3", 
    "depends": [
        "argil_account_per_warehouse",
        "base", 
        "sale",
    ], 
    "data": [
        "res_currency_view.xml",
        "account_invoice_report_view.xml"
    ], 
    "js": [], 
    "css": [], 
    "qweb": [], 
    "installable": True, 
    "auto_install": False, 
    "active": False
}
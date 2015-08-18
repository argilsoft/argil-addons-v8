# -*- encoding: utf-8 -*-
#
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2015 - Argil Consulting - http://www.argil.mx
#    Info  (info@argil.mx)
#
#    Coded by: Israel Cruz Argil (israel.cruz@argil.mx)
#
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
#

{
    "name": "Account Advance Payment",
    "version": "1.0",
    "author": "Argil Consulting",
    "category": "Account",
    "description" : """
Account Advance Payment
=======================

This module you can help with advance payment for customers and suppliers.

This module adds fields Account Supplier Advance and Account Customer Advance,

Also adds the field Transaction Type in the view payments of customs and suppliers.

    """,
    "website": "http://www.argil.mx/",
    "license": "AGPL-3",
    "depends": [
            "account",
            "account_voucher",
                ],
    "data": [
        'view/res_partner_advance_payment_view.xml',
        'view/account_voucher_advance_payment_view.xml',
    ],
    "installable": True,
    "active": False,
}

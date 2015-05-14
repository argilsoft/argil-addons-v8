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
##############################################################################


{
    'name': 'Account Chart Consolidation',
    'version': '1.0',
    'category': 'Generic Modules/Account',
    'description': """ 
Account Chart Consolidation
===========================

This module helps to have Account Chart Consolidation for  Subsidiaries

Many companies in the World have subsidiaries in the same country. But they need to know profitability for each subsidiary, so multicompany environment is used.
The problem is that Consolidated accounts don't work between companies, unless you use this module.

This module requires:
* Chart of Account for each subsidiary
Example:
::
	Chart of Account for Subsidiary 1
	01	- Subsidiary 1
	01-1	- ASSETS
	01-11	- Banks
	01-111	- Bank for Subsidiary 1
	..
	..
	01-2	- LIABILITIES
	..
	..

        Chart of Account for Subsidiary 2
        02      - Subsidiary 2
        02-1    - ASSETS
        02-11   - Banks
        02-111  - Bank for Subsidiary 2
        ..
        ..
        02-2    - LIABILITIES
        ..
        ..

        Chart of Account for Subsidiary X
        0X      - Subsidiary 1
        0X-1    - ASSETS
        0X-11   - Banks
        0X-111  - Bank for Subsidiary X
        ..
        ..
        0X-2    - LIABILITIES
        ..
        ..


* Chart of Account for Holding Company, with consolidated accounts using subsidiaries accounts
::
        Chart of Account for Holding
        00      - Holding
        00-1    - ASSETS
	00-11	- Banks
	00-110	- Bank for Holding
	00-111	- Bank for Subsidiary 1 (Consolidated account pointing to Account 01-111)
	00-112	- Bank for Subsidiary 2 (Consolidated account pointing to Account 02-111)
	00-11X	- Bank for Subsidiary X (Consolidated account pointing to Account 0X-111)
        ..
        ..
        00-2    - LIABILITIES
        ..
        ..

* Holding and subsidiaries accounting are in the same currency
* Holding and subsidiaries Fiscal Year name and Periods name are exactly the same.
For example:
::
	Company		Fiscalyear name
	Holding		2014
	Subsidiary 1	2014
	Subsidiary 2	2014
	Subsidiary X	2014


        Company         Period name 
        Holding         08/2014
        Subsidiary 1    08/2014
        Subsidiary 2    08/2014
        Subsidiary X    08/2014


""",
    'author': 'Argil Consulting',
    'depends': ['account'],
    'data': ['account_chart_argil_view.xml',
             'account_view.xml',
            ],
    'website': 'http://www.argil.mx',
    'installable': True,
    'active': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

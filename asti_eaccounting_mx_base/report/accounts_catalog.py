# -*- encoding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Argil Consulting (<http://argil.mx>).
#
#	 Coded by: Israel CA (israel.cruz@argil.mx)
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

import time
from openerp.report import report_sxw

class accounts_catalog_rml_parser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context = None):
        if context is None:
            context = {}
        super(accounts_catalog_rml_parser, self).__init__(cr, uid, name, context=context)
        #print "context: ", context
        self.localcontext.update({'rfc': context['rfc'],
         'period': context['period'],
         'print_date': time.strftime('%d/%M/%Y'),
         'print_time': time.strftime('%H:%m:%S')})



report_sxw.report_sxw('report.rml.ceCatalogosContables', 'account.account', rml='asti_eaccounting_mx_base/report/accounts_catalog.rml', header='external', parser=accounts_catalog_rml_parser)


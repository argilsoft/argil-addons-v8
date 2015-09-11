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

from openerp.osv import fields, osv
from lxml import etree as et

class account_journal_fit(osv.osv):
    _inherit = 'account.journal'
    _columns = {'journal_type': fields.many2one('account.journal.types', 'Tipo de p\xc3\xb3liza'),
     'cmpl_type': fields.selection([('check', 'Cheque'), ('transfer', 'Transferencia'), ('payment', 'Otro m\xc3\xa9todo de pago')], string='Tipo de complemento', help='Indique el tipo de complemento que este diario generar\xc3\xa1 en las p\xc3\xb3lizas.'),
     'credit_cmpl_acc_id': fields.many2one('eaccount.bank.account', 'Cuenta bancaria acreedora', help='Especifique la cuenta bancaria a utilizar en los complementos de contabilidad electr\xc3\xb3nica'),
     'debit_cmpl_acc_id': fields.many2one('eaccount.bank.account', 'Cuenta bancaria deudora', help='Especifique la cuenta bancaria a utilizar en los complementos de contabilidad electr\xc3\xb3nica'),
     'other_payment': fields.many2one('eaccount.payment.methods', 'M\xc3\xa9todo de pago SAT')}

    def fields_view_get(self, cr, uid, view_id = None, view_type = 'form', context = None, toolbar = False, submenu = False):
        req = super(account_journal_fit, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
        if self.pool.get('res.users').browse(cr, uid, uid).company_id.auto_mode_enabled:
            return req
        if view_type == 'form':
            view_arch = et.fromstring(req['arch'])
            iters = -1
            for node in view_arch.getiterator('field'):
                if iters > 1:
                    break
                if node.get('name') in ('cmpl_type', 'debit_cmpl_acc_id', 'credit_cmpl_acc_id', 'other_payment'):
                    node.attrib['invisible'] = '1'
                    node.attrib['modifiers'] = '{"invisible" : true}'
                    iters += 1

            req['arch'] = et.tostring(view_arch, pretty_print=True)
        return req



account_journal_fit()


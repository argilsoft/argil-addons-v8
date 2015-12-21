# -*- coding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
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
from openerp import tools
import openerp.addons.decimal_precision as dp
from openerp.osv import fields,osv

class account_invoice_report(osv.osv):
    _inherit = "account.invoice.report"
    
    _columns = {
        'currency_rate'             : fields.float('Currency Rate', readonly=True, group_operator = 'avg'),
        'currency_rate2'            : fields.float('Rate MXN', readonly=True, digits_compute=(12,4), group_operator = 'avg'),
        'price_subtotal_inv_curr'   : fields.float('Base FC', readonly=True),
        'invoice_number'            : fields.char('Invoice Number', readonly=True),
        'residual2'                 : fields.float('Residual FC', readonly=True),
    }
    

    _depends = {
        'account.invoice': [
            'number', 'supplier_invoice_number',
        ],
        'res.currency.rate': ['rate2'],        
    }

    
    def init(self, cr):
        # self._table = account_invoice_report
        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""CREATE or REPLACE VIEW %s as (
            WITH currency_rate (currency_id, rate, rate2, date_start, date_end) AS (
                SELECT r.currency_id, r.rate, r.rate2, left(r.name::text,10)::date AS date_start,
                    (SELECT left(name::text,10)::date FROM res_currency_rate r2
                     WHERE left(r2.name::text, 10) > left(r.name::text, 10) AND
                           r2.currency_id = r.currency_id
                     ORDER BY r2.name ASC
                     LIMIT 1) AS date_end
                FROM res_currency_rate r
            )
            %s
            FROM (
                %s %s %s
            ) AS sub
            JOIN currency_rate cr ON
                (cr.currency_id = sub.currency_id AND
                 cr.date_start <= COALESCE(sub.date, NOW()) AND
                 (cr.date_end IS NULL OR cr.date_end > COALESCE(sub.date, NOW())))
        )""" % (
                    self._table,
                    self._select(), self._sub_select(), self._from(), self._group_by()))

    def _select(self):
        return  super(account_invoice_report, self)._select() + ", cr.rate2/sub.nbr as currency_rate2, sub.invoice_number, sub.price_total price_subtotal_inv_curr, sub.residual residual2"

    def _sub_select(self):
        return  super(account_invoice_report, self)._sub_select() + ", case when ai.supplier_invoice_number is not null THEN ai.supplier_invoice_number ELSE ai.number END invoice_number"

    def _group_by(self):
        return super(account_invoice_report, self)._group_by() + ", ai.number, ai.supplier_invoice_number, ail.price_subtotal"
        
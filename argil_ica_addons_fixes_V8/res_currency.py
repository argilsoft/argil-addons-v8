# -*- coding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
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
from openerp.osv import osv, fields
import time

class res_currency(osv.osv):
    _inherit = "res.currency"

    
    def _current_rate(self, cr, uid, ids, name, arg, context=None):
        return super(res_currency, self)._current_rate(cr, uid, ids, name, arg, context)
    
    def _current_rate_silent(self, cr, uid, ids, name, arg, context=None):
        return super(res_currency, self)._current_rate_silent(cr, uid, ids, name, arg, context)
    
    def _get_current_rate2(self, cr, uid, ids, name, arg, context=None):
        if context is None:
            context = {}
        res = {}

        date = context.get('date') or time.strftime('%Y-%m-%d')
        for id in ids:
            cr.execute('SELECT rate2, name FROM res_currency_rate '
                       'WHERE currency_id = %s '
                         'AND left(name::text, 10) <= %s '
                       'ORDER BY name desc LIMIT 1',
                       (id, date))
            if cr.rowcount:
                res[id] = cr.fetchone()[0]
            else:
                res[id] = 0
            #else:
            #    currency = self.browse(cr, uid, id, context=context)
            #    raise osv.except_osv(_('Error!'),_("No currency rate associated for currency '%s' for the given period" % (currency.name)))
        return res
    
    
    
    _columns = {
        'rate': fields.function(_current_rate, string='Current Rate', digits=(18,12),
            help='The rate of the currency to the currency of rate 1.'),
        'rate_silent2': fields.function(_get_current_rate2, string='Current Rate', digits=(12,6),
            help='The rate of the currency to the currency of rate 1'),
        
        # Do not use for computation ! Same as rate field with silent failing
        'rate_silent': fields.function(_current_rate_silent, string='Current Rate', digits=(18,12),
            help='The rate of the currency to the currency of rate 1 (0 if no rate defined).'),
    }

    
    def _get_current_rate(self, cr, uid, ids, raise_on_no_rate=True, context=None):
        if context is None:
            context = {}
        res = {}

        date = context.get('date') or time.strftime('%Y-%m-%d')
        for id in ids:
            cr.execute('SELECT rate FROM res_currency_rate '
                       'WHERE currency_id = %s '
                         'AND left(name::text, 10) <= %s '
                       'ORDER BY name desc LIMIT 1',
                       (id, date))
            if cr.rowcount:
                res[id] = cr.fetchone()[0]
            elif not raise_on_no_rate:
                res[id] = 0
            else:
                currency = self.browse(cr, uid, id, context=context)
                raise osv.except_osv(_('Error!'),_("No currency rate associated for currency '%s' for the given period" % (currency.name)))
        return res

class res_currency_rate(osv.osv):
    _inherit = "res.currency.rate"
    
    _columns = {
        'rate': fields.float('Rate', digits=(18, 12), help='The rate of the currency to the currency of rate 1'),
        'rate2': fields.float('Rate2', digits=(12, 6), help='If you leave blank field Rate, then it will be overwritten by this field as 1 / Rate2'),
    }
    
    def create(self, cr, uid, vals, context=None):
        if not vals['rate2'] and not vals['rate']:
            raise osv.except_osv(_('Error!'),_("No currency rate given"))
        if vals['rate2']:
            vals.update({'rate': 1.0  / vals['rate2']})
        elif vals['rate']:
            vals.update({'rate2': 1.0  / vals['rate']})
        return super(res_currency_rate, self).create(cr, uid, vals, context)

    
    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        if not ids:
            return True
        if isinstance(ids, (int, long)):
            ids = [ids]
        if 'rate2' in vals and vals['rate2']:
            vals.update({'rate': 1.0 / vals['rate2']})
        elif 'rate' in vals and vals['rate']:
            vals.update({'rate2': 1.0 / vals['rate']})
        return super(res_currency_rate, self).write(cr, uid, ids, vals, context=context)

    
# -*- encoding: utf-8 -*-
#
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013 Vauxoo - http://www.vauxoo.com/
#    All Rights Reserved.
#    info Vauxoo (info@vauxoo.com)
#
#    Coded by: Jorge Angel Naranjo (jorge_nr@vauxoo.com)
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

from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _

import openerp.addons.decimal_precision as dp


class account_voucher(osv.Model):
    _inherit = 'account.voucher'
    _columns = {
        'trans_type': fields.selection([
            ('normal', 'Payments'),
            ('advance', 'Advance'),
        ], 'Transaction Type', select=True, track_visibility='always',
            help="""Payments.- Normal payment is made. \nAdvance.- Advance payment of custom or supplier"""),
    }

    _defaults = {
        'trans_type': 'normal',
    }

    def on_change_account_advance_payment_supplier(self, cr, uid, ids, trans_type, partner_id, context=None):        
        if trans_type =='advance':
            partner_obj = self.pool.get('res.partner')
            acc_id = partner_obj.read(cr, uid, [partner_id], ['property_account_supplier_advance'])[0]['property_account_supplier_advance'] if partner_id else False
            return {'value': {'payment_option': 'with_writeoff', 'writeoff_acc_id': acc_id, 'comment' : _('Supplier Payment in Advance')}}
        else:
            return {'value': {'payment_option': 'without_writeoff', 'writeoff_acc_id': False, 'comment' : _('Write Off')}}


    def on_change_account_advance_payment_customer(self, cr, uid, ids, trans_type, partner_id, context=None):        
        if trans_type =='advance':
            partner_obj = self.pool.get('res.partner')
            acc_id = partner_obj.read(cr, uid, [partner_id], ['property_account_customer_advance'])[0]['property_account_customer_advance'] if partner_id else False
            return {'value': {'payment_option': 'with_writeoff', 'writeoff_acc_id': acc_id, 'comment' : _('Customer Payment in Advance')}}
        else:
            return {'value': {'payment_option': 'without_writeoff', 'writeoff_acc_id': False, 'comment' : _('Write Off')}}


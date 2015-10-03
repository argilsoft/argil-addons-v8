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
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import SUPERUSER_ID, api
import logging
_logger = logging.getLogger(__name__)


class sale_order_line(osv.osv):
    _inherit = "sale.order.line"

    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):
        res = super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product, qty=qty,
            uom=uom, qty_uos=qty_uos, uos=uos, name=name, partner_id=partner_id,
            lang=lang, update_tax=update_tax, date_order=date_order, packaging=packaging, fiscal_position=fiscal_position, flag=flag, context=context)
        if not pricelist:
            return res
        if context is None:
            context = {}
    
        pricelist_obj = self.pool.get('product.pricelist')
        frm_cur = self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id.id
        sale_pricelist = pricelist_obj.browse(cr, uid, [pricelist])[0]
        to_cur = sale_pricelist.currency_id.id
        if product:
            product = self.pool['product.product'].browse(cr, uid, product, context=context)
            ctx = context.copy()
            ctx['date'] = date_order
            currency_obj = self.pool.get('res.currency')
            purchase_price = currency_obj.compute(cr, uid,
                                3, sale_pricelist.currency_id.id,
                                float('%.*f' % (2,product.costo_usd)),
                                round=False, context=ctx)
            to_uom = ('value' in res) and res['value'].get('product_uom', uom) or False
            
            if to_uom != product.uom_id.id:
                purchase_price = self.pool['product.uom']._compute_price(cr, uid, product.uom_id.id, purchase_price, to_uom)
            price = (to_cur == 3)  and purchase_price or self.pool.get('res.currency').compute(cr, uid, frm_cur, to_cur, purchase_price, round=False, context=ctx)
            res['value'].update({'purchase_price': price})
        return res
    
    
    
    

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


class purchase_order(osv.osv):
    _inherit = "purchase.order"

    _columns = {
        'get_product_ean': fields.char('Add Product', size=64,
            help="Read a product barcode to add it as new Line."),
        }
    
#    def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
#            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
#            name=False, price_unit=False, state='draft', context=None):
        
    def onchange_product_ean(self, cr, uid, ids, get_product_ean, pricelist_id, 
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False, order_line=False,
            context=None):        
        context = context or {}
        if not get_product_ean:
            return
        qty = 1.0
        product_ean = get_product_ean
        if '+' in get_product_ean:
            try:
                product_ean = get_product_ean.split('+')[0]
                qty = float(get_product_ean.split('+')[1])
            except:
                warning = {'title': _('Warning!'),
                           'message': _("There is an error after symbol '+'. After product Barcode or Reference you can add '+' and quantity: %s") % (get_product_ean),
                          }
                return {'value' : {'get_product_ean':False},'warning':warning }
                
                
        product_obj = self.pool.get('product.product')
        prod_ids = product_obj.search(cr, uid, [('ean13','=',product_ean)], limit=1)
        if not prod_ids:
            prod_ids = product_obj.search(cr, uid, [('default_code','=',product_ean)], limit=1)
            if not prod_ids:
                warning = {'title': _('Warning!'),
                           'message': _("There is no product with Barcode or Reference: %s") % (product_ean),
                          }
                return {'value' : {'get_product_ean':False},'warning':warning }
            product = product_obj.browse(cr, uid, prod_ids)[0]
        product = product_obj.browse(cr, uid, prod_ids)[0]
        
        res = self.pool.get('purchase.order.line').onchange_product_id(cr, uid, ids, pricelist_id, product.id,
                                                                       1.0, product.uom_id.id, partner_id, date_order,
                                                                       fiscal_position_id, date_planned, name=False,
                                                                       price_unit=False, state='draft', context=context)        
        line = (0,0,{'product_id'   : product.id,
                     'name'         : res['value']['name'],
                     'date_planned' : res['value']['date_planned'],
                     'product_qty'  : qty,
                     'product_uom'  : res['value']['product_uom'],
                     'price_unit'   : res['value']['price_unit'],
                     'taxes_id'     : [(6,0,res['value']['taxes_id'])],
                        }
               )

        xorder_line = order_line and order_line or []
        xorder_line.append(line)
        return {'value': {'get_product_ean': False, 'order_line' : xorder_line}}

            
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:    
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


class stock_location(osv.osv):
    _inherit = "stock.location"

    _columns = {
        'change_std_price_account_id': fields.many2one('account.account', 'Change Standard Price Account', 
                                                        domain=[('type', '=', 'other')],
            help="This account will be used when changing Product Standard Price, if this account is not set then default product accounts will be used."),
        }
    
class stock_quant(osv.osv):
    _inherit = "stock.quant"


    def _get_accounting_data_for_valuation(self, cr, uid, move, context=None):
        """
        Return the accounts and journal to use to post Journal Entries for the real-time
        valuation of the quant.

        :param context: context dictionary that can explicitly mention the company to consider via the 'force_company' key
        :returns: journal_id, source account, destination account, valuation account
        :raise: osv.except_osv() is any mandatory account or journal is not defined.
        """
        product_obj = self.pool.get('product.template')
        accounts = product_obj.get_product_accounts(cr, uid, move.product_id.product_tmpl_id.id, context)
        journal_id = accounts['stock_journal']
        #####
        # Transferencias entre ubicaciones 'internal','transit','inventory','production'
        if move.location_id.usage in ('internal','transit','inventory','production') \
            and move.location_dest_id.usage in ('internal','transit','inventory','production'):
            acc_src = move.location_id.valuation_out_account_id and move.location_id.valuation_out_account_id.id \
                        or accounts.get('property_stock_valuation_account_id', False)
            acc_dest = move.location_dest_id.valuation_in_account_id and move.location_dest_id.valuation_in_account_id.id \
                        or accounts.get('property_stock_valuation_account_id', False)
            acc_valuation = False
            return journal_id, acc_src, acc_dest, acc_valuation

        # Transferencia de Entrada por Compra y/o Devolucion de Venta
        if move.location_id.usage in ('customer','supplier') and move.location_dest_id.usage in ('internal'):
            acc_src = move.location_id.usage in ('supplier') and accounts['stock_account_input'] or False
            acc_dest = move.location_id.usage in ('customer') and accounts['stock_account_output'] or False
            acc_valuation = move.location_dest_id.valuation_in_account_id and move.location_dest_id.valuation_in_account_id.id \
                        or accounts.get('property_stock_valuation_account_id', False)
            #acc_dest = acc_valuation
            return journal_id, acc_src, acc_dest, acc_valuation

        # Transferencia de Salida Venta y/o Devolucion de Compra
        if move.location_dest_id.usage in ('customer','supplier') and move.location_id.usage in ('internal'):
            acc_src = move.location_dest_id.usage in ('supplier') and accounts['stock_account_input'] or False
            acc_dest = move.location_dest_id.usage in ('customer') and accounts['stock_account_output'] or False
            acc_valuation = move.location_id.valuation_in_account_id and move.location_id.valuation_in_account_id.id \
                        or accounts.get('property_stock_valuation_account_id', False)
            #acc_dest = acc_valuation
            return journal_id, acc_src, acc_dest, acc_valuation
                
            
        return journal_id, acc_src, acc_dest, acc_valuation
    
    
    def _account_entry_move(self, cr, uid, quants, move, context=None):
        """
        Accounting Valuation Entries

        quants: browse record list of Quants to create accounting valuation entries for. Unempty and all quants are supposed to have the same location id (thay already moved in)
        move: Move to use. browse record
        """
        if context is None:
            context = {}
        location_obj = self.pool.get('stock.location')
        location_from = move.location_id
        location_to = quants[0].location_id
        company_from = location_obj._location_owner(cr, uid, location_from, context=context)
        company_to = location_obj._location_owner(cr, uid, location_to, context=context)

        if move.product_id.valuation != 'real_time':
            return False
        for q in quants:
            if q.owner_id:
                #if the quant isn't owned by the company, we don't make any valuation entry
                return False
            if q.qty <= 0:
                #we don't make any stock valuation for negative quants because the valuation is already made for the counterpart.
                #At that time the valuation will be made at the product cost price and afterward there will be new accounting entries
                #to make the adjustments when we know the real cost price.
                return False

        if move.location_id.usage in ('internal','transit','inventory','production') \
              and move.location_dest_id.usage in ('internal','transit','inventory','production'):
            ctx = context.copy()
            ctx['force_company'] = company_to and company_to.id or company_from.id
            journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation(cr, uid, move, context=ctx)
            self._create_account_move_line(cr, uid, quants, move, acc_src, acc_dest, journal_id, context=ctx)
            return
        #in case of routes making the link between several warehouse of the same company, the transit location belongs to this company, so we don't need to create accounting entries
        # Create Journal Entry for products arriving in the company
        if company_to and (move.location_id.usage not in ('internal', 'transit') and move.location_dest_id.usage == 'internal' or company_from != company_to):
            ctx = context.copy()
            ctx['force_company'] = company_to.id
            journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation(cr, uid, move, context=ctx)
            if location_from and location_from.usage == 'customer':
                #goods returned from customer
                self._create_account_move_line(cr, uid, quants, move, acc_dest, acc_valuation, journal_id, context=ctx)
            else:
                self._create_account_move_line(cr, uid, quants, move, acc_src, acc_valuation, journal_id, context=ctx)

        # Create Journal Entry for products leaving the company
        if company_from and (move.location_id.usage == 'internal' and move.location_dest_id.usage not in ('internal', 'transit') or company_from != company_to):
            ctx = context.copy()
            ctx['force_company'] = company_from.id
            journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation(cr, uid, move, context=ctx)
            if location_to and location_to.usage == 'supplier':
                #goods returned to supplier
                self._create_account_move_line(cr, uid, quants, move, acc_valuation, acc_src, journal_id, context=ctx)
            else:
                self._create_account_move_line(cr, uid, quants, move, acc_valuation, acc_dest, journal_id, context=ctx)
    
        return

class product_template(osv.osv):
    _inherit = 'product.template'


    def do_change_standard_price(self, cr, uid, ids, new_price, context=None):
        """ Changes the Standard Price of Product and creates an account move accordingly."""
        location_obj = self.pool.get('stock.location')
        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        if context is None:
            context = {}
        user_company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        loc_ids = location_obj.search(cr, uid, [('usage', '=', 'internal'), ('company_id', '=', user_company_id)])
        for rec_id in ids:
            datas = self.get_product_accounts(cr, uid, rec_id, context=context)
            for location in location_obj.browse(cr, uid, loc_ids, context=context):
                c = context.copy()
                c.update({'location': location.id, 'compute_child': False})
                product = self.browse(cr, uid, rec_id, context=c)

                diff = product.standard_price - new_price
                if not diff:
                    raise osv.except_osv(_('Error!'), _("No difference between standard price and new price!"))
                for prod_variant in product.product_variant_ids:
                    qty = prod_variant.qty_available
                    if qty:
                        # Accounting Entries
                        move_vals = {
                            'journal_id': datas['stock_journal'],
                            'company_id': location.company_id.id,
                        }
                        move_id = move_obj.create(cr, uid, move_vals, context=context)
    
                        if diff*qty > 0:
                            amount_diff = qty * diff
                            debit_account_id = location.change_std_price_account_id and location.change_std_price_account_id.id or datas['stock_account_input']
                            credit_account_id = location.valuation_out_account_id and location.valuation_out_account_id.id or datas['property_stock_valuation_account_id']
                        else:
                            amount_diff = qty * -diff
                            debit_account_id = location.valuation_in_account_id and location.valuation_in_account_id.id or datas['property_stock_valuation_account_id']
                            credit_account_id = location.change_std_price_account_id and location.change_std_price_account_id.id or datas['stock_account_output']
    
                        move_line_obj.create(cr, uid, {
                                        'name': _('Standard Price changed'),
                                        'account_id': debit_account_id,
                                        'debit': amount_diff,
                                        'credit': 0,
                                        'move_id': move_id,
                                        }, context=context)
                        move_line_obj.create(cr, uid, {
                                        'name': _('Standard Price changed'),
                                        'account_id': credit_account_id,
                                        'debit': 0,
                                        'credit': amount_diff,
                                        'move_id': move_id
                                        }, context=context)
            self.write(cr, uid, rec_id, {'standard_price': new_price})
        return True
    
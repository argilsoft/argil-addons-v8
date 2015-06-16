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


class account_move_line(osv.Model):
    _inherit = "account.move.line"

    """
    """

    _columns = {
        'stock_move_id': fields.many2one('stock.move', 'Stock Move'),
        'location_id': fields.related('stock_move_id', 'location_id', string='Source Location',
            type='many2one', relation='stock.location', store=True, help='Location Move Source'),
        'location_dest_id': fields.related('stock_move_id', 'location_dest_id',
            type='many2one', string='Destination Location', relation='stock.location', store=True,
            help="Location Move Destination")
    }

class stock_move(osv.Model):
    _inherit = "stock.move"

    """
    """

    _columns = {
        'account_move_line_ids' : fields.one2many('account.move.line', 'stock_move_id', 'Partidas Contables', readonly=True),
    }
    


class account_move(osv.Model):
    _inherit = "account.move"

    """
    """


    def show_stock_moves(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        context = context or {}
        res = []
        
        cr.execute(
                '''SELECT distinct stock_move_id
                   FROM account_move_line
                   WHERE move_id = %s;''' % (ids[0]))

        res = filter(None, map(lambda x:x[0], cr.fetchall()))
        print "res: ", res
        ir_model_data_obj = self.pool.get('ir.model.data')
        tree_view = ir_model_data_obj.get_object_reference(cr, uid, 'stock', 'view_move_tree')
        act_obj = self.pool.get('ir.actions.act_window')
        res_id = act_obj.search(cr, uid, [('res_model','=','stock.move'),('view_type','=','form'),
                                          ('view_id','=',tree_view and tree_view[1] or False)])
        result = act_obj.read(cr, uid, res_id, context=context)[0]
        result['domain'] = "[('id','in', [" + ','.join(map(str, res)) + "])]"
        return result
        
        

class stock_quant(osv.osv):
    _inherit = "stock.quant"


    def _create_account_move_line(self, cr, uid, quants, move, credit_account_id, debit_account_id, journal_id, context=None):
        #group quants by cost
        #print "· · · · · · · · · · · · · · ·"
        #print "move.id: ", move.id
        #print "move.product: (%s) %s" % (move.product_id.id, move.product_id.name)
        #print "move.product_uom_qty: ", move.product_uom_qty
        quant_cost_qty = {}
        for quant in quants:
            if quant_cost_qty.get(quant.cost):
                quant_cost_qty[quant.cost] += quant.qty
            else:
                quant_cost_qty[quant.cost] = quant.qty
        move_obj = self.pool.get('account.move')        
        stock_move_obj = self.pool.get('stock.move')
        for cost, qty in quant_cost_qty.items():
            move_lines = self._prepare_account_move_line(cr, uid, move, qty, cost, credit_account_id, debit_account_id, context=context)
            #print "move_lines (before): ", move_lines
            move_lines[0][2].update({'stock_move_id' : move.id})
            move_lines[1][2].update({'stock_move_id' : move.id})
            #print "move_lines (after): ", move_lines                        
            period_id = context.get('force_period', self.pool.get('account.period').find(cr, uid, context=context)[0])
            move_id = move_obj.create(cr, uid, {'journal_id': journal_id,
                                      'line_id': move_lines,
                                      'period_id': period_id,
                                      'date': fields.date.context_today(self, cr, uid, context=context),
                                      'ref': move.picking_id.name}, context=context)
                        
        #raise osv.except_osv('Pausa!', 'Pausa')


class stock_picking(osv.Model):
    _inherit = "stock.picking"

    def show_entry_lines(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        context = context or {}
        res = []
        for picking_brw in self.browse(cr, uid, ids, context=context):
            for move in picking_brw.move_lines:
                res += [x.id for x in move.account_move_line_ids]
                
        return {
            'domain': "[('id','in',\
                [" + ','.join(map(str, res)) + "])]",
            'name': _('Journal Entries'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move.line',
            'view_id': False,
            'type': 'ir.actions.act_window'
        }

    def show_journal_entries(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        context = context or {}
        res = []
        
        for picking_brw in self.browse(cr, uid, ids, context=context):
            for move in picking_brw.move_lines:
                res += [x.move_id.id for x in move.account_move_line_ids]
        res = list(set(res))
        return {
            'domain': "[('id','in',\
                [" + ','.join(map(str, res)) + "])]",
            'name': _('Journal Entries'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window'
        }


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
import time



class account_move(osv.osv):

    _inherit = 'account.move'

    def post(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        move_ids = ids
        for move in self.browse(cr, uid, ids):
            if move.journal_id.pos_dont_create_entries:
                self.unlink(cr, uid, [move.id])
                move_ids.remove(move.id)
        res = True
        if move_ids:
            res = super(account_move, self).post(cr, uid, move_ids, context)
        return res


class account_journal(osv.osv):
    _inherit = 'account.journal'
    """
	Adds check to indicate if Cash Account Journal will not create Account Entries
    """

    _columns = {
        'pos_dont_create_entries' : fields.boolean("No crear Pólizas de Tickets del POS", 
                                               help="Si marca esta casilla entonces no se van a generar pólizas de\n"+\
                                                    "los Ticketsde TPV (en el funcionamiento estándar se genera póliza\n"+\
                                                    "contable por cada Ticket de Venta, pero de alguna manera se\n"+\
                                                    "duplican las partidas cuando se crean las Facturas."),
        'pos_payments_remove_entries' : fields.boolean("Eliminar Pagos del POS",
                                                help="Las partidas contables generadas por los pagos de una TPV\n"+\
                                                     "se eliminarán cuando se haga el cierre de Caja"),

    }



class product_uom(osv.osv):
    _inherit = 'product.uom'
    """
	Adds check to indicate if Partner is General Public
    """

    _columns = {
        'use_4_invoice_general_public' : fields.boolean('Use for General Public Invoice'),
    }
    
    def _check_use_4_invoice_general_public(self, cr, uid, ids, context=None):        
        for record in self.browse(cr, uid, ids, context=context):
            if record.use_4_invoice_general_public:
                res = self.search(cr, uid, [('use_4_invoice_general_public', '=', 1)], context=None)                
                if res and res[0] and res[0] != record.id:
                    return False
        return True

    
    _constraints = [
        (_check_use_4_invoice_general_public, 'Error ! You can have only one Unit of Measure checked to Use for General Public Invoice...', ['use_4_invoice_general_public']),
        ]



class res_partner(osv.osv):
    _name = 'res.partner'
    _inherit = 'res.partner'
    """
	Adds check to indicate Partner is General Public
    """

    _columns = {
        'invoice_2_general_public'  : fields.boolean('Invoice to General Public Partner', help="Check this if this Customer will be invoiced as General Public"),
        'use_as_general_public'     : fields.boolean('Use as General Public Partner', help="Check this if this Customer will be used to create Daily Invoice for General Public"),
    }
    
    def _check_use_as_general_public(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids, context=context):
            if record.use_as_general_public:
                res = self.search(cr, uid, [('use_as_general_public', '=', 1)], context=None)                
                if res and res[0] and res[0] != record.id:
                    return False
        return True

    
    _constraints = [
        (_check_use_as_general_public, 'Error ! You can have only one Partner checked as Use as General Public...', ['use_as_general_public']),
        ]
        
    
    def on_change_use_as_general_public(self, cr, uid, ids, use_as_general_public=False, context=None):
        if context is None: context = {}
        res = {}
        if not use_as_general_public:
            return res
        
        if use_as_general_public:
            return {'value':{'invoice_2_general_public':False}}
    
    

class account_invoice_pos_reconcile_with_payments(osv.osv_memory):
    _name = "account.invoice.pos_reconcile_with_payments"
    _description = "Wizard to Reconcile POS Payments with Invoices from POS Orders"

    _columns = {
	   'date'		: fields.date('Payment Date', help='This date will be used as the payment date !', required=True),
    }

    _defaults = {
        'date': lambda *a	: time.strftime('%Y-%m-%d'),
	}
	

    def get_aml_to_reconcile(self, cr, uid, ids, context=None):
        am_obj = self.pool.get('account.move')
        amls = []
        for move in am_obj.browse(cr, uid, ids):
            for line in move.line_id:
                if line.account_id.type=='receivable':
                    #print "line: %s - %s - %s" % (move.name, line.account_id.code, line.account_id.name)
                    amls.append(line.id)
        return amls
	
    def reconcile_invoice_with_pos_payments(self, cr, uid, ids, context=None):
        if context is None: context = {}
        rec_ids = context.get('active_ids', [])
        
        inv_obj = self.pool.get('account.invoice')
        aml_obj = self.pool.get('account.move.line')
        am_obj = self.pool.get('account.move')
        pos_order_obj = self.pool.get('pos.order')
        
        for invoice in inv_obj.browse(cr, uid, rec_ids, context):
            if invoice.state != 'open':
                continue                
            order_ids = pos_order_obj.search(cr, uid, [('invoice_id','=',invoice.id)])
            data_statement_line_ids, data_aml_ids = [], []
            for order in pos_order_obj.browse(cr, uid, order_ids, context):
                if order.session_id.state != 'closed':
                    raise osv.except_osv('Advertencia!', "La Sesion %s del TPV %s asociado al Ticket %s el cual esta asociado a la Factura %s no ha sido cerrada, no se pudo realizar la Conciliacion de los Pagos. Primero cierre la sesion para poder correr este proceso." % (order.session_id.name, order.session_id.config_id.name, order.name, invoice.number))
                if order.state != 'invoiced':
                    continue
                for statement in order.statement_ids:
                    if statement.statement_id.journal_id.pos_payments_remove_entries: 
                        continue
                    aml_ids = [x.id for x in statement.journal_entry_id.line_id]
                    if aml_ids: data_aml_ids += aml_ids
                    am_id = statement.journal_entry_id.id
                    posted = bool(statement.journal_entry_id.state=='posted')
                    if posted:
                        am_obj.button_cancel(cr, uid, [am_id])
                    if not statement.journal_entry_id.partner_id or statement.journal_entry_id.partner_id.id != invoice.partner_id.id:
                        am_obj.write(cr, uid, [am_id], {'partner_id': invoice.partner_id.id})
                        aml_obj.write(cr, uid, aml_ids, {'partner_id': invoice.partner_id.id})
                    data_statement_line_ids.append(statement.id)

            if data_aml_ids:
                move_ids = []
                cad = ','.join(str(e) for e in data_aml_ids)
                cr.execute("select distinct statement_id from account_move_line where id in (%s);" % (cad))
                a = cr.fetchall()
                statement_ids = [x[0] for x in a]
                for xstatement in statement_ids:
                    cr.execute("select distinct move_id from account_move_line where id in (%s) and statement_id=%s limit 1;" % (cad, xstatement))
                    move_id = cr.fetchall()[0][0]
                    cr.execute("""update account_bank_statement_line set journal_entry_id=%s where id in (%s);""" % 
                               (move_id, ','.join(str(x) for x in data_statement_line_ids)))
                    cr.execute("select distinct move_id from account_move_line where id in (%s) and statement_id=%s;" % (cad, xstatement))
                    xids = [x[0] for x in cr.fetchall()]
                    for move in am_obj.browse(cr, uid, xids):
                        if move_id != move.id:
                            move_ids.append(str(move.id))
                    cr.execute("""
                        drop table if exists argil_account_move_line;
                        create table argil_account_move_line
                        as
                        select now() create_date, now() write_date, create_uid, write_uid, date, company_id,
                            statement_id, partner_id, blocked, journal_id, centralisation, 
                            state, account_id, period_id, not_move_diot, ref, 'Pagos de Sesion: ' || ref as name,
                            %s::integer as move_id,
                            case 
                            when sum(debit) - sum(credit) > 0 then sum(debit) - sum(credit)
                            else 0
                            end::float debit,
                            case 
                            when sum(credit) - sum(debit) > 0 then sum(credit) - sum(debit)
                            else 0
                            end::float credit
                            from account_move_line
                            where id in (%s) and statement_id=%s
                            group by create_uid, write_uid, date, company_id, 
                            statement_id, partner_id, blocked, journal_id, centralisation, 
                            state, account_id, period_id, not_move_diot, ref;

                        update argil_account_move_line
                        set partner_id = %s 
                        where partner_id is null;
                        
                        update argil_account_move_line set account_id = %s
                        where account_id in (select id from account_account where type='receivable');

                        delete from account_move_line where id in (%s) and statement_id=%s;
                        delete from account_move where id in (%s);

                        insert into account_move_line
                        (
                            create_date, write_date, create_uid,  write_uid, date, company_id, 
                            statement_id, partner_id, blocked, journal_id, centralisation,
                            state, account_id, period_id, not_move_diot, ref, name, move_id,
                            debit, credit)
                        (select create_date, write_date, create_uid,  write_uid, date, company_id, 
                            statement_id, partner_id, blocked, journal_id, centralisation,
                            state, account_id, period_id, not_move_diot, ref, name, move_id,
                            debit, credit
                        from argil_account_move_line);
                        drop table if exists argil_account_move_line;

                    """ % (move_id, cad, xstatement, invoice.partner_id.id, invoice.account_id.id, cad, xstatement, (move_ids and ', '.join(move_ids) or '0')))
                    if posted:
                        am_obj.post(cr, uid, [move_id])
                aml_to_reconcile = self.get_aml_to_reconcile(cr, uid, [move_id, invoice.move_id.id])    
                res2 = aml_obj.reconcile_partial(cr, uid, aml_to_reconcile, context=context)


        #raise osv.except_osv('Pausa!', 'Pausa')
        return True
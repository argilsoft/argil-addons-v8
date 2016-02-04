# -*- encoding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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

from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.osv import fields
from openerp.osv import osv
from openerp.tools.translate import _
from openerp import netsvc

#Importamos la libreria logger
import logging
#Definimos la Variable Global
_logger = logging.getLogger(__name__)


class account_voucher_tax_fix_entries2(osv.osv_memory):
    _name = 'account.voucher.tax.fix2'
    
    
    def run_fixes(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        record_ids =  context.get('active_ids',[])
        
        self.pool.get('account.voucher.tax.fix').fix_tax_account_moves(cr, uid, record_ids, context)
        return True

class account_voucher_tax_fix_entries(osv.osv_memory):
    _name = 'account.voucher.tax.fix'

    _columns = {
            'company_id'  : fields.many2one('res.company', 'Company', readonly=True),
            'date_start'  : fields.date('Fecha Inicial', required=True),
            'date_end'    : fields.date('Fecha Final', required=True),
        }

    _defaults = {'date_start' : fields.date.context_today,
                 'date_end'   : fields.date.context_today,
                 'company_id' : lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, uid).company_id.id,
                 }

    
    def run_fixes(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
            
        rec = self.browse(cr, uid, ids)[0]
    
        #print "Intentando conectar,..."
        fecha_inicial = rec.date_start
        fecha_final = rec.date_end
        company_obj = self.pool.get('res.company')
        sql =""
        for company in company_obj.browse(cr, uid, [rec.company_id.id]):
            #print "==============================="
            #print "Recorriendo los pagos de la Sucursal"
            #print "%s" % (company.name)
            #print "==============================="

            sql ="""
                    select distinct avl.voucher_id--,  ai.number, ai.supplier_invoice_number, ai.currency_id, aj.currency

                    from 

                    account_voucher_line avl
                    inner join account_voucher av on av.id=avl.voucher_id and av.date >= '%s' and av.date <= '%s' and av.company_id= %s and av.state='posted' and av.amount > 0
                    inner join account_move_line aml on aml.id=avl.move_line_id
                    inner join account_move am on am.id=aml.move_id
                    inner join account_invoice ai on ai.move_id=am.id --and ai.currency_id=3
                    inner join account_journal aj on aj.id=av.journal_id-- and aj.currency is null
                    where avl.amount > 0.0;

            """ % (fecha_inicial, fecha_final, company.id)

            cr.execute(sql)
            voucher_ids = [x[0] for x in cr.fetchall()]
            self.fix_tax_account_moves(cr, uid, voucher_ids, context)
        return True

    def fix_tax_account_moves(self, cr, uid, ids, context=None):        
        context = context or {}
        acc_v_obj = self.pool.get('account.voucher')
        move_obj = self.pool.get('account.move')

        invoice_obj = self.pool.get('account.invoice')

        voucher_ids = ids
        x = len(voucher_ids)
        #print "Comprobantes a procesar: ", x
        y = 0
        for voucher in acc_v_obj.browse(cr, uid, voucher_ids, context):
            y = y + 1 
            _logger.info(". . . . . . . . . .%s de %s . . . . . . . . . . . . . . . . ." % (y, x))
            _logger.info("Voucher: %s - %s - %s - %s - %s - Monto: %s" % (voucher.id, voucher.number, voucher.date, voucher.move_id.period_id.name, voucher.move_id.date, voucher.amount))
            move_obj.button_cancel(cr, uid, [voucher.move_id.id])
            #print "Despues de desasentar la poliza..."
            sql = """delete from account_move_line where move_id=%s and account_id in 
                        (select account_collected_id from account_tax where account_collected_id is not null
                        union all 
                        select account_paid_voucher_id from account_tax where account_paid_voucher_id is not null
                        union all 
                        select account_collected_voucher_id from account_tax  where account_collected_voucher_id is not null
                        );
                        delete from account_move_line where move_id=%s and name ilike '""" % (voucher.move_id.id, voucher.move_id.id)
            sql = sql + "%"
            sql = sql + "- Factura:"
            sql = sql + "%';"

            cr.execute(sql)
            res = acc_v_obj.voucher_move_line_tax_create(cr, uid, voucher.id, voucher.move_id.id, context)
            move_obj.button_validate(cr, uid, [voucher.move_id.id])
        return



# -*- coding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2012 Vauxoo - http://www.vauxoo.com
#    All Rights Reserved.
#    info@vauxoo.com
############################################################################
#    Coded by: Rodo (rodo@vauxoo.com)
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

from openerp.addons.decimal_precision import decimal_precision as dp
from openerp.tools.translate import _

class account_voucher(osv.Model):
    _inherit = 'account.voucher'

    def voucher_move_line_create(self, cr, uid, voucher_id, line_total, move_id, company_currency, current_currency, context=None):
        res = super(account_voucher, self).voucher_move_line_create(cr, uid, voucher_id, line_total, move_id, company_currency, current_currency, context=None)
        self.voucher_move_line_tax_create(cr, uid, voucher_id, move_id, context=context)
        #~ res[1] and res[1][0]+new
        return res


    def get_rate(self, cr, uid, move_id, context=None):
        move_obj = self.pool.get('account.move')
        if not context:
            context = {}
        for move in move_obj.browse(cr, uid, [move_id], context):
            for line in move.line_id:
                amount_base = line.debit or line.credit or 0
                rate = 1
                if amount_base and line.amount_currency:
                    rate = amount_base / line.amount_currency
                    return rate
        return rate


    def voucher_move_line_tax_create(self, cr, uid, voucher_id, xmove_id, context=None):
        if context is None:
            context = {}
        ctx = context.copy()
        precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')
        currency_obj = self.pool.get('res.currency')
        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        invoice_obj = self.pool.get('account.invoice')
        company_currency = self._get_company_currency(cr, uid, voucher_id, context)
        current_currency = self._get_current_currency(cr, uid, voucher_id, context)
        move_ids = []
        for voucher in self.browse(cr, uid, [voucher_id], context=context):
            if voucher.amount <= 0:
              continue
            flag_journal_fc = bool(company_currency != current_currency)            
            for line in voucher.line_ids:
                amount_to_paid = line.amount_original if line.amount > line.amount_original else line.amount
                factor = ((amount_to_paid * 100) / line.amount_original) / 100 if line.amount_original else 0
                move_id = line.move_line_id.move_id.id
                invoice_ids = invoice_obj.search(cr, uid, [('move_id', '=', move_id)], context=context)                
                for invoice in invoice_obj.browse(cr, uid, invoice_ids, context=context):
                    for inv_line_tax in invoice.tax_line:
                        if not inv_line_tax.tax_id.tax_category_id.name in ('IVA', 'IVA-EXENTO', 'IVA-RET', 'IVA-PART'):
                            continue
                        # Inicio Modificacion
                        src_account_id = inv_line_tax.tax_id.account_collected_id.id
                        dest_account_id = inv_line_tax.tax_id.account_collected_voucher_id.id or inv_line_tax.tax_id.account_paid_voucher_id.id
                        if not (src_account_id and dest_account_id):
                            raise osv.except_osv('Advertencia !',"El impuesto %s no se encuentra correctamente configurado, favor de revisar." % (inv_line_tax.tax_id.name))
                        voucher_curr = current_currency
                        invoice_curr = invoice.currency_id.id
                        company_curr = company_currency
                        mi_invoice = inv_line_tax.amount * factor
                        mib_invoice = inv_line_tax.base_amount * factor
                        ctx['date'] = invoice.date_invoice 
                        mi_company_curr_orig = currency_obj.compute(cr, uid,
                                    invoice.currency_id.id, company_curr,
                                    float('%.*f' % (2,mi_invoice)),
                                    round=False, context=ctx)
                        mib_company_curr_orig = currency_obj.compute(cr, uid,
                                    invoice.currency_id.id, company_curr,
                                    float('%.*f' % (2,mib_invoice)),
                                    round=False, context=ctx)
                        mi_voucher_curr_orig = currency_obj.compute(cr, uid,
                                    invoice.currency_id.id, voucher_curr,
                                    float('%.*f' % (2,mi_invoice)),
                                    round=False, context=ctx)
                        mib_voucher_curr_orig = currency_obj.compute(cr, uid,
                                    invoice.currency_id.id, voucher_curr,
                                    float('%.*f' % (2,mib_invoice)),
                                    round=False, context=ctx)
                                                
                        ctx['date'] = voucher.date 
                        mi_invoice_voucher_date = currency_obj.compute(cr, uid,
                                                    invoice.currency_id.id, company_curr,
                                                    float('%.*f' % (2,mi_invoice)),
                                                    round=False, context=ctx) * factor

                        mib_invoice_voucher_date = currency_obj.compute(cr, uid,
                                                    invoice.currency_id.id, company_curr,
                                                    float('%.*f' % (2,mib_invoice)),
                                                    round=False, context=ctx) * factor

                        mi_voucher_amount_currency3 = currency_obj.compute(cr, uid,
                                                    invoice.currency_id.id, current_currency,
                                                    float('%.*f' % (2,mi_invoice)),
                                                    round=False, context=ctx) * factor
                        mi_voucher_amount_currency2 = currency_obj.compute(cr, uid,
                                                    current_currency, company_currency,
                                                    float('%.*f' % (2,mi_voucher_amount_currency3)),
                                                    round=False, context=ctx) * factor

                        journal_id = voucher.journal_id.id
                        period_id = voucher.period_id.id
                        acc_a = inv_line_tax.account_analytic_id and inv_line_tax.account_analytic_id.id or False
                        date = voucher.date
                        # Partida correspondiente al Monto Original del Impuesto en la factura
                        line2 = {
                            'name': inv_line_tax.tax_id.name + ((_(" - Invoice: ") +  (invoice.supplier_invoice_number or invoice.internal_number)) or ''),
                            'quantity': 1,
                            'partner_id': invoice.partner_id.id, 
                            'debit': round((mi_company_curr_orig < 0.0 and -mi_company_curr_orig or 0.0), precision),
                            'credit': round((mi_company_curr_orig >= 0.0 and mi_company_curr_orig or 0.0), precision),
                            'account_id': src_account_id, 
                            'journal_id': journal_id,
                            'period_id': period_id,
                            'company_id': invoice.company_id.id,
                            'move_id': int(xmove_id),
                            'tax_id_secondary': inv_line_tax.tax_id.id,
                            'analytic_account_id': acc_a,
                            'date': date,
                            'currency_id': (company_currency != invoice_curr) and invoice_curr or False,
                            'amount_currency' : (company_currency != invoice.currency_id.id) and ((mi_invoice >= 0.0) and -mi_invoice or mi_invoice) or False,
                            'amount_base' : mib_company_curr_orig,
                            'state' : 'draft',
                        }

                        line1 = line2.copy()
                        line3 = {}
                        xparam = self.pool.get('ir.config_parameter').get_param(cr, uid, 'tax_amount_according_to_currency_exchange_on_payment_date', context=context)[0]
                        if not xparam == "1" or (company_curr == voucher_curr == invoice_curr):
                            line1.update({
                                'account_id'  : dest_account_id,
                                'debit'       : line2['credit'],
                                'credit'      : line2['debit'],
                                'amount_base' : line2['amount_base'],
                                
                                })
                            if company_currency != current_currency:
                                line1.update({
                                        'amount_currency' : -line2['amount_currency']
                                    })
                        elif xparam == "1":                                                        
                            line1.update({
                                'debit': mi_voucher_amount_currency2 >= 0.0 and mi_voucher_amount_currency2 or 0.0,
                                'credit': mi_voucher_amount_currency2 < 0.0 and -mi_voucher_amount_currency2 or 0.0,
                                'account_id': dest_account_id,
                                'currency_id': (company_currency != current_currency) and current_currency or False,
                                'amount_currency' : (company_currency != current_currency) and mi_voucher_amount_currency3 or False,
                                'amount_base' : abs(mi_voucher_amount_currency2) / inv_line_tax.tax_id.amount,
                                })

                            if (mi_company_curr_orig != mi_voucher_amount_currency2):
                                amount_diff =  mi_company_curr_orig - mi_voucher_amount_currency2
                                line3 = {
                                    'name': _('Write Off for Voucher') + ' - ' + inv_line_tax.tax_id.name + (invoice and (_(" - Invoice: ") +  (invoice.supplier_invoice_number or invoice.internal_number)) or ''),
                                    'quantity': 1,
                                    'partner_id': invoice.partner_id.id,
                                    'debit': amount_diff >= 0.0 and amount_diff or 0.0,
                                    'credit': amount_diff < 0.0 and abs(amount_diff) or 0.0,
                                    'account_id': (amount_diff < 0 ) and invoice.company_id.income_currency_exchange_account_id.id or invoice.company_id.expense_currency_exchange_account_id.id,
                                    'journal_id': journal_id,
                                    'period_id': period_id,
                                    'company_id': invoice.company_id.id,
                                    'move_id': int(xmove_id),
                                    #'tax_id': tax_id,
                                    'analytic_account_id': acc_a,
                                    'date': date,
                                    'currency_id': False,
                                    'amount_currency' : False,
                                    'state' : 'draft',
                                    }
                            else:
                                line3 = {}
                        lines = line3 and [line1,line2,line3] or [line1,line2]
                        #raise osv.except_osv('Pausa!',"Pausa")
                        for move_line_tax in lines:
                            #print "move_line_tax: ", move_line_tax
                            move_create = move_line_obj.create(cr, uid, move_line_tax,
                                                    context=context)
                            move_ids.append(move_create)
        return move_ids


#    def _get_base_amount_tax_secondary(self, cr, uid, line_tax,
#                            amount_base_tax, reference_amount, context=None):
#        amount_base = 0
#        tax_secondary = False
#        if line_tax and line_tax.tax_category_id and line_tax.tax_category_id.name in (
#                'IVA', 'IVA-EXENTO', 'IVA-RET', 'IVA-PART'):
#            amount_base = line_tax.tax_category_id.value_tax and\
#                reference_amount / line_tax.tax_category_id.value_tax\
#                or amount_base_tax
#            tax_secondary = line_tax.id
#        return [amount_base, tax_secondary]






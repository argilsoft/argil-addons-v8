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
            for line in voucher.line_ids:
                if line.amount > line.amount_original:
                    amount_to_paid = line.amount_original
                else:
                    amount_to_paid = line.amount
                factor = ((amount_to_paid * 100) / line.amount_original) / 100 if line.amount_original else 0
                move_id = line.move_line_id.move_id.id
                invoice_ids = invoice_obj.search(cr, uid, [('move_id', '=', move_id)], context=context)
                for invoice in invoice_obj.browse(cr, uid, invoice_ids, context=context):
                    for inv_line_tax in invoice.tax_line:
                        if inv_line_tax.tax_id.tax_voucher_ok:
                            base_amount = inv_line_tax.amount
                            account = inv_line_tax.tax_id.account_collected_voucher_id.id
                            credit_amount = float('%.*f' % (2, (base_amount * factor)))
                            credit_amount_original = (base_amount * factor)
                            amount_unround = float(credit_amount_original)
                            diff_amount_tax = 0.0
                            diff_account_id = False
                            if company_currency == current_currency:
                                base_amount_curr = inv_line_tax.base_amount
                                rate_move = self.get_rate(cr, uid, move_id, context=context)                                
                                credit_amount = credit_amount * rate_move
                                amount_unround = amount_unround * rate_move
                            else:
                                credit_amount = currency_obj.compute(cr, uid,
                                    invoice.currency_id.id, current_currency,
                                    float('%.*f' % (2, credit_amount)),
                                    round=False, context=context)
                                amount_unround = currency_obj.compute(cr, uid,
                                    invoice.currency_id.id, current_currency,
                                    float(amount_unround), round=False,
                                    context=context)
                                base_amount_curr = currency_obj.compute(cr, uid,
                                    invoice.currency_id.id, current_currency,
                                    float('%.*f' % (2, base_amount)), round=False,
                                    context=context)
                                ctx['date'] = invoice.date_invoice 
                                credit_orig = currency_obj.compute(cr, uid,
                                    current_currency, company_currency,
                                    float('%.*f' % (2, credit_amount)),
                                    round=False, context=ctx)
                                ctx['date'] = voucher.date
                                credit_diff = currency_obj.compute(cr, uid,
                                    current_currency, company_currency,
                                    float('%.*f' % (2, credit_amount)),
                                    round=False, context=ctx)
                                diff_amount_tax = currency_obj.compute(cr, uid,
                                    company_currency, current_currency, float(
                                        '%.*f' % (2, (credit_orig - credit_diff))),
                                    round=False, context=context)
                                acc_expense_voucher_id = inv_line_tax and inv_line_tax.tax_id and\
                                    inv_line_tax.tax_id.account_expense_voucher_id and\
                                    inv_line_tax.tax_id.account_expense_voucher_id.id or False
                                acc_income_voucher_id = inv_line_tax and inv_line_tax.tax_id and\
                                    inv_line_tax.tax_id.account_income_voucher_id and\
                                    inv_line_tax.tax_id.account_income_voucher_id.id or False
                                if credit_orig > credit_diff:
                                    if voucher.type == 'receipt':
                                        diff_account_id = acc_expense_voucher_id
                                    else:
                                        diff_account_id = acc_income_voucher_id
                                elif credit_orig < credit_diff:
                                    if voucher.type == 'receipt':
                                        diff_account_id = acc_income_voucher_id
                                    else:
                                        diff_account_id = acc_expense_voucher_id
                                        
                            # Aqui van las partidas nuevas
                            amount_tax_unround = amount_unround

                            if voucher.type in ('sale', 'receipt'):
                                account_tax_voucher = inv_line_tax.tax_id.account_collected_voucher_id.id
                            else:
                                account_tax_voucher = inv_line_tax.tax_id.account_paid_voucher_id.id

                            account_tax_collected = inv_line_tax.tax_id.account_collected_id.id

                            ctx['date'] = line.move_line_id.date
                            reference_amount = amount_unround
                            
                            move_lines_tax = self._preparate_move_line_tax(
                                cr, uid, account_tax_voucher, account_tax_collected, xmove_id, 
                                voucher.type, voucher.partner_id.id, voucher.period_id.id, voucher.journal_id.id, voucher.date, 
                                company_currency, reference_amount, amount_tax_unround, current_currency, inv_line_tax.tax_id.id, 
                                inv_line_tax.tax_id, 
                                inv_line_tax.account_analytic_id and inv_line_tax.account_analytic_id.id or False,
                                base_amount_curr,
                                factor, context=context)
                            
                            for move_line_tax in move_lines_tax:
                                move_create = move_line_obj.create(cr, uid, move_line_tax,
                                                        context=context)
                                move_ids.append(move_create)
        return move_ids


    # pylint: disable=W0622
    def _preparate_move_line_tax(self, cr, uid, src_account_id, dest_account_id,
                            move_id, type, partner, period, journal, date,
                            company_currency, reference_amount,
                            amount_tax_unround, reference_currency_id,
                            tax_id, line_tax, acc_a, amount_base_tax,  # informacion de lineas de impuestos
                            factor=0, context=None):
        if type == 'payment' or reference_amount < 0:
            src_account_id, dest_account_id = dest_account_id, src_account_id
        if type == 'payment' and reference_amount < 0:
            src_account_id, dest_account_id = dest_account_id, src_account_id

        amount_base, tax_secondary = self._get_base_amount_tax_secondary(cr,
                                    uid, line_tax,
                                    amount_base_tax * factor, reference_amount,
                                    context=context)
        debit_line_vals = {
            'name': line_tax.name,
            'quantity': 1,
            'partner_id': partner,
            'debit': abs(reference_amount),
            'credit': 0.0,
            'account_id': dest_account_id,
            'journal_id': journal,
            'period_id': period,
            'company_id': company_currency,
            'move_id': int(move_id),
            #'tax_id': tax_id,
            'analytic_account_id': acc_a,
            'date': date,
            #'tax_voucher_id': tax_id,
        }
        credit_line_vals = {
            'name': line_tax.name,
            'quantity': 1,
            'partner_id': partner,
            'debit': 0.0,
            'credit': abs(reference_amount),
            'account_id': src_account_id,
            'journal_id': journal,
            'period_id': period,
            'company_id': company_currency,
            'move_id': int(move_id),
            'amount_tax_unround': amount_tax_unround,
            #'tax_id': tax_id,
            'analytic_account_id': acc_a,
            'date': date,
            #'tax_voucher_id': tax_id,
        }

        if context.get('amount_voucher') and context.get('amount_voucher') < 0:
            debit_line_vals.update({'credit': debit_line_vals.get('debit', 0.0), 'debit': 0.0})
            credit_line_vals.update({'debit': credit_line_vals.get('credit', 0.0), 'credit': 0.0})

        if type in ('payment', 'purchase'):
            if reference_amount < 0:
                credit_line_vals.pop('analytic_account_id')
                credit_line_vals.update({
                    'amount_base': abs(amount_base),
                    'tax_id_secondary': tax_secondary})
            else:
                debit_line_vals.pop('analytic_account_id')
                debit_line_vals.update({
                    'tax_id_secondary': tax_secondary,
                    'amount_base': abs(amount_base)})
        else:
            if reference_amount < 0:
                debit_line_vals.pop('analytic_account_id')
                debit_line_vals.pop('tax_id_secondary')
            else:
                credit_line_vals.pop('analytic_account_id')

        if not amount_tax_unround:
            credit_line_vals.pop('amount_tax_unround')
            'tax_id' in credit_line_vals and credit_line_vals.pop('tax_id')
            'tax_id' in debit_line_vals and debit_line_vals.pop('tax_id')

        account_obj = self.pool.get('account.account')
        reference_amount = abs(reference_amount)
        src_acct, dest_acct = account_obj.browse(cr, uid, [src_account_id, dest_account_id], context=context)
        src_main_currency_id = src_acct.currency_id and src_acct.currency_id.id or src_acct.company_id.currency_id.id
        dest_main_currency_id = dest_acct.currency_id and dest_acct.currency_id.id or dest_acct.company_id.currency_id.id
        cur_obj = self.pool.get('res.currency')
        if reference_currency_id != src_main_currency_id:
            # fix credit line:
            credit_line_vals['credit'] = cur_obj.compute(cr, uid, reference_currency_id, src_main_currency_id, reference_amount, context=context)
            credit_line_vals['amount_tax_unround'] = cur_obj.compute(cr, uid, reference_currency_id, src_main_currency_id, abs(reference_amount), round=False, context=context)
            if (not src_acct.currency_id) or src_acct.currency_id.id == reference_currency_id:
                credit_line_vals.update(currency_id=reference_currency_id, amount_currency=-reference_amount)
        if reference_currency_id != dest_main_currency_id:
            # fix debit line:
            debit_line_vals['debit'] = cur_obj.compute(cr, uid, reference_currency_id, dest_main_currency_id, reference_amount, context=context)
            if (not dest_acct.currency_id) or dest_acct.currency_id.id == reference_currency_id:
                debit_line_vals.update(currency_id=reference_currency_id, amount_currency=reference_amount)

        return [debit_line_vals, credit_line_vals]

    def _get_base_amount_tax_secondary(self, cr, uid, line_tax,
                            amount_base_tax, reference_amount, context=None):
        amount_base = 0
        tax_secondary = False
        if line_tax and line_tax.tax_category_id and line_tax.tax_category_id.name in (
                'IVA', 'IVA-EXENTO', 'IVA-RET', 'IVA-PART'):
            amount_base = line_tax.tax_category_id.value_tax and\
                reference_amount / line_tax.tax_category_id.value_tax\
                or amount_base_tax
            tax_secondary = line_tax.id
        return [amount_base, tax_secondary]





class account_move_line(osv.Model):
    _inherit = 'account.move.line'

    def _get_query_round(self, cr, uid, ids, context=None):
        if context == None:
            context = {}
        cr.execute("""
                select account_id, sum(amount_tax_unround) as without,
                    case  when sum(credit) > 0.0
                        then sum(credit)
                    when sum(debit) > 0.0
                        then sum(debit)
                    end as round, id
                from account_move_line
                where move_id in (
                select move_id from account_move_line aml
                where id in %s)
                and amount_tax_unround is not null
                group by account_id, id
                order by id asc """, (tuple(ids),))
        dat = cr.dictfetchall()
        return dat

    # pylint: disable=W0622
    def reconcile(self, cr, uid, ids, type='auto', writeoff_acc_id=False, writeoff_period_id=False, writeoff_journal_id=False, context=None):
        res = super(account_move_line, self).reconcile(cr, uid, ids=ids,
        type='auto', writeoff_acc_id=writeoff_acc_id, writeoff_period_id=writeoff_period_id,
        writeoff_journal_id=writeoff_journal_id, context=context)
#        if not writeoff_acc_id:
        if context.get('apply_round', False):
            dat = []
        else:
            dat = self._get_query_round(cr, uid, ids, context=context)
        res_round = {}
        res_without_round = {}
        res_ids = {}

        for val_round in dat:
            res_round.setdefault(val_round['account_id'], 0)
            res_without_round.setdefault(val_round['account_id'], 0)
            res_ids.setdefault(val_round['account_id'], 0)
            res_round[val_round['account_id']] += val_round['round'] or 0.0
            res_without_round[val_round['account_id']] += val_round['without']
            res_ids[val_round['account_id']] = val_round['id']
        for res_diff_id in res_round.items():
            diff_val = abs(res_without_round[res_diff_id[0]]) - abs(res_round[res_diff_id[0]])
            diff_val = round(diff_val, 2)
            if diff_val != 0.00:
                move_diff_id = [res_ids[res_diff_id[0]]]
                for move in self.browse(cr, uid, move_diff_id, context=context):
                    move_line_ids = self.search(cr, uid, [('move_id', '=', move.move_id.id), ('tax_id', '=', move.tax_id.id)])
                    for diff_move in self.browse(cr, uid, move_line_ids, context=context):
                        if diff_move.debit == 0.0 and diff_move.credit:
                            self.write(cr, uid, [diff_move.id], {'credit': diff_move.credit + diff_val})
                        if diff_move.credit == 0.0 and diff_move.debit:
                            self.write(cr, uid, [diff_move.id], {'debit': diff_move.debit + diff_val})
        return res

    _columns = {
        'amount_tax_unround': fields.float('Amount tax undound', digits=(12, 16)),
        'tax_id': fields.many2one('account.voucher.line.tax', 'Tax'),
        'tax_voucher_id': fields.many2one('account.voucher.line.tax', 'Tax Voucher'),
    }


class account_voucher_line_tax(osv.Model):
    _name = 'account.voucher.line.tax'

    def _compute_balance(self, cr, uid, ids, name, args, context=None):
        res = {}

        for line_tax in self.browse(cr, uid, ids, context=context):
            tax_sum = 0.0
            old_ids = self.search(cr, uid, [('move_line_id', '=', line_tax.move_line_id.id), ('id', '!=', line_tax.id)])
            for lin_sum in self.browse(cr, uid, old_ids, context=context):
                tax_sum += lin_sum.amount_tax
            res[line_tax.id] = line_tax.original_tax - tax_sum
        return res

    def onchange_amount_tax(self, cr, uid, ids, amount, tax):
        res = {}
        res['value'] = {'amount_tax': amount, 'amount_tax_unround': amount, 'diff_amount_tax': abs(tax - amount)}
        return res

    _columns = {
        'tax_id': fields.many2one('account.tax', 'Tax'),
        'account_id': fields.many2one('account.account', 'Account'),
        'amount_tax': fields.float('Amount Tax', digits=(12, 16)),
        'amount_tax_unround': fields.float('Amount tax undound'),
        'original_tax': fields.float('Original Import Tax'),
        'tax': fields.float('Tax'),
        'balance_tax': fields.function(_compute_balance, type='float', string='Balance Import Tax', store=True, digits=(12, 6)),
        #~ 'balance_tax':fields.float('Balance Import Tax'),
        'diff_amount_tax': fields.float('Difference', digits_compute= dp.get_precision('Account')),
        'diff_account_id': fields.many2one('account.account', 'Account Diff'),
        'voucher_line_id': fields.many2one('account.voucher.line', 'Voucher Line'),
        'move_line_id': fields.many2one('account.move.line', 'Move'),
        'analytic_account_id': fields.many2one('account.analytic.account', 'Account Analytic'),
        'amount_base': fields.float('Amount Base')
    }

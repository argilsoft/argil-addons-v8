# -*- encoding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Argil Consulting (<http://argil.mx>).
#
#	 Coded by: Israel CA (israel.cruz@argil.mx)
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

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

from openerp.osv import fields, osv
from lxml import etree as et
from dateutil.relativedelta import relativedelta
import datetime

class voucher_fit(osv.osv):
    _inherit = 'account.voucher'
    _columns = {'partner_acc_id': fields.many2one('res.partner.bank', 'Cuenta'),
     'check_number': fields.char('N\xc3\xbamero de cheque', size=20),
     'cmpl_type': fields.char('Complement type', size=20)}

    def fields_view_get(self, cr, uid, view_id = None, view_type = 'form', context = None, toolbar = False, submenu = False):
        req = super(voucher_fit, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
        if self.pool.get('res.users').browse(cr, uid, uid).company_id.auto_mode_enabled:
            return req
        if view_type == 'form':
            view_arch = et.fromstring(req['arch'])
            max = -1
            for node in view_arch.getiterator('field'):
                if max > 1:
                    break
                if node.get('name') in ('check_number', 'partner_acc_id'):
                    node.attrib['invisible'] = '1'
                    node.attrib['modifiers'] = '{"invisible" : true}'
                    max += 1

            req['arch'] = et.tostring(view_arch, pretty_print=True)
        return req



    def onchange_journal(self, cr, uid, ids, journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id, context = None):
        res = super(voucher_fit, self).onchange_journal(cr, uid, ids, journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id, context)
        if journal_id:
            journal = self.pool.get('account.journal').browse(cr, uid, journal_id)
            res['value']['cmpl_type'] = journal.cmpl_type
            if journal.cmpl_type != 'check':
                res['value']['check_number'] = False
            if journal.cmpl_type == 'other':
                res['value']['partner_acc_id'] = False
        return res



    def action_move_line_create(self, cr, uid, ids, context = None):
        super(voucher_fit, self).action_move_line_create(cr, uid, ids, context)
        company = self.pool.get('res.users').browse(cr, uid, uid).company_id
        if not company.auto_mode_enabled:
            return True
        cmplObj = self.pool.get('eaccount.complements')
        cmplTypeObj = self.pool.get('eaccount.complement.types')
        for vc_id in ids:
            voucher = self.browse(cr, uid, vc_id)
            if not voucher.journal_id.cmpl_type:
                continue
            if voucher.journal_id.cmpl_type in ('transfer', 'check'):
                if not voucher.partner_acc_id.partner_id:
                    raise osv.except_osv(u'Informaci\xf3n faltante', u'La cuenta "%s" no tiene un beneficiario asignado.' % voucher.partner_acc_id.name_get()[0][1])
                if not voucher.partner_acc_id.partner_id.vat:
                    raise osv.except_osv(u'Informaci\xf3n faltante', u'"%s", beneficiario de la cuenta "%s", no tiene un R.F.C. configurado' % (voucher.partner_acc_id.partner_id.name, voucher.partner_acc_id.name_get()[0][1]))
                if voucher.type == 'receipt' and not voucher.journal_id.debit_cmpl_acc_id:
                    raise osv.except_osv(u'Informaci\xf3n faltante', u'No se ha definido una cuenta bancaria deudora para el diario "%s"' % voucher.journal_id.name)
                if voucher.type == 'payment' and not voucher.journal_id.credit_cmpl_acc_id:
                    raise osv.except_osv(u'Informaci\xf3n faltante', u'No se ha definido una cuenta bancaria acreedora para el diario "%s"' % voucher.journal_id.name)
                line_id = [ ln for ln in voucher.move_id.line_id if ln.account_id.type == 'liquidity' ]
                msg = u'No se ha encontrado una cuenta de tipo "liquidez" en el asiento contable del pago %s' % voucher.name
            elif voucher.journal_id.cmpl_type == 'payment':
                if not voucher.partner_id.vat:
                    if voucher.partner_id.supplier:
                        title = 'proveedor'
                    elif voucher.partner_id.customer:
                        title = 'cliente'
                    else:
                        title = 'registro'
                    raise osv.except_osv(u'Informaci\xf3n faltante', u'El %s %s no cuenta con un R.F.C., requerido para el complemento de contabilidad electr\xf3nica' % (title, voucher.partner_id.name))
                line_id = voucher.move_id.line_id
                msg = 'No se han encontrado asientos contables para adjuntar el complemento.'
            if not len(line_id):
                raise osv.except_osv(u'Informaci\xf3n faltante', msg)
            cmpl_vals = {'compl_currency_id': voucher.currency_id.id,
             'amount': voucher.amount,
             'compl_date': voucher.date,
             'type_id': cmplTypeObj.search(cr, uid, [('key', '=', voucher.journal_id.cmpl_type)])[0],
             'type_key': voucher.journal_id.cmpl_type}
            curr_rate = False
            rate_lines = [ rate for rate in voucher.currency_id.rate_ids if rate.name == voucher.date ]
            if len(rate_lines) and rate_lines[0].rate:
                curr_rate = 1 / rate_lines[0].rate
            else:
                rate_lines = [{'name':val.name,'rate':val.rate} for val in voucher.currency_id.rate_ids]
                rate_lines = sorted(rate_lines, reverse=True)
                for ln in rate_lines:
                    if ln['name'] < voucher.date and ln['rate']:
                        curr_rate = 1 / ln['rate']
                        break

            cmpl_vals['exchange_rate'] = curr_rate
            if cmpl_vals['type_key'] == 'check':
                cmpl_vals['check_number'] = voucher.check_number
            if voucher.type == 'receipt':
                cmpl_vals['payee_id'] = company.partner_id.id
                destiny_rfc = company.rfc
                if cmpl_vals['type_key'] != 'payment':
                    cmpl_vals['origin_native_accid'] = voucher.partner_acc_id.id
                    cmpl_vals['show_native_accs'] = True
                    origin_rfc = voucher.partner_acc_id.partner_id.vat[2:] if len(voucher.partner_acc_id.partner_id.vat) > 13 else voucher.partner_acc_id.partner_id.vat
                    origin_bank = voucher.partner_acc_id.bank
                    if cmpl_vals['type_key'] == 'transfer':
                        cmpl_vals['destiny_account_id'] = voucher.journal_id.credit_cmpl_acc_id.id
                        destiny_bank = voucher.journal_id.debit_cmpl_acc_id.bank_id
            elif voucher.type == 'payment':
                cmpl_vals['payee_id'] = voucher.partner_id.id
                if cmpl_vals['type_key'] == 'payment':
                    destiny_rfc = voucher.partner_id.vat[2:] if len(voucher.partner_id.vat) > 13 else voucher.partner_id.vat
                else:
                    destiny_rfc = voucher.partner_acc_id.partner_id.vat[2:] if len(voucher.partner_acc_id.partner_id.vat) > 13 else voucher.partner_acc_id.partner_id.vat
                    cmpl_vals['origin_account_id'] = voucher.journal_id.credit_cmpl_acc_id.id
                    origin_rfc = company.rfc
                    origin_bank = voucher.journal_id.credit_cmpl_acc_id.bank_id
                    if cmpl_vals['type_key'] == 'transfer':
                        cmpl_vals['destiny_native_accid'] = voucher.partner_acc_id.id
                        cmpl_vals['show_native_accs1'] = True
                        destiny_bank = voucher.partner_acc_id.bank
            cmpl_vals['rfc2'] = destiny_rfc
            cmpl_vals['move_line_id'] = line_id[0].id
            if cmpl_vals['type_key'] == 'payment':
                cmpl_vals['pay_method_id'] = voucher.journal_id.other_payment.id
            else:
                cmpl_vals['rfc'] = origin_rfc
                cmpl_vals['origin_bank_id'] = origin_bank.id
                cmpl_vals['origin_bank_key'] = origin_bank.sat_bank_id.bic
                if origin_bank.sat_bank_id.bic == '999':
                    cmpl_vals['origin_frgn_bank'] = origin_bank.name
                if cmpl_vals['type_key'] == 'transfer':
                    cmpl_vals['destiny_bank_id'] = destiny_bank.id
                    cmpl_vals['destiny_bank_key'] = destiny_bank.sat_bank_id.bic
                    if destiny_bank.sat_bank_id.bic == '999':
                        cmpl_vals['destiny_frgn_bank'] = destiny_bank.name
            cmplObj.create(cr, uid, cmpl_vals)
            voucher.move_id.write({'item_concept': company._assembly_concept(voucher.type, voucher=voucher)})

        return True



voucher_fit()


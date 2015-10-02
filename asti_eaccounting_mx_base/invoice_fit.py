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

class invoice_fit(osv.osv):
    _inherit = 'account.invoice'
    _columns = {'foreign_invoice': fields.char('No. factura extranjera', size=36)}

    def fields_view_get(self, cr, uid, view_id = None, view_type = 'form', context = None, toolbar = False, submenu = False):
        req = super(invoice_fit, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
        if self.pool.get('res.users').browse(cr, uid, uid).company_id.auto_mode_enabled:
            return req
        if view_type == 'form' and 'supplier' in req['name']:
            view_arch = et.fromstring(req['arch'])
            max = -1
            for node in view_arch.getiterator('field'):
                if max > 1:
                    break
                if node.get('name') == 'foreign_invoice':
                    node.attrib['invisible'] = '1'
                    node.attrib['modifiers'] = '{"invisible" : true}'
                    max += 1

            req['arch'] = et.tostring(view_arch, pretty_print=True)
        return req



    def action_move_create(self, cr, uid, ids, context = None):
        cmplsObj = self.pool.get('eaccount.complements')
        compl_type_id = self.pool.get('eaccount.complement.types').search(cr, uid, [('key', '=', 'foreign')])[0]
        super(invoice_fit, self).action_move_create(cr, uid, ids, context)
        invoices = self.browse(cr, uid, ids)
        company = self.pool.get('res.users').browse(cr, uid, uid).company_id
        if not company.auto_mode_enabled:
            return True
        for inv in invoices:
            if inv.type not in ('in_invoice', 'in_refund'):
                continue
            if inv.type == 'in_invoice':
                line_id = [ ln.id for ln in inv.move_id.line_id if ln.account_id.type == 'payable' ]
                msg = u'No se encontr\xf3 ning\xfan asiento con una cuenta de tipo "A pagar" en la p\xf3liza %s' % inv.move_id.name
            else:
                line_id = [ ln.id for ln in inv.move_id.line_id ]
                msg = u'No se encontraron asientos en la p\xf3liza %s' % inv.move_id.name
            if not len(line_id):
                raise osv.except_osv(u'Informaci\xf3n faltante', msg)
            cmpl_vals = {}
            if inv.foreign_invoice and inv.partner_id.type_of_third != '05':
                raise osv.except_osv(u'Incosistencia de informaci\xf3n', u'Se ha indicado una factura a extranjero, pero el tipo de tercero en la DIOT no corresponde.')
            if inv.foreign_invoice and not inv.partner_id.number_fiscal_id_diot:
                raise osv.except_osv(u'Informaci\xf3n faltante', u'Se necesita un ID fiscal para el complemento a extranjeros, verifique la configuraci\xf3n de la DIOT para este proveedor.')
            cmpl_vals['foreign_taxid'] = inv.partner_id.number_fiscal_id_diot
            cmpl_vals['foreign_invoice'] = inv.foreign_invoice
            if cmpl_vals['foreign_taxid'] and cmpl_vals['foreign_invoice']:
                cmpl_vals.update({'amount': inv.amount_total,
                 'compl_date': inv.date_invoice,
                 'compl_currency_id': inv.currency_id.id,
                 'type_key': 'foreign',
                 'type_id': compl_type_id,
                 'move_line_id': line_id[0]})
                curr_rate = False
                rate_lines = [ rate for rate in inv.currency_id.rate_ids if rate.name == inv.date_invoice ]
                if len(rate_lines) and rate_lines[0].rate:
                    curr_rate = 1 / rate_lines[0].rate
                else:
                    rate_lines = [{'name':val.name,'rate':val.rate} for val in inv.currency_id.rate_ids]
                    #rate_lines = sorted(rate_lines, reverse=True)
                    for ln in rate_lines:
                        if ln['name'] < inv.date_invoice and ln['rate']:
                            curr_rate = 1 / ln['rate']
                            break
                    
                    #inv.currency_id.rate_ids = sorted(inv.currency_id.rate_ids, key=lambda k: k.name, reverse=True)
                    #for ln in inv.currency_id.rate_ids:
                    #    if ln.name < inv.date_invoice and ln.rate:
                    #        curr_rate = 1 / ln.rate
                    #        break

                cmpl_vals['exchange_rate'] = str(curr_rate) if curr_rate else False
                cmplsObj.create(cr, uid, cmpl_vals)
            else:
                attObj = self.pool.get('ir.attachment')
                attachIds = attObj.search(cr, uid, [('name', 'ilike', '.xml'), ('res_model', '=', 'account.invoice'), ('res_id', '=', inv.id)])
                if len(attachIds):
                    cmplObj = self.pool.get('eaccount.complements')
                    user = self.pool.get('res.users').browse(cr, uid, uid)
                    attachment = attObj.browse(cr, uid, attachIds)[0]
                    cmpl_vals = cmplObj.onchange_attachment(cr, uid, [], attachment.datas, currency_id=inv.currency_id)['value']
                    if not inv.partner_id.vat:
                        raise osv.except_osv(u'Informaci\xf3n faltante', u'El proveedor %s no tiene configurado un R.F.C.' % inv.partner_id.name)
                    partner_vat = inv.partner_id.vat[2:] if len(inv.partner_id.vat) > 13 else inv.partner_id.vat
                    if partner_vat != cmpl_vals['rfc']:
                        raise osv.except_osv(u'Inconsistencia de datos', u'El RFC emisor ("%s") no coincide con el RFC del proveedor ("%s")' % (cmpl_vals['rfc'], partner_vat))
                    if user.company_id.rfc != cmpl_vals['rfc2']:
                        raise osv.except_osv(u'Inconsistencia de datos', u'El RFC receptor ("%s") no coincide con el RFC de la empresa ("%s")' % (cmpl_vals['rfc2'], user.company_id.rfc))
                    low = inv.amount_total - 0.1
                    upp = inv.amount_total + 0.1
                    if not low < cmpl_vals['amount'] < upp:
                        raise osv.except_osv(u'Inconsistencia de datos', u'El total del XML ("%s") est\xe1 fuera del rango de tolerancia ("%s" - "%s")' % (str(cmpl_vals['amount']), str(low), str(upp)))
                    cmpl_vals['type_id'] = self.pool.get('eaccount.complement.types').search(cr, uid, [('key', '=', 'cfdi')])[0]
                    cmpl_vals['type_key'] = 'cfdi'
                    cmpl_vals['move_line_id'] = line_id[0]
                    cmplObj.create(cr, uid, cmpl_vals)
            inv.move_id.write({'item_concept': company._assembly_concept(inv.type, invoice=inv)})

        return True



invoice_fit()


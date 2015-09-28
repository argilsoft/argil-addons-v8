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

class sf_invoicing_fit(osv.osv_memory):
    _inherit = 'ir.attachment.facturae.mx'

    def signal_sign(self, cr, uid, ids, context = None):
        res = super(sf_invoicing_fit, self).signal_sign(cr, uid, ids, context)
        if res:
            attObj = self.pool.get('ir.attachment')
            cfdi = self.browse(cr, uid, ids)[0]
            invoice_id = self.pool.get('account.invoice').browse(cr, uid, cfdi.invoice_id.id)
            line_id = [ ln.id for ln in invoice_id.move_id.line_id if ln.account_id.type == 'receivable' ]
            company = self.pool.get('res.users').browse(cr, uid, uid).company_id
            if not company.auto_mode_enabled:
                return res
            if len(line_id):
                attachIds = attObj.search(cr, uid, [('name', '=', invoice_id.fname_invoice + '.xml'),
                 ('datas_fname', '=', invoice_id.fname_invoice + '.xml'),
                 ('res_model', '=', 'account.invoice'),
                 ('res_id', '=', invoice_id.id)])
                if len(attachIds):
                    cmplObj = self.pool.get('eaccount.complements')
                    attachment = attObj.browse(cr, uid, attachIds)[0]
                    cmpl_vals = cmplObj.onchange_attachment(cr, uid, [], attachment.datas, currency_id=invoice_id.currency_id)['value']
                    cmpl_vals['type_id'] = self.pool.get('eaccount.complement.types').search(cr, uid, [('key', '=', 'cfdi')])[0]
                    cmpl_vals['type_key'] = 'cfdi'
                    cmpl_vals['move_line_id'] = line_id[0]
                    cmplObj.create(cr, uid, cmpl_vals)
                    invoice_id.move_id.write({'item_concept': company._assembly_concept(invoice_id.type, invoice=invoice_id)})
        return res



sf_invoicing_fit()


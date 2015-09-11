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

from lxml import etree as et
from openerp.osv import fields, osv
import base64

class account_fit(osv.osv):
    _inherit = 'account.account'
    _columns = {'sat_code_id': fields.many2one('sat.account.code', 'C\xc3\xb3digo agrupador SAT'),
     'take_for_xml': fields.boolean('Considerar para XML', help='Si esta casilla esta seleccionada,' + 'la cuenta ser\xc3\xa1 incluida en el cat\xc3\xa1logo de ' + 'cuentas generado para la contabilidad electr\xc3\xb3nica.'),
     'in_debt': fields.boolean('Deudora'),
     'in_cred': fields.boolean('Acreedora'),
     'first_period_id': fields.many2one('account.period', 'Primer per\xc3\xadodo reportado', help='Per\xc3\xadodo en que la cuenta fue reportada por primera vez ante el SAT. Ning\xc3\xban XML generado con un per\xc3\xadodo anterior incluir\xc3\xa1 esta cuenta.'),
     'rfc': fields.char('R.F.C.', size=15),
     'apply_in_check': fields.boolean('Cheque'),
     'apply_in_trans': fields.boolean('Transferencia'),
     'apply_in_cfdi': fields.boolean('Comp. nacional'),
     'apply_in_other': fields.boolean('Comp. otro'),
     'apply_in_forgn': fields.boolean('Comp. extranjero'),
     'apply_in_paymth': fields.boolean('M\xc3\xa9todo de pago'),
     'eaccount_account_ids': fields.one2many('eaccount.bank.account', 'account_id', 'Eaccounting bank accounts')}
    _defaults = {'take_for_xml': lambda *a: False,
     'in_debt': True}

    def ondebt_changed(self, cr, uid, ids, val):
        return {'value': {'in_debt': val,
                   'in_cred': not val}}



    def oncred_changed(self, cr, uid, ids, val):
        return {'value': {'in_debt': not val,
                   'in_cred': val}}



    def launch_period_chooser(self, cr, uid, ids, context):
        if self.pool.get('res.users').browse(cr, uid, uid).company_id._check_validity():
            raise osv.except_osv(u'Licenciamiento de contabilidad electr\xf3nica no v\xe1lido', u'\xbfHa cambiado sus datos de empresa recientemente?')
        if not len(context['active_ids']):
            raise osv.except_osv(u'Archivo vac\xedo', 'No hay cuentas disponibles para procesar.')
        return {'type': 'ir.actions.act_window',
         'res_model': 'period.chooser',
         'view_mode': 'form',
         'view_type': 'form',
         'target': 'new',
         'name': 'Contabilidad Electr\xc3\xb3nica - cat\xc3\xa1logo de cuentas',
         'context': {'active_ids': context['active_ids']}}



    def create(self, cr, uid, vals, context = None):
        accountsFlag = True
        if vals.get('rfc', False):
            accounts = vals.get('eaccount_account_ids', [])
            for acc in accounts:
                if acc[2]:
                    accountsFlag = False
                    break

            if accountsFlag:
                raise osv.except_osv(u'Datos incompletos', u'Al asignar un RFC debe asignar cuentas bancarias.')
        accountsFlag = False
        if 'eaccount_account_ids' in vals.keys():
            for acc in vals['eaccount_account_ids']:
                if acc[2]:
                    accountsFlag = True
                    break

            if accountsFlag and not vals.get('rfc', False):
                raise osv.except_osv(u'Datos incompletos', u'Al asignar un cuentas bancarias debe asignar un RFC.')
        return super(account_fit, self).create(cr, uid, vals, context)



account_fit()

class period_chooser(osv.osv_memory):
    _name = 'period.chooser'
    _columns = {'period_id': fields.many2one('account.period', 'Per\xc3\xadodo a generar', required=True)}

    def generate_xml(self, cr, uid, ids, context):
        form = self.browse(cr, uid, ids)[0]
        wizardObj = self.pool.get('files.generator.wizard')
        wizard_vals = {'xml_target': 'accounts_catalog',
         'month': form.period_id.date_start[5:7],
         'year': int(form.period_id.date_start[0:4])}
        wizId = wizardObj.create(cr, uid, wizard_vals)
        return wizardObj.process_file(cr, uid, [wizId], context, account_ids=context['active_ids'])



period_chooser()


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
from hashlib import sha1
from lxml import etree as et
import logging

class account_move_concept_template(osv.osv):
    _name = 'account.move.concept.template'
    _columns = {'move_type': fields.selection([('in_invoice', 'Factura de proveedor'),
                   ('out_invoice', 'Factura / Nota de cargo de cliente'),
                   ('out_refund', u'Nota de cr\xe9dito de cliente'),
                   ('payment', 'Pago de proveedor'),
                   ('receipt', 'Pago de cliente'),
                   ('out_refund', u'Nota de cr\xe9dito de proveedor')], string='Tipo de p\xc3\xb3liza', help='Elija el tipo de p\xc3\xb3liza para la cual aplicar esta plantilla. Solo puede haber una plantilla por tipo.', required=True),
     'concept': fields.text('Plantilla de concepto', help='Escriba la plantilla, considere que el l\xc3\xadmite m\xc3\xa1ximo son 300 caracteres una vez aplicado el formato.', required=True),
     'company_id': fields.many2one('res.company', 'Concept template ids', required=True)}
    _sql_constraints = [('unique_move_type', 'unique(move_type, company_id)', 'Solamente puede haber una plantilla por tipo de p\xc3\xb3liza en cada empresa.')]

account_move_concept_template()

class company_fit(osv.osv):
    _inherit = 'res.company'
    _columns = {'regname': fields.char('Raz\xc3\xb3n social', size=250, required=True),
     'rfc': fields.char('R.F.C.', size=15, required=True),
     'mobile_number': fields.char('M\xc3\xb3vil', size=50),
     'block': fields.char('Colonia', size=200),
     'accounts_config_done': fields.boolean('Accounts config done'),
     'license_key': fields.char('Clave de licenciamiento', size=40),
     'apply_in_check': fields.boolean('Cheque'),
     'apply_in_trans': fields.boolean('Transferencia'),
     'apply_in_cfdi': fields.boolean('Comp. nacional'),
     'apply_in_other': fields.boolean('Comp. otro'),
     'apply_in_forgn': fields.boolean('Comp. extranjero'),
     'apply_in_paymth': fields.boolean('M\xc3\xa9todo de pago'),
     'concept_template_ids': fields.one2many('account.move.concept.template', 'company_id', 'Concept template ids'),
     'auto_mode_enabled': fields.boolean('Modo autom\xc3\xa1tico (C.E.)', help='Marque esta casilla para proporcionar las caracter\xc3\xadsticas de automatizaci\xc3\xb3n en la contabilidad electr\xc3\xb3nica; se requiere una nueva clave de licenciamiento para activaci\xc3\xb3n.')}
    _defaults = {'regname': '',
     'rfc': ''}

    def _check_validity(self, cr, uid, ids, request = None):
		return False
        records = self.browse(cr, uid, ids)
        target = records[0] if len(records) else records
        if not target.name or not target.regname or not target.rfc:
            is_invalid = True
        else:
            val = u'ASTI-eAccounting' + target.name + (target.street if target.street else u'') + target.regname + target.rfc + u'-V1.2'
            if target.auto_mode_enabled:
                val += '-advanced-'
            is_invalid = sha1(val.encode('UTF-8')).hexdigest().lower() != target.license_key.lower() if target.license_key else True
        if request is None:
            return is_invalid
        if is_invalid:
            request['arch'] = '<form string="" version="7"><separator string="La licencia de uso no es v\xc3\xa1lida"/><h4>Compruebe que los campos "Nombre", "Raz\xc3\xb3n social" y "R.F.C." de la compa\xc3\xb1ia est\xc3\xa9n correctamente configurados y que la casilla de &quot;Modo autom\xc3\xa1tico (C.E.)&quot; corresponda con su configuraci\xc3\xb3n habitual.</h4><h4>\xc2\xbfHa cambiado su configuraci\xc3\xb3n de empresa recientemente?</h4></form>'
        return request



    def _assembly_concept(self, cr, uid, ids, mv_type, invoice = None, voucher = None):
        records = self.browse(cr, uid, ids)
        company = records[0] if len(records) else records
        if mv_type == 'in_invoice':
            move = 'facturas de proveedor'
        elif mv_type == 'out_invoice':
            move = 'facturas y notas de cargo de cliente'
        elif mv_type == 'out_refund':
            move = u'notas de cr\xe9dito de cliente'
        elif mv_type == 'payment':
            move = 'pagos de proveedor'
        elif mv_type == 'receipt':
            move = 'pagos de cliente'
        elif mv_type == 'out_refund':
            move = u'notas de cr\xe9dito de proveedor'
        templates = [ ln.concept for ln in company.concept_template_ids if ln.move_type == mv_type ]
        if len(templates):
            concept_parts = templates[0].split('___')
            if len(concept_parts) != 2:
                raise osv.except_osv(u'Plantilla de concepto err\xf3nea', u'Confirme que la plantilla para %s cuenta con argumentos.' % move)
            try:
                return concept_parts[0] % eval(concept_parts[1])
            except Exception as e:
                logging.getLogger(self._name).exception('Error evaluating concept template.')
                logging.getLogger(self._name).exception(e)
                raise osv.except_osv(u'Plantilla de concepto err\xf3nea', u'Confirme que la plantilla para %s cuenta con el formato requerido y que los campos especificados existen en el modelo.' % move)
        return False



    def fields_view_get(self, cr, uid, view_id = None, view_type = 'form', context = None, toolbar = False, submenu = False):
        req = super(company_fit, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
        if self.pool.get('res.users').browse(cr, uid, uid).company_id.auto_mode_enabled:
            return req
        if view_type == 'form':
            view_arch = et.fromstring(req['arch'])
            for node in view_arch.getiterator('group'):
                if node.attrib.get('string', '') == 'Plantillas para conceptos en p\xc3\xb3lizas':
                    node.attrib['invisible'] = '1'
                    node.attrib['modifiers'] = '{"invisible" : true}'
                    break

            req['arch'] = et.tostring(view_arch, pretty_print=True)
        return req



company_fit()


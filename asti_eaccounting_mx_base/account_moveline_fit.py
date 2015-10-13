from openerp.osv import fields, osv
from lxml import etree as et
import base64
import re
_RFC_PATTERN = re.compile('[A-Z\xc3\x91&]{3,4}[0-9]{2}[0-1][0-9][0-3][0-9][A-Z0-9]?[A-Z0-9]?[0-9A-Z]?')
_SERIES_PATTERN = re.compile('[A-Z]+')
_UUID_PATTERN = re.compile('[a-f0-9A-F]{8}-[a-f0-9A-F]{4}-[a-f0-9A-F]{4}-[a-f0-9A-F]{4}-[a-f0-9A-F]{12}')

class eaccount_complement_types(osv.osv):
    _name = 'eaccount.complement.types'
    _columns = {'key': fields.char('Key', size=20, required=True),
     'name': fields.char('Name', size=50, required=True),
     'allowed_in_helper': fields.boolean('Helper exlusive', required=True)}

eaccount_complement_types()

class eaccount_complements(osv.osv):
    _name = 'eaccount.complements'
    _description = 'Complementos para contabilidad electr\xc3\xb3nica'
    _columns = {'move_line_id': fields.many2one('account.move.line', 'Move line', ondelete='cascade'),
     'move_id': fields.many2one('account.move', 'Move', ondelete='cascade'),
     'file_data': fields.binary('Adjuntar'),
     'type_id': fields.many2one('eaccount.complement.types', 'Tipo ', help='Elija el tipo de complemento que desea anexar a la p\xc3\xb3liza.'),
     'type_key': fields.char('Type key', size=20),
     'origin_bank_key': fields.char('Origin bank key', size=10),
     'destiny_bank_key': fields.char('Destiny bank key', size=10),
     'show_native_accs': fields.boolean('Mostrar otras'),
     'origin_account_id': fields.many2one('eaccount.bank.account', 'Cuenta origen'),
     'origin_native_accid': fields.many2one('res.partner.bank', 'Cuenta origen (otros)'),
     'payee_id': fields.many2one('res.partner', 'Beneficiario (cliente / proveedor)'),
     'payee_acc_id': fields.many2one('account.account', 'Beneficiario (cta contable)'),
     'show_native_accs2': fields.boolean('Mostrar otras 2'),
     'destiny_account_id': fields.many2one('eaccount.bank.account', 'Cuenta destino'),
     'destiny_native_accid': fields.many2one('res.partner.bank', 'Cuenta destino (otros)'),
     'show_native_accs1': fields.boolean('Mostrar otras 1'),
     'origin_bank_id': fields.many2one('res.bank', 'Banco nacional (origen)'),
     'origin_frgn_bank': fields.char('Banco extranjero (origen)', size=150),
     'destiny_bank_id': fields.many2one('res.bank', 'Banco nacional (destino)'),
     'destiny_frgn_bank': fields.char('Banco extranjero (destino)', size=150),
     'uuid': fields.char('UuId', size=36),
     'amount': fields.float('Monto total'),
     'rfc': fields.char('R.F.C. origen', size=13),
     'rfc2': fields.char('R.F.C. destino', size=13),
     'compl_date': fields.date('Fecha'),
     'pay_method_id': fields.many2one('eaccount.payment.methods', 'M\xc3\xa9todo de pago'),
     'compl_currency_id': fields.many2one('res.currency', 'Moneda'),
     'exchange_rate': fields.float('Tipo de cambio'),
     'cbb_series': fields.char('Serie', size=10),
     'cbb_number': fields.float('No. folio', digits=(15, 0)),
     'foreign_invoice': fields.char('No. de factura', size=36),
     'foreign_taxid': fields.char('Contribuyente extranjero (tax id)', size=30),
     'check_number': fields.char('No. cheque', size=20)}
    _defaults = {'type_id': lambda *a: False}

    def onchange_type(self, cr, uid, ids, type_id):
        vals = {'uuid': False,
         'cbb_series': False,
         'cbb_number': False,
         'foreign_invoice': False,
         'type_key': False,
         'origin_account_id': False,
         'origin_native_accid': False,
         'show_native_accs': False,
         'rfc': False,
         'origin_bank_id': False,
         'origin_frgn_bank': False,
         'destiny_account_id': False,
         'destiny_native_accid': False,
         'show_native_accs1': False,
         'rfc2': False,
         'destiny_bank_id': False,
         'destiny_frng_bank': False,
         'payee_id': False,
         'payee_acc_id': False,
         'show_native_accs2': False,
         'foreign_tax_id': False,
         'check_number': False,
         'pay_method_id': False,
         'compl_currency_id': False,
         'exchange_rate': False}
        if type_id:
            complType = self.pool.get('eaccount.complement.types').browse(cr, uid, type_id)
            vals['type_key'] = complType.key
            user = self.pool.get('res.users').browse(cr, uid, uid)
            has_rate_silent = 'rate_silent' in user.company_id.currency_id._columns.keys()
            if user.company_id.currency_id:
                if complType.key == 'check' and user.company_id.apply_in_check:
                    vals['compl_currency_id'] = user.company_id.currency_id.id
                    vals['exchange_rate'] = user.company_id.currency_id.rate_silent if has_rate_silent else user.company_id.currency_id.rate
                elif complType.key == 'transfer' and user.company_id.apply_in_trans:
                    vals['compl_currency_id'] = user.company_id.currency_id.id
                    vals['exchange_rate'] = user.company_id.currency_id.rate_silent if has_rate_silent else user.company_id.currency_id.rate
                elif complType.key == 'cfdi' and user.company_id.apply_in_cfdi:
                    vals['compl_currency_id'] = user.company_id.currency_id.id
                    vals['exchange_rate'] = user.company_id.currency_id.rate_silent if has_rate_silent else user.company_id.currency_id.rate
                elif complType.key == 'other' and user.company_id.apply_in_other:
                    vals['compl_currency_id'] = user.company_id.currency_id.id
                    vals['exchange_rate'] = user.company_id.currency_id.rate_silent if has_rate_silent else user.company_id.currency_id.rate
                elif complType.key == 'foreign' and user.company_id.apply_in_forgn:
                    vals['compl_currency_id'] = user.company_id.currency_id.id
                    vals['exchange_rate'] = user.company_id.currency_id.rate_silent if has_rate_silent else user.company_id.currency_id.rate
                elif complType.key == 'payment' and user.company_id.apply_in_paymth:
                    vals['compl_currency_id'] = user.company_id.currency_id.id
                    vals['exchange_rate'] = user.company_id.currency_id.rate_silent if has_rate_silent else user.company_id.currency_id.rate
                if vals['exchange_rate']:
                    vals['exchange_rate'] = 1 / vals['exchange_rate']
        return {'value': vals}



    def onchange_bank(self, cr, uid, ids, bank_id, context):
        if bank_id:
            bank = self.pool.get('res.bank').browse(cr, uid, bank_id)
        bkey = bank.sat_bank_id.bic if bank_id else False
        vals = {'origin_bank_key': bkey} if context.get('is_origin', False) else {'destiny_bank_key': bkey}
        vals['origin_frgn_bank' if context.get('is_origin', False) else 'destiny_frgn_bank'] = bank.name if bkey == '999' else False
        return {'value': vals}



    def onchange_account(self, cr, uid, ids, acc_id, context):
        rfcKey = 'rfc' if context.get('is_origin', False) else 'rfc2'
        bankKey = 'origin_bank_id' if context.get('is_origin', False) else 'destiny_bank_id'
        payeeKey = 'payee_id' if context.get('is_native', False) else 'payee_acc_id'
        if acc_id:
            ormObj = self.pool.get('res.partner.bank' if context.get('is_native', False) else 'eaccount.bank.account')
            account = ormObj.browse(cr, uid, acc_id)
            partner_rfc = account.partner_id.vat if context.get('is_native', False) else account.account_id.rfc
            vals = {bankKey: account.bank.id if context.get('is_native', False) else account.bank_id.id}
            if partner_rfc:
                vals[rfcKey] = partner_rfc[2:] if len(partner_rfc) > 13 else partner_rfc
            if context.get('type_key', '') == 'transfer':
                vals[payeeKey] = account.partner_id.id if context.get('is_native') else account.account_id.id
                vals['show_native_accs2'] = not context.get('is_native', False)
            else:
                vals[payeeKey] = False
            vals['show_native_accs2'] = False
        else:
            vals = {rfcKey: False,
             bankKey: False,
             payeeKey: False,
             'show_native_accs2': False}
        return {'value': vals}



    def onchange_options(self, cr, uid, ids, selected, account, native_account, context):
        if selected:
            return self.onchange_account(cr, uid, ids, native_account, context)
        else:
            return self.onchange_account(cr, uid, ids, account, context)



    def onchange_payee(self, cr, uid, ids, payee_id, context):
        vals = {}
        if context.get('type_key', '') in ('payment', 'check'):
            ormObj = self.pool.get('res.partner' if context.get('is_native', False) else 'account.account')
            if payee_id:
                payee = ormObj.browse(cr, uid, payee_id)
                payee_rfc = payee.vat if context.get('is_native', False) else payee.rfc
                if payee_rfc:
                    vals['rfc2'] = payee_rfc[2:] if len(payee_rfc) > 13 else payee_rfc
            else:
                vals['rfc2'] = False
        elif context.get('type_key', '') == 'foreign':
            vals['rfc2'] = False
        return {'value': vals}



    def onchange_rfc(self, cr, uid, ids, rfc):
        if rfc and not _RFC_PATTERN.match(rfc):
            raise osv.except_osv(u'Verifique su informaci\xf3n', u'El R.F.C. "%s" no se apega a los lineamientos del SAT.' % rfc)
        return True



    def onchange_series(self, cr, uid, ids, series):
        if series and not _SERIES_PATTERN.match(series):
            raise osv.except_osv(u'Verifique su informaci\xf3n', u'La serie del comprobante solo puede contener letras de la A a la Z, sin incluir la \xd1.')
        return True



    def onchange_uuid(self, cr, uid, ids, uuid):
        if uuid and not _UUID_PATTERN.match(uuid):
            raise osv.except_osv(u'Verifique su informaci\xf3n', u'El UUID ingresado no se apega a los lineamientos del SAT.')
        return True



    def onchange_payee_opts(self, cr, uid, ids, selected, payee_id, payee_acc_id, context):
        if selected:
            return self.onchange_payee(cr, uid, ids, payee_acc_id, context)
        else:
            return self.onchange_payee(cr, uid, ids, payee_id, context)



    def onchange_attachment(self, cr, uid, ids, selected_file, currency_id = False):
        if selected_file:
            xml_data = base64.b64decode(selected_file)
            try:
                xmlTree = et.ElementTree(et.fromstring(xml_data))
            except:
                raise osv.except_osv('Formato de archivo incorrecto', u'Se necesita cargar un archivo de extensi\xf3n ".xml" (CFDI o CFD)')
            if 'cfdi:Comprobante' not in xml_data[0:100] and 'Comprobante' not in xml_data[0:100]:
                raise osv.except_osv('Archivo XML incorrecto', 'Se necesita cargar un archivo de tipo CFDI o CFD.')
            vals = {}
            if 'cfdi:Comprobante' in xml_data[0:100]:
                vouchNode = xmlTree.getroot()
                if vouchNode is None:
                    raise osv.except_osv(u'Estructura CFDI inv\xe1lida', u'No se encontr\xf3 el nodo "cfdi:Comprobante"')
                if 'total' not in vouchNode.attrib.keys() or 'fecha' not in vouchNode.attrib.keys():
                    raise osv.except_osv(u'Informaci\xf3n faltante', u'Compruebe que el CFDI tenga asignados los campos "total" y "fecha".')
                emitterNode = vouchNode.find('{http://www.sat.gob.mx/cfd/3}Emisor')
                if emitterNode is None:
                    raise osv.except_osv(u'Estructura CFDI inv\xe1lida', u'No se encontr\xf3 el nodo "cfdi:Emisor"')
                if 'rfc' not in emitterNode.attrib.keys():
                    raise osv.except_osv(u'Informaci\xf3n faltante', u'No se encontr\xf3 el RFC emisor.')
                receiverNode = vouchNode.find('{http://www.sat.gob.mx/cfd/3}Receptor')
                if receiverNode is None:
                    raise osv.except_osv(u'Estructura CFDI inv\xe1lida', u'No se encontr\xf3 el nodo "cfdi:Receptor"')
                if 'rfc' not in receiverNode.attrib.keys():
                    raise osv.except_osv(u'Informaci\xf3n faltante', u'No se encontr\xf3 el RFC receptor.')
                complNode = vouchNode.find('{http://www.sat.gob.mx/cfd/3}Complemento')
                if complNode is None:
                    raise osv.except_osv(u'Estructura CFDI inv\xe1lida', u'No se encontr\xf3 el nodo "cfdi:Complemento"')
                stampNode = complNode.find('{http://www.sat.gob.mx/TimbreFiscalDigital}TimbreFiscalDigital')
                if stampNode is None:
                    raise osv.except_osv(u'Estructura CFDI inv\xe1lida', u'No se encontr\xf3 el nodo "tfd:TimbreFiscalDigital"')
                if 'UUID' not in stampNode.attrib.keys():
                    raise osv.except_osv(u'Informaci\xf3n faltante', u'No se encontr\xf3 el UUID')
                if len(stampNode.attrib['UUID']) != 36:
                    raise osv.except_osv(u'Informaci\xf3n incorrecta', u'El UUID %s es incorrecto: se esperaban 36 caracteres, se encontraron %s' % (stampNode.attrib['UUID'], len(stampNode.attrib['UUID'])))
                vals['uuid'] = stampNode.attrib['UUID'].upper()
            else:
                vouchNode = xmlTree.getroot()
                if vouchNode is None:
                    raise osv.except_osv(u'Estructura CFD inv\xe1lida', u'No se encontr\xf3 el nodo "Comprobante"')
                if 'total' not in vouchNode.attrib.keys() or 'fecha' not in vouchNode.attrib.keys():
                    raise osv.except_osv(u'Informaci\xf3n faltante', u'Compruebe que el CFD tenga asignados los campos "total" y "fecha".')
                emitterNode = vouchNode.find('{http://www.sat.gob.mx/cfd/2}Emisor')
                if emitterNode is None:
                    raise osv.except_osv(u'Estructura CFD inv\xe1lida', u'No se encontr\xf3 el nodo "Emisor"')
                if 'rfc' not in emitterNode.attrib.keys():
                    raise osv.except_osv(u'Informaci\xf3n faltante', u'No se encontr\xf3 el RFC emisor.')
                receiverNode = vouchNode.find('{http://www.sat.gob.mx/cfd/2}Receptor')
                if receiverNode is None:
                    raise osv.except_osv(u'Estructura CFD inv\xe1lida', u'No se encontr\xf3 el nodo "Receptor"')
                if 'rfc' not in receiverNode.attrib.keys():
                    raise osv.except_osv(u'Informaci\xf3n faltante', u'No se encontr\xf3 el RFC receptor.')
            vals['compl_currency_id'] = currency_id.id if currency_id else False
            if 'TipoCambio' in vouchNode.attrib.keys():
                vals['exchange_rate'] = float(vouchNode.attrib['TipoCambio'])
            vals['cbb_series'] = vouchNode.attrib.get('serie', '')
            vals['cbb_number'] = int(vouchNode.attrib.get('folio', 0))
            vals['rfc'] = emitterNode.attrib['rfc']
            vals['rfc2'] = receiverNode.attrib['rfc']
            vals['compl_date'] = vouchNode.attrib['fecha'][0:10]
            vals['amount'] = float(vouchNode.attrib['total'])
            return {'value': vals}



eaccount_complements()

class account_moveline_fit(osv.osv):
    _inherit = 'account.move.line'
    _columns = {'complement_line_ids': fields.one2many('eaccount.complements', 'move_line_id', 'Complements')}

    def unlink(self, cr, uid, ids, context=None, check=True):
        if context is None:
            context = {}
        compl_obj = self.pool.get('eaccount.complements')
        for move_line in self.browse(cr, uid, ids, context=context):
            compl_obj.unlink(cr, uid, [compl_line.id for compl_line in move_line.complement_line_ids])
        result = super(account_moveline_fit, self).unlink(cr, uid, ids, context=context, check=check)
        return result
    
    
    def edit_eaccount_info(self, cr, uid, ids, context):
        line = self.browse(cr, uid, ids)[0] if len(ids) else self.browse(cr, uid, ids)
        ctx = context.copy()
        ctx['c_amount'] = line.credit or line.debit
        ctx['c_date'] = line.move_id.date
        new_wizard = self.pool.get('moveline.info.manager').create(cr, uid, {'line_id': ids[0]})
        return {'name': u'Informaci\xf3n para contabilidad electr\xf3nica',
         'type': 'ir.actions.act_window',
         'res_model': 'moveline.info.manager',
         'res_id': new_wizard,
         'view_mode': 'form',
         'view_type': 'form',
         'target': 'new',
         'context': ctx}



account_moveline_fit()


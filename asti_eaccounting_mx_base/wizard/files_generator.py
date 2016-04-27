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

from base64 import b64decode as b64dec, b64encode as b64enc
from openerp.osv import fields, osv
from lxml import etree as et
from M2Crypto import RSA, X509
from M2Crypto.EVP import MessageDigest
from StringIO import StringIO
from zipfile import ZipFile
import time
import os
from openerp import tools, release
import zipfile
import tempfile
import re
_RFC_PATTERN = re.compile('[A-Z\xc3\x91&]{3,4}[0-9]{2}[0-1][0-9][0-3][0-9][A-Z0-9]?[A-Z0-9]?[0-9A-Z]?')
_SERIES_PATTERN = re.compile('[A-Z]+')
_UUID_PATTERN = re.compile('[a-f0-9A-F]{8}-[a-f0-9A-F]{4}-[a-f0-9A-F]{4}-[a-f0-9A-F]{4}-[a-f0-9A-F]{12}')

class files_generator_wizard(osv.osv_memory):
    _name = 'files.generator.wizard'
    _columns = {'filename': fields.char('Filename', size=128),
     'primary_file': fields.binary('Primary file'),
     'stamped_file': fields.binary('Stamped file'),
     'zipped_file': fields.binary('Zipped file'),
     'format': fields.selection([('xml', 'XML'), ('pdf', 'PDF')], string='Formato del archivo', required=True),
     'xml_target': fields.selection([('accounts_catalog', 'Cat\xc3\xa1logo de cuentas'),
                    ('trial_balance', 'Balanza de comprobaci\xc3\xb3n'),
                    ('vouchers', 'Informaci\xc3\xb3n de p\xc3\xb3lizas'),
                    ('helpers', 'Auxiliar de folios')], string='Archivo a generar', required=True),
     'state': fields.selection([('init', 'Init'),
               ('val_xcpt', 'Val Except'),
               ('val_done', 'Val Done'),
               ('stamp_xcpt', 'Stamp Except'),
               ('stamp_done', 'Stamp Done'),
               ('zip_done', 'Zip done')], string='State'),
     'month': fields.selection([('01', 'Enero'),
               ('02', 'Febrero'),
               ('03', 'Marzo'),
               ('04', 'Abril'),
               ('05', 'Mayo'),
               ('06', 'Junio'),
               ('07', 'Julio'),
               ('08', 'Agosto'),
               ('09', 'Septiembre'),
               ('10', 'Octubre'),
               ('11', 'Noviembre'),
               ('12', 'Diciembre'),
               ('13', '-- Cierre --')], 'Periodo', required=True),
     'trial_delivery': fields.selection([('N', 'Normal'), ('C', 'Complementaria')], string='Tipo de env\xc3\xado', required=True),
     'trial_lastchange_date': fields.date('\xc3\x9altima modificaci\xc3\xb3n contable'),
     'request_type': fields.selection([('AF', 'Acto de fiscalizaci\xc3\xb3n'),
                      ('FC', 'Fiscalizaci\xc3\xb3n compulsa'),
                      ('DE', 'Devoluci\xc3\xb3n'),
                      ('CO', 'Compensaci\xc3\xb3n')], string='Tipo de solicitud', attrs={'required': [('xml_target', '=', 'vouchers')]}),
     'order_number': fields.char('N\xc3\xbamero de orden', size=13),
     'procedure_number': fields.char('N\xc3\xbamero de tr\xc3\xa1mite', size=10),
     'year': fields.integer('Ejercicio', required=True),
     'accounts_chart': fields.many2one('account.account', 'Plan contable', domain=[('parent_id', '=', False)])}
    _defaults = {'state': lambda *a: 'init',
     'format': lambda *a: 'xml',
     'xml_target': lambda *a: 'accounts_catalog',
     'year': lambda *a: int(time.strftime('%Y')),
     'trial_delivery': lambda *a: 'N',
     'request_type': lambda *a: 'DE'}
    _XSI_DECLARATION = 'http://www.w3.org/2001/XMLSchema-instance'
    _SAT_NS = {'xsi': _XSI_DECLARATION}
    _ACCOUNTS_CATALOG_URI = 'www.sat.gob.mx/esquemas/ContabilidadE/1_1/CatalogoCuentas'
    _TRIAL_BALANCE_URI = 'www.sat.gob.mx/esquemas/ContabilidadE/1_1/BalanzaComprobacion'
    _VOUCHERS_URI = 'www.sat.gob.mx/esquemas/ContabilidadE/1_1/PolizasPeriodo'
    _HELPERS_URI = 'www.sat.gob.mx/esquemas/ContabilidadE/1_1/AuxiliarFolios'
    _LETTER_PERIODS = {'01': 'Enero / ',
     '02': 'Febrero / ',
     '03': 'Marzo / ',
     '04': 'Abril / ',
     '05': 'Mayo / ',
     '06': 'Junio / ',
     '07': 'Julio / ',
     '08': 'Agosto / ',
     '09': 'Septiembre / ',
     '10': 'Octubre / ',
     '11': 'Noviembre / ',
     '12': 'Diciembre / '}

    def _outputXml(self, output):
        return et.tostring(output, pretty_print=True, xml_declaration=True, encoding='UTF-8')



    def _reopen_wizard(self, res_id):
        return {'type': 'ir.actions.act_window',
         'res_id': res_id,
         'view_mode': 'form',
         'view_type': 'form',
         'res_model': 'files.generator.wizard',
         'target': 'new',
         'name': 'Contabilidad electr\xc3\xb3nica'}



    def _xml_from_dict(self, node, namespaces, nsuri, parent = None):
        """
         Recursively builds an XML tree from a two elements tuple passed in the 'content' parameter.
        Consider that this method is prepared only to generate nodes, attributes and content in the
        form of child nodes; moreover, all the elements will be qualified using the specified nsuri
        and prefix. 
         Each element of that list represents a node or set of nodes that will be created. Each tuple
        contains two positions: 
        Position 0: tag of a new element to be created or the key word 'unroot' to indicate that no
                    new element is needed.
        Position 1: value for the element. This can either be a list of tuples or any other object. When
                    a list is found, content for the element will be created from it using recursive
                    calls to this method. When any other type is found, an attribute for the element 
                    will be created; if a string value is passed then the attribute is appended as-is,
                    otherwise a new string is created from the value and then used to append a new
                    attribute.
              
        Consider the following lines of code
        
        data = [
                ('root', [('at', 'val'), ('at1', 12),
                          ('el', [('at0', True), 
                                  ('subel0', [('at0', 'val0'), ('at01', 34.987)]),
                                  ('subel1', [('at1', -123), ('unroot', [
                                                                         ('child', [('at', 'val')])
                                                                        ]
                                                            )
                                            ]
                                )
                                ]
                          ),
                          ('el1', [('subel11', [('at0', False)])
                                   ('subel12', [
                                                ('child', [('at', 'val')])
                                               ])]
                          )
                        ]
                 )
            ]
                
        Applying the rules outlined above, the resulting XML generated by this method is
        
        <?xml version="1.0" coding="UTF-8"?>
            <root at="val" at1="12">
                <el at0="True">
                    <subel0 at0="val0" at01="34.987"/>
                    <subel1 at1="-123">
                        <child at="val"/>
                    </subel1>
                </el>
                <el1>
                    <subel11 at0="False"/>
                    <subel12>
                        <child1 at1="val1"/>
                    </subel12>
                </el1>
            </root>
        
        """
        attrs = {}
        attrs.update({elm[0]:elm[1] if type(elm[1]) in (str, unicode) else str(elm[1]) for elm in node[1] if not isinstance(elm[1], list)})
        children = [ elm for elm in node[1] if isinstance(elm[1], list) ]
        currNode = et.Element('{' + nsuri + '}' + node[0], attrib=attrs, nsmap=namespaces) if node[0] != 'unroot' else parent
        for chl in children:
            child = self._xml_from_dict(chl, namespaces, nsuri, currNode)
            if child is not currNode:
                currNode.append(child)

        return currNode



    def _validate_xml(self, cr, uid, schema, xmlTree, filename):
        validationResult = 'val_done'
        schema_path = self._find_file_in_addons('asti_eaccounting_mx_base/sat_xsd', schema)
        try:
            schema_file = open(schema_path, 'r')
        except IOError:
            raise osv.except_osv('Esquema XSD no encontrado', u'El esquema de validaci\xf3n de SAT no fue encontrado en la ruta "%s"' % schema_path[0:schema_path.find(schema)])
        schemaXml = et.parse(schema_file)
        try:
            schema = et.XMLSchema(schemaXml)
        except et.XMLSchemaParseError:
            if 'accounts_catalog' in schema_path:
                newLocation = schema_path.replace('accounts_catalog', 'complex_types')
            elif 'vouchers' in schema_path:
                newLocation = schema_path.replace('vouchers', 'complex_types')
            else:
                newLocation = schema_path.replace('helpers', 'complex_types')
            schemaXml.find('{http://www.w3.org/2001/XMLSchema}import').attrib['schemaLocation'] = newLocation
            try:
                schema = et.XMLSchema(schemaXml)
                validationResult = 'val_xcpt'
            except:
                schema = None
        if schema is None:
            raise osv.except_osv(u'Error al cargar esquema de validaci\xf3n', 'Por favor realize nuevamente el procesamiento del archivo.')
        try:
            schema.assertValid(xmlTree)
            return validationResult
        except et.DocumentInvalid as ex:
            error_haul = u'Los siguientes errores fueron encontrados:\n\n'
            error_haul += u'\n'.join([ u'L\xednea: %s\nTipo: %s\nMensaje: %s\n**********' % (err.line, err.type_name, err.message) for err in ex.error_log ])
            xsdhandler_id = self.pool.get('xsdvalidation.handler.wizard').create(cr, uid, {'error_file': b64enc(error_haul.encode('UTF-8')),
             'error_filename': 'errores.txt',
             'sample_xml': b64enc(self._outputXml(xmlTree)),
             'sample_xmlname': filename})
            return {'type': 'ir.actions.act_window',
             'res_model': 'xsdvalidation.handler.wizard',
             'res_id': xsdhandler_id,
             'view_mode': 'form',
             'view_type': 'form',
             'target': 'new',
             'name': 'La validaci\xc3\xb3n del archivo generado fall\xc3\xb3.'}



    def _find_file_in_addons(self, directory, filename):
        """To use this method, specify a filename and the directory where it resides.
        Said directory must be at the first level for the modules folders."""
        addons_paths = tools.config['addons_path'].split(',')
        actual_module = directory.split('/')[0]
        if len(addons_paths) == 1:
            return os.path.join(addons_paths[0], directory, filename)
        for pth in addons_paths:
            for subdir in os.listdir(pth):
                if subdir == actual_module:
                    return os.path.join(pth, directory, filename)


        return False



    def _verify_report_existance(self, cr, uid, report_name):
        """Pass the report name and search it in the database. An exception is raised if the report is not found."""
        report_ids = self.pool.get('ir.actions.report.xml').search(cr, uid, [('report_name', '=', report_name)])
        if not len(report_ids):
            raise osv.except_osv('Informe no encontrado', u'El informe seleccionado no se encuentra registrado en la base de datos. Verifique su configuraci\xf3n')



    def fields_view_get(self, cr, uid, view_id = None, view_type = 'form', context = None, toolbar = False, submenu = False):
        original_req = super(files_generator_wizard, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
        if context is None:
            context = {}
        if context.get('launched_from_menu', False):
            user = self.pool.get('res.users').browse(cr, uid, uid)
            return user.company_id._check_validity(original_req)
        return original_req



    def process_file(self, cr, uid, ids, context, account_ids = None, balance_ids = None, moveIds = None):
        form = self.browse(cr, uid, ids)[0]
        user = self.pool.get('res.users').browse(cr, uid, uid)
        if len(user.company_id.rfc) < 12 or len(user.company_id.rfc) > 13 or not _RFC_PATTERN.match(user.company_id.rfc):
            raise osv.except_osv(u'Datos de compa\xf1ia err\xf3neos', u'El RFC "%s" no es v\xe1lido con respecto a los lineamientos del SAT.' % user.company_id.rfc)
        if form.year < 2015:
            raise osv.except_osv('Fecha fuera de rango', 'La contabilidad electr\xc3\xb3nica comienza a reportarse a partir del 2015.')
        if not user.company_id.rfc:
            raise osv.except_osv(u'Informaci\xf3n faltante', 'No se ha configurado un R.F.C. para la empresa')
        periodObj = self.pool.get('account.period')
        period_ids = periodObj.search(cr, uid, [('code', '=', form.month + '/' + str(form.year)), ('company_id', '=', user.company_id.id)])
        if not len(period_ids):
            raise osv.except_osv(u'Informaci\xf3n faltante', u'El per\xedodo especificado no fue encontrado. Compruebe que los c\xf3digos de sus per\xedodos fiscales tienen el formato "mm/aaaa"')
        period_id = periodObj.browse(cr, uid, period_ids[0])
        if form.xml_target == 'accounts_catalog':
            accountObj = self.pool.get('account.account')
            if account_ids is None:
                account_ids = accountObj.search(cr, uid, [('take_for_xml', '=', True), ('company_id', '=', user.company_id.id)])
            if form.format == 'pdf':
                report_action = {'type': 'ir.actions.report.xml'}
                if tools.config['workers'] == 0:
                    self._verify_report_existance(cr, uid, 'jasper.ceCatalogosContables')
                    report_action['report_name'] = 'jasper.ceCatalogosContables'
                    report_action['datas'] = {'ids': account_ids,
                     'model': 'account.account',
                     'report_type': 'pdf',
                     'parameters': {'period': self._LETTER_PERIODS[form.month] + str(form.year),
                                    'rfc': user.company_id.rfc}}
                else:
                    report_action['report_name'] = 'rml.ceCatalogosContables'
                    report_action['datas'] = {'ids': account_ids,
                     'model': 'account.account',
                     'form': 'data'}
                    report_action['context'] = {'period': self._LETTER_PERIODS[form.month] + str(form.year),
                     'rfc': user.company_id.rfc}
                return report_action
            accounts = accountObj.browse(cr, uid, account_ids)
            ctas = []
            for acc in accounts:
                if not acc.sat_code_id:
                    raise osv.except_osv(u'Informaci\xf3n faltante', u'La cuenta %s no tiene asociado un c\xf3digo agrupador del SAT' % acc.name_get())
                if acc.first_period_id.date_start <= period_id.date_start:
                    ctaAttrs = [('CodAgrup', acc.sat_code_id.key),
                     ('NumCta', acc.code[0:100]),
                     ('Desc', acc.name[0:400]),
                     ('Nivel', acc.level + 1 if acc.level else 1),
                     ('Natur', 'A' if acc.in_cred else 'D')]
                    if acc.parent_id:
                        ctaAttrs.append(('SubCtaDe', acc.parent_id.code[0:100]))
                    ctas.append(('Ctas', ctaAttrs))

            if not len(ctas):
                raise osv.except_osv(u'Archivo vac\xedo', u'No se encontraron cuentas para XML cuyo primer per\xedodo reportado sea mayor o igual al per\xedodo procesado.')
            xml_content = ('Catalogo', [('Version', '1.1'),
              ('RFC', user.company_id.rfc),
              ('Mes', period_id.date_start[5:7]),
              ('Anio', period_id.date_start[0:4]),
              ('unroot', ctas)])
            catalog_ns = self._SAT_NS.copy()
            catalog_ns['catalogocuentas'] = self._ACCOUNTS_CATALOG_URI
            xmlTree = self._xml_from_dict(xml_content, catalog_ns, self._ACCOUNTS_CATALOG_URI)
            xmlTree.attrib['{{{pre}}}schemaLocation'.format(pre=self._XSI_DECLARATION)] = '%s http://www.sat.gob.mx/esquemas/ContabilidadE/1_1/CatalogoCuentas/CatalogoCuentas_1_1.xsd' % self._ACCOUNTS_CATALOG_URI
        elif form.xml_target == 'trial_balance':
            if form.format == 'pdf':
                self._verify_report_existance(cr, uid, 'jasper.ceBalanzaComprobacion')
            if balance_ids is None:
                trialWizardObj = self.pool.get('account.monthly_balance_wizard')
                trial_balance_id = trialWizardObj.create(cr, uid, 
                                                         {'chart_account_id': form.accounts_chart.id,
                                                         'company_id'       : user.company_id.id,
                                                         'period_id'        : period_id.id,
                                                         'partner_breakdown': False,
                                                         'output'           : 'list_view',
                                                                  })
                balance_ids = eval(trialWizardObj.get_info(cr, uid, [trial_balance_id])['domain'][1:-1])[2]
            balanceRecords = self.pool.get('account.monthly_balance').browse(cr, uid, balance_ids)
            if form.format == 'pdf':
                report_action = {'type': 'ir.actions.report.xml'}
                allowed_ids = [ rc.id for rc in balanceRecords if rc.account_id.take_for_xml and rc.account_id.first_period_id.date_start <= period_id.date_start if rc.account_id.company_id.id == user.company_id.id ]
                if tools.config['workers'] == 0:
                    report_action['report_name'] = 'jasper.ceBalanzaComprobacion'
                    report_action['datas'] = {'ids': allowed_ids,
                     'model': 'account.monthly_balance',
                     'report_type': 'pdf',
                     'parameters': {'period': self._LETTER_PERIODS[form.month] + str(form.year),
                                    'send_type': form.trial_delivery,
                                    'last_modified': form.trial_lastchange_date if form.trial_delivery == 'C' else '',
                                    'rfc': user.company_id.rfc}}
                else:
                    report_action['report_name'] = 'rml.ceBalanzaComprobacion'
                    report_action['datas'] = {'ids': allowed_ids,
                     'model': 'account.monthly_balance',
                     'form': 'data'}
                    report_action['context'] = {'period': self._LETTER_PERIODS[form.month] + str(form.year),
                     'send_type': form.trial_delivery,
                     'last_modified': form.trial_lastchange_date if form.trial_delivery == 'C' else '',
                     'rfc': user.company_id.rfc}
                return report_action
            ctas = []
            for record in balanceRecords:
                if record.account_id.take_for_xml and record.account_id.first_period_id.date_start <= period_id.date_start and record.account_id.company_id.id == user.company_id.id:
                    ctasAttrs = [('NumCta', record.account_code[0:100]),
                     ('SaldoIni', round(record.initial_balance, 2)),
                     ('Debe', round(record.debit, 2)),
                     ('Haber', round(record.credit, 2)),
                     ('SaldoFin', round(record.ending_balance, 2))]
                    ctas.append(('Ctas', ctasAttrs))

            if not len(ctas):
                raise osv.except_osv(u'Archivo vac\xedo', u'Ninguna cuenta de la balanza en este per\xedodo est\xe1 marcada para considerarse en el XML.')
            content = [('Version', '1.1'),
             ('RFC', user.company_id.rfc),
             ('Mes', form.month),#period_id.date_start[5:7]),
             ('Anio', period_id.date_start[0:4]),
             ('TipoEnvio', form.trial_delivery),
             ('unroot', ctas)]
            if form.trial_delivery == 'C':
                content.append(('FechaModBal', form.trial_lastchange_date))
            trialBalance_ns = self._SAT_NS.copy()
            trialBalance_ns['BCE'] = self._TRIAL_BALANCE_URI
            xmlTree = self._xml_from_dict(('Balanza', content), trialBalance_ns, self._TRIAL_BALANCE_URI)
            xmlTree.attrib['{{{pre}}}schemaLocation'.format(pre=self._XSI_DECLARATION)] = '%s http://www.sat.gob.mx/esquemas/ContabilidadE/1_1/BalanzaComprobacion/BalanzaComprobacion_1_1.xsd' % self._TRIAL_BALANCE_URI
        elif form.xml_target in ('vouchers', 'helpers'):
            if form.format == 'pdf':
                raise osv.except_osv('Informe no disponible', u'La representaci\xf3n impresa no est\xe1 definida para las p\xf3lizas.')
            if form.request_type in ('AF', 'FC'):
                if len(form.order_number) != 13:
                    raise osv.except_osv(u'N\xfamero de orden err\xf3neo', u'Verifique que su n\xfamero de orden contenga 13 caracteres (incluida la diagonal)')
                if not re.compile('[A-Z]{3}[0-6][0-9][0-9]{5}(/)[0-9]{2}').match(form.order_number.upper()):
                    raise osv.except_osv(u'N\xfamero de orden err\xf3neo', u'Verifique que su n\xfamero de orden tenga la siguiente estructura:\n  ' + u'  * Tres letras may\xfasculas de la A al Z sin incluir la "\xd1"\n' + u'  * Un d\xedgito entre 0 y 6\n' + u'  * Un d\xedgito entre 0 y 9\n' + u'  * Cinco d\xedgitos entre 0 y 9\n' + u'  * Una diagonal "/"\n' + u'  * Dos d\xedgitos del entre 0 y 9')
            if form.request_type in ('DE', 'CO'):
                if len(form.procedure_number) != 10 or not re.compile('[0-9]{10}').match(form.procedure_number):
                    raise osv.except_osv(u'N\xfamero de tr\xe1mite err\xf3neo', u'Verifique que su n\xfamero de tr\xe1mite contenga 10 d\xedgitos.')
            accountMoveObj = self.pool.get('account.move')
            if moveIds is None:
                moveIds = accountMoveObj.search(cr, uid, [('period_id', '=', period_id.id), ('state', '=', 'posted'), ('company_id', '=', user.company_id.id)])
            if form.format == 'pdf':
                return {}
            moves = accountMoveObj.browse(cr, uid, moveIds)
            if not len(moves):
                raise osv.except_osv(u'Informaci\xf3n faltante', u'No se han encontrado p\xf3lizas para el per\xedodo seleccionado.')
            entries = []
            if form.xml_target == 'vouchers':
                for mv in moves:
                    voucher = (mv.ref if mv.ref else '') + '(' + mv.name + ')'
                    if not len(mv.line_id):
                        raise osv.except_osv(u'P\xf3liza incompleta', u'La p\xf3liza %s no tiene asientos definidos.' % voucher)
                    if not mv.item_concept:
                        raise osv.except_osv(u'Informaci\xf3n faltante', u'La p\xf3liza %s no tiene definido un concepto' % voucher)
                    mvAttrs = [('NumUnIdenPol', mv.name[0:50]), ('Fecha', mv.date), ('Concepto', mv.item_concept[0:300])]
                    lines = []
                    for ln in mv.line_id:
                        if not ln.name:
                            raise osv.except_osv(u'Informaci\xf3n faltante', u'Compruebe que todos los asientos de la p\xf3liza %s tengan un concepto definido.' % voucher)
                        lnAttrs = [('NumCta', ln.account_id.code[0:100]),
                         ('DesCta', ln.account_id.name[0:100]),
                         ('Concepto', ln.name[0:200]),
                         ('Debe', round(ln.debit, 2)),
                         ('Haber', round(ln.credit, 2))]
                        (cfdis, others, foreigns, checks, transfers, payments,) = ([],
                         [],
                         [],
                         [],
                         [],
                         [])
                        for cmpl in ln.complement_line_ids:
                            if cmpl.rfc and not _RFC_PATTERN.match(cmpl.rfc):
                                raise osv.except_osv(u'Informaci\xf3n incorrecta', u'El RFC "%s" no es v\xe1lido con respecto a los lineamientos del SAT. P\xf3liza %s' % (cmpl.rfc, voucher))
                            if cmpl.rfc2 and not _RFC_PATTERN.match(cmpl.rfc2):
                                raise osv.except_osv(u'Informaci\xf3n incorrecta', u'El RFC "%s" no es v\xe1lido con respecto a los lineamientos del SAT. P\xf3liza %s' % (cmpl.rfc2, voucher))
                            cmpl_attrs = []
                            commons = ['cfdi', 'foreign', 'other']
                            cmpl_attrs.append(('MontoTotal' if cmpl.type_key in commons else 'Monto', round(cmpl.amount, 2)))
                            if cmpl.compl_currency_id:
                                if not cmpl.compl_currency_id.sat_currency_id:
                                    raise osv.except_osv(u'Informaci\xf3n faltante', u'La moneda "%s" no tiene asignado un c\xf3digo del SAT.' % cmpl.compl_currency_id.name)
                                cmpl_attrs.append(('Moneda', cmpl.compl_currency_id.sat_currency_id.code))
                            if cmpl.exchange_rate:
                                cmpl_attrs.append(('TipCamb', round(cmpl.exchange_rate, 5)))
                            commons.pop(1)
                            commons.append('check')
                            commons.append('transfer')
                            if cmpl.type_key in commons:
                                if cmpl.rfc and cmpl.rfc2 and cmpl.rfc != user.company_id.rfc and cmpl.rfc2 != user.company_id.rfc:
                                    cmpl_attrs.append(('RFC', cmpl.rfc2.upper()))
                                else:
                                    cmpl_attrs.append(('RFC', cmpl.rfc.upper() if cmpl.rfc != user.company_id.rfc else cmpl.rfc2.upper()))
                            commons.pop(0)
                            commons.pop(0)
                            if cmpl.type_key in commons:
                                if cmpl.show_native_accs and cmpl.origin_native_accid:
                                    cmpl_attrs.append(('CtaOri', cmpl.origin_native_accid.acc_number[0:50]))
                                elif cmpl.origin_account_id:
                                    cmpl_attrs.append(('CtaOri', cmpl.origin_account_id.code[0:50]))
                            commons.append('payment')
                            if cmpl.type_key in commons:
                                cmpl_attrs.append(('Fecha', cmpl.compl_date))
                                cmpl_attrs.append(('Benef', cmpl.payee_acc_id.name[0:300] if cmpl.show_native_accs2 else cmpl.payee_id.name[0:300]))
                            if cmpl.type_key == 'cfdi':
                                if cmpl.uuid:
                                    if len(cmpl.uuid) != 36 or not _UUID_PATTERN.match(cmpl.uuid.upper()):
                                        raise osv.except_osv(u'Informaci\xf3n incorrecta', u'El UUID "%s" en la p\xf3liza %s no se apega a los lineamientos del SAT.' % (cmpl.uuid, voucher))
                                    cmpl_attrs.append(('UUID_CFDI', cmpl.uuid.upper()))
                                cfdis.append(('CompNal', cmpl_attrs))
                            elif cmpl.type_key == 'other':
                                if cmpl.cbb_series and not _SERIES_PATTERN.match(cmpl.cbb_series):
                                    raise osv.except_osv(u'Informaci\xf3n incorrecta', u'La "Serie" en el comprobante de la p\xf3liza %s solo debe contener letras.' % voucher)
                                if cmpl.cbb_series:
                                    cmpl_attrs.append(('CFD_CBB_Serie', cmpl.cbb_series))
                                cmpl_attrs.append(('CFD_CBB_NumFol', cmpl.cbb_number))
                                others.append(('CompNalOtr', cmpl_attrs))
                            elif cmpl.type_key == 'foreign':
                                cmpl_attrs.append(('NumFactExt', cmpl.foreign_invoice))
                                cmpl_attrs.append(('TaxID', cmpl.foreign_taxid))
                                foreigns.append(('CompExt', cmpl_attrs))
                            elif cmpl.type_key == 'check':
                                if not cmpl.check_number:
                                    raise osv.except_osv(u'Informaci\xf3n faltante', u'No se ha encontrado un n\xfamero de cheque en la p\xf3liza % s' % voucher)
                                cmpl_attrs.append(('Num', cmpl.check_number))
                                cmpl_attrs.append(('BanEmisNal', cmpl.origin_bank_id.sat_bank_id.bic))
                                if cmpl.origin_bank_id.sat_bank_id.bic == '999':
                                    cmpl_attrs.append(('BanEmisExt', cmpl.origin_frgn_bank))
                                checks.append(('Cheque', cmpl_attrs))
                            elif cmpl.type_key == 'transfer':
                                cmpl_attrs.append(('BancoOriNal', cmpl.origin_bank_id.sat_bank_id.bic))
                                if cmpl.origin_bank_id.sat_bank_id.bic == '999':
                                    cmpl_attrs.append(('BancoOriExt', cmpl.origin_bank_id.name[0:150]))
                                cmpl_attrs.append(('CtaDest', cmpl.destiny_native_accid.acc_number[0:50] if cmpl.show_native_accs1 else cmpl.destiny_account_id.code[0:50]))
                                cmpl_attrs.append(('BancoDestNal', cmpl.destiny_bank_id.sat_bank_id.bic))
                                if cmpl.destiny_bank_id.sat_bank_id.bic == '999':
                                    cmpl_attrs.append(('BancoDestExt', cmpl.destiny_frgn_bank))
                                transfers.append(('Transferencia', cmpl_attrs))
                            elif cmpl.type_key == 'payment':
                                cmpl_attrs.append(('MetPagoPol', cmpl.pay_method_id.code))
                                cmpl_attrs.append(('RFC', cmpl.rfc2.upper()))
                                payments.append(('OtrMetodoPago', cmpl_attrs))

                        if len(cfdis):
                            lnAttrs.append(('unroot', cfdis))
                        if len(others):
                            lnAttrs.append(('unroot', others))
                        if len(foreigns):
                            lnAttrs.append(('unroot', foreigns))
                        if len(checks):
                            lnAttrs.append(('unroot', checks))
                        if len(transfers):
                            lnAttrs.append(('unroot', transfers))
                        if len(payments):
                            lnAttrs.append(('unroot', payments))
                        lines.append(('Transaccion', lnAttrs))

                    mvAttrs.append(('unroot', lines))
                    entries.append(('Poliza', mvAttrs))

            else:
                for mv in moves:
                    if not len(mv.complement_line_ids):
                        continue
                    voucher = (mv.ref if mv.ref else '') + '(' + mv.name + ')'
                    if not mv.name or mv.name == '/':
                        raise osv.except_osv(u'Informaci\xf3n faltante', u'La p\xf3liza %s no tiene un n\xfamero definido.' % voucher)
                    if not mv.date:
                        raise osv.except_osv(u'Informaci\xf3n faltante', u'La p\xf3liza %s no tiene una fecha definida.' % voucher)
                    mvAttrs = [('NumUnIdenPol', mv.name), ('Fecha', mv.date)]
                    (cfdis, others, foreigns,) = ([], [], [])
                    for cmpl in mv.complement_line_ids:
                        cmpl_attrs = [('MontoTotal', round(cmpl.amount, 2))]
                        if cmpl.rfc:
                            if not _RFC_PATTERN.match(cmpl.rfc):
                                raise osv.except_osv(u'Informaci\xf3n incorrecta', u'El RFC "%s" no es v\xe1lido con respecto a los lineamientos del SAT. P\xf3liza %s' % (cmpl.rfc, voucher))
                            cmpl_attrs.append(('RFC', cmpl.rfc))
                        if cmpl.compl_currency_id:
                            if not cmpl.compl_currency_id.sat_currency_id:
                                raise osv.except_osv(u'Informaci\xf3n faltante', u'La moneda "%s" no tiene asignado un c\xf3digo del SAT.' % cmpl.compl_currency_id.name)
                            cmpl_attrs.append(('Moneda', cmpl.compl_currency_id.sat_currency_id.code))
                        if cmpl.exchange_rate:
                            cmpl_attrs.append(('TipCamb', round(1 / cmpl.exchange_rate, 5)))
                        if cmpl.pay_method_id:
                            cmpl_attrs.append(('MetPagoAux', cmpl.pay_method_id.code))
                        if cmpl.type_key == 'cfdi':
                            if cmpl.uuid:
                                if len(cmpl.uuid) != 36 or not _UUID_PATTERN.match(cmpl.uuid.upper()):
                                    raise osv.except_osv(u'Informaci\xf3n incorrecta', u'El UUID "%s" en la p\xf3liza %s no se apega a los lineamientos del SAT.' % (cmpl.uuid, voucher))
                            cmpl_attrs.append(('UUID_CFDI', cmpl.uuid.upper()))
                            cfdis.append(('ComprNal', cmpl_attrs))
                        elif cmpl.type_key == 'other':
                            if cmpl.cbb_series:
                                cmpl_attrs.append(('CFD_CBB_Serie', cmpl.cbb_series))
                            cmpl_attrs.append(('CFD_CBB_NumFol', cmpl.cbb_number))
                            others.append(('ComprNalOtr', cmpl_attrs))
                        else:
                            if cmpl.foreign_taxid:
                                cmpl_attrs.append(('TaxID', cmpl.foreign_taxid))
                            cmpl_attrs.append(('NumFactExt', cmpl.foreign_invoice))
                            foreigns.append(('ComprExt', cmpl_attrs))

                    if len(cfdis):
                        mvAttrs.append(('unroot', cfdis))
                    if len(others):
                        mvAttrs.append(('unroot', others))
                    if len(foreigns):
                        mvAttrs.append(('unroot', foreigns))
                    entries.append(('DetAuxFol', mvAttrs))

                if not len(entries):
                    raise osv.except_osv(u'Auxiliar vac\xedo', u'No se encontraron p\xf3lizas que tengan complementos auxiliares relacionados.')
            content = [('Version', '1.1' if form.xml_target == 'vouchers' else '1.2'),
             ('RFC', user.company_id.rfc),
             ('Mes', period_id.date_start[5:7]),
             ('Anio', period_id.date_start[0:4]),
             ('TipoSolicitud', form.request_type),
             ('unroot', entries)]
            if form.request_type in ('AF', 'FC'):
                content.append(('NumOrden', form.order_number.upper()))
            if form.request_type in ('DE', 'CO'):
                content.append(('NumTramite', form.procedure_number))
            target_ns = self._SAT_NS.copy()
            if form.xml_target == 'vouchers':
                target_ns['PLZ'] = self._VOUCHERS_URI
                xmlTree = self._xml_from_dict(('Polizas', content), target_ns, self._VOUCHERS_URI)
                xmlTree.attrib['{{{pre}}}schemaLocation'.format(pre=self._XSI_DECLARATION)] = '%s http://www.sat.gob.mx/esquemas/ContabilidadE/1_1/PolizasPeriodo/PolizasPeriodo_1_1.xsd' % self._VOUCHERS_URI
            else:
                target_ns['RepAux'] = self._HELPERS_URI
            xmlTree = self._xml_from_dict(('RepAuxFol', content), target_ns, self._HELPERS_URI)
            xmlTree.attrib['{{{pre}}}schemaLocation'.format(pre=self._XSI_DECLARATION)] = '%s http://www.sat.gob.mx/esquemas/ContabilidadE/1_1/AuxiliarFolios/AuxiliarFolios_1_1.xsd' % self._HELPERS_URI
        filename = self.pool.get('res.users').browse(cr, uid, uid).company_id.rfc + str(form.year) + form.month
        if form.xml_target == 'accounts_catalog':
            filename += 'CT'
        elif form.xml_target == 'trial_balance':
            filename += 'B' + form.trial_delivery
        elif form.xml_target == 'vouchers':
            filename += 'PL'
        elif form.xml_target == 'helpers':
            filename += 'XF'
        filename += '.xml'
        validationResult = self._validate_xml(cr, uid, form.xml_target + '.xsd', xmlTree, filename)
        if isinstance(validationResult, dict):
            return validationResult
        self.write(cr, uid, ids, {'state': validationResult,
         'filename': filename,
         'primary_file': b64enc(self._outputXml(xmlTree))})
        return self._reopen_wizard(ids[0])



    def do_stamp(self, cr, uid, ids, context):
        if context is None:
            context = {}
        form = self.browse(cr, uid, ids)[0]
        stamp_res = 'stamp_done'
        xslt_path = self._find_file_in_addons('asti_eaccounting_mx_base/sat_xslt', form.xml_target + '.xslt')
        try:
            xslt_file = open(xslt_path, 'r')
        except:
            raise osv.except_osv('Hoja XSLT no encontrada', u'La hoja de transformaci\xf3n no fue encontrada en la ruta "%s"' % xslt_path)
        xsltTree = et.parse(xslt_file)
        xsltTree.find('{http://www.w3.org/1999/XSL/Transform}output').attrib['omit-xml-declaration'] = 'yes'
        try:
            xslt = et.XSLT(xsltTree)
        except et.XSLTParseError:
            xsltTree.find('{http://www.w3.org/1999/XSL/Transform}include').attrib['href'] = xslt_path.replace(form.xml_target, 'utils')
            try:
                xslt = et.XSLT(xsltTree)
                stamp_res = 'stamp_xcpt'
            except:
                xslt = None
        if xslt is None:
            raise osv.except_osv('Error al cargar la hoja XSLT', 'Por favor intente sellar de nuevo el documento.')
        xmlTree = et.ElementTree(et.fromstring(b64dec(form.primary_file)))
        transformedDocument = str(xslt(xmlTree))
        user = self.pool.get('res.users').browse(cr, uid, uid)
        ##########
        certificate_obj = self.pool.get('res.company.facturae.certificate')
        certificate_ids = certificate_obj.search(cr, uid, [
                ('company_id', '=', user.company_id.id),
                ('date_start', '<=', time.strftime('%Y-%m-%d')),
                ('date_end', '>=', time.strftime('%Y-%m-%d')),
                ('active', '=', True),
            ], limit=1)
        certificate_id = certificate_ids and certificate_ids[0] or False
        if not certificate_id:
            raise osv.except_osv(u'Informaci\xf3n faltante', u'No se ha encontrado una configuraci\xf3n de certificados disponible para la compa\xf1\xeda %s' % user.company_id.name)
        #########
        #allConfiguredCerts = user.company_id._get_current_certificate(cr, uid, [user.company_id.id], context=ctx)
        #allConfiguredCerts = user.company_id.certificate_id.id
        #print "allConfiguredCerts: ", allConfiguredCerts
        #if user.company_id.id not in allConfiguredCerts.keys() or not allConfiguredCerts[user.company_id.id]:
        #    raise osv.except_osv(u'Informaci\xf3n faltante', u'No se ha encontrado una configuraci\xf3n de certificados disponible para la compa\xf1\xeda %s' % user.company_id.name)
        #eCert = self.pool.get('res.company.facturae.certificate').browse(cr, uid, [allConfiguredCerts[user.company_id.id]])[0]        
        ##########
        eCert = self.pool.get('res.company.facturae.certificate').browse(cr, uid, [certificate_id])[0]
        ##########
        if not eCert.certificate_key_file_pem:
            raise osv.except_osv(u'Informaci\xf3n faltante', 'Se necesita una clave en formato PEM para poder sellar el documento')
        crypter = RSA.load_key_string(b64dec(eCert.certificate_key_file_pem))
        algrthm = MessageDigest('sha1')
        algrthm.update(transformedDocument)
        rawStamp = crypter.sign(algrthm.digest(), 'sha1')
        certHexNum = X509.load_cert_string(b64dec(eCert.certificate_file_pem), X509.FORMAT_PEM).get_serial_number()
        certNum = ('%x' % certHexNum).replace('33', 'B').replace('3', '')
        cert = ''.join([ ln for ln in b64dec(eCert.certificate_file_pem).split('\n') if 'CERTIFICATE' not in ln ])
        target = '{'
        if form.xml_target == 'accounts_catalog':
            target += self._ACCOUNTS_CATALOG_URI + '}Catalogo'
        elif form.xml_target == 'trial_balance':
            target += self._TRIAL_BALANCE_URI + '}Balanza'
        xmlTree.getroot().attrib['Sello'] = b64enc(rawStamp)
        xmlTree.getroot().attrib['noCertificado'] = certNum
        xmlTree.getroot().attrib['Certificado'] = cert
        validationResult = self._validate_xml(cr, uid, form.xml_target + '.xsd', xmlTree, form.filename)
        if isinstance(validationResult, dict):
            return validationResult
        self.write(cr, uid, ids, {'state': stamp_res,
         'stamped_file': b64enc(self._outputXml(xmlTree))})
        return self._reopen_wizard(ids[0])



    def do_zip(self, cr, uid, ids, context):
        form = self.browse(cr, uid, ids)[0]
        (descriptor, zipname,) = tempfile.mkstemp('eaccount_', '__asti_')
        zipDoc = ZipFile(zipname, 'w')
        xmlContent = b64dec(form.stamped_file) if form.stamped_file else b64dec(form.primary_file)
        zipDoc.writestr(form.filename, xmlContent, zipfile.ZIP_DEFLATED)
        zipDoc.close()
        os.close(descriptor)
        filename = self.pool.get('res.users').browse(cr, uid, uid).company_id.rfc + str(form.year) + form.month
        if form.xml_target == 'accounts_catalog':
            filename += 'CT'
        elif form.xml_target == 'trial_balance':
            filename += 'B' + form.trial_delivery
        elif form.xml_target == 'vouchers':
            filename += 'PL'
        elif form.xml_target == 'helpers':
            filename += 'XF'
        filename += '.zip'
        self.write(cr, uid, ids, {'state': 'zip_done',
         'zipped_file': b64enc(open(zipname, 'rb').read()),
         'filename': filename})
        return self._reopen_wizard(ids[0])



files_generator_wizard()


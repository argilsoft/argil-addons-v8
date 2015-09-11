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
import csv
import os.path
from openerp import tools, release
import base64
import StringIO

class overall_config_wizard(osv.osv_memory):
    _name = 'overall.config.wizard'
    _columns = {'action_status': fields.char('', size=128),
     'sat_filename': fields.char('Filename', size=128),
     'sat_data': fields.binary('Archivo de importaci\xc3\xb3n', filters='*.csv', help='Si ning\xc3\xban archivo es seleccionado se usar\xc3\xa1 el CSV instalado por defecto.'),
     'sat_catalog': fields.selection([('eaccount.bank', 'Bancos oficiales'),
                     ('account.journal.types', 'Tipos de p\xc3\xb3liza'),
                     ('sat.account.code', 'C\xc3\xb3digo agrupador'),
                     ('eaccount.currency', 'Monedas'),
                     ('eaccount.payment.methods', 'M\xc3\xa9todos de pago')], string='Cat\xc3\xa1logo objetivo'),
     'init_period_id': fields.many2one('account.period', 'Per\xc3\xadodo de inicializaci\xc3\xb3n'),
     'install_catalog_report': fields.boolean('Cat\xc3\xa1logo contable'),
     'install_trial_report': fields.boolean('Balanza de comprobaci\xc3\xb3n')}
    _defaults = {'sat_catalog': lambda *a: 'sat.account.code'}
    _period_names = {'01': 'Enero',
     '02': 'Febrero',
     '03': 'Marzo',
     '04': 'Abril',
     '05': 'Mayo',
     '06': 'Junio',
     '07': 'Julio',
     '08': 'Agosto',
     '09': 'Septiembre',
     '10': 'Octubre',
     '11': 'Noviembre',
     '12': 'Diciembre'}

    def _reopen_wizard(self, res_id):
        return {'type': 'ir.actions.act_window',
         'res_id': res_id,
         'view_mode': 'form',
         'view_type': 'form',
         'res_model': 'overall.config.wizard',
         'target': 'new',
         'name': 'Asistente para configuraci\xc3\xb3n general - Contabilidad Electr\xc3\xb3nica'}



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



    def default_get(self, cr, uid, fields, context = None):
        report_ids = self.pool.get('ir.actions.report.xml').search(cr, uid, [('report_name', 'ilike', 'jasper.')])
        jasper_reports = self.pool.get('ir.actions.report.xml').browse(cr, uid, report_ids)
        rs = super(overall_config_wizard, self).default_get(cr, uid, fields, context)
        for fld in fields:
            if fld == 'install_catalog_report':
                rs['install_catalog_report'] = len([ jr for jr in jasper_reports if jr.report_name == 'jasper.ceCatalogosContables' ])
            elif fld == 'install_trial_report':
                rs['install_trial_report'] = len([ jr for jr in jasper_reports if jr.report_name == 'jasper.ceBalanzaComprobacion' ])

        return rs



    def fields_view_get(self, cr, uid, view_id = None, view_type = 'form', context = None, toolbar = False, submenu = False):
        if context is None:
            context = {}
        if context.get('launched_from_menu', False):
            val = super(overall_config_wizard, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
            user = self.pool.get('res.users').browse(cr, uid, uid)
            return user.company_id._check_validity(val)
        return super(overall_config_wizard, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)



    def process_catalogs(self, cr, uid, ids, context):
        form = self.browse(cr, uid, ids)[0]
        user = self.pool.get('res.users').browse(cr, uid, uid)
        expected_col_number = 3 if form.sat_catalog == 'eaccount.bank' else 2
        orm_obj = self.pool.get(form.sat_catalog)
        if form.sat_data:
            decoded_string = base64.decodestring(form.sat_data)
            iterable_data = StringIO.StringIO(decoded_string)
        elif form.sat_catalog == 'eaccount.bank':
            target_file = self._find_file_in_addons('asti_eaccounting_mx_base/loadable_data', 'banks.csv')
        elif form.sat_catalog == 'account.journal.types':
            target_file = self._find_file_in_addons('asti_eaccounting_mx_base/loadable_data', 'journal_types.csv')
        elif form.sat_catalog == 'sat.account.code':
            target_file = self._find_file_in_addons('asti_eaccounting_mx_base/loadable_data', 'sat_codes.csv')
        elif form.sat_catalog == 'eaccount.payment.methods':
            target_file = self._find_file_in_addons('asti_eaccounting_mx_base/loadable_data', 'payment_methods.csv')
        else:
            target_file = self._find_file_in_addons('asti_eaccounting_mx_base/loadable_data', 'currencies.csv')
        iterable_data = open(target_file, 'r').readlines()
        reader = csv.reader(iterable_data)
        if context is None:
            context = {}
        context['allow_management'] = True
        obj_fields = []
        vals = {}
        if form.sat_catalog == 'eaccount.bank':
            search_field = 'bic'
        elif form.sat_catalog == 'sat.account.code':
            search_field = 'key'
        else:
            search_field = 'code'
        for (idx, row,) in enumerate(reader):
            if len(row) < expected_col_number:
                self.write(cr, uid, ids, {'action_status': 'Formato inesperado. Se esperaban %s columnas, pero se encontraron %s. L\xc3\xadnea %s' % (expected_col_number, len(row), idx + 1)})
                return True
            if idx == 0:
                obj_fields = row
                continue
            for (pos, fld,) in enumerate(obj_fields):
                vals[fld] = row[pos].zfill(3) if fld == search_field and form.sat_catalog in ('eaccount.bank', 'eaccount.currency') else row[pos]

            if form.sat_catalog == 'eaccount.currency':
                vals['company_id'] = user.company_id.id
            stored_ids = orm_obj.search(cr, uid, [(search_field, '=', vals[search_field])])
            if len(stored_ids):
                orm_obj.write(cr, uid, stored_ids, vals, context)
            else:
                orm_obj.create(cr, uid, vals, context)

        if form.sat_catalog == 'eaccount.bank':
            status = 'Los Bancos han sido correctamente procesados.'
        elif form.sat_catalog == 'account.journal.types':
            status = 'Los Tipos de P\xc3\xb3liza han sido correctamente procesados.'
        elif form.sat_catalog == 'sat.account.code':
            status = 'Los C\xc3\xb3digos del SAT han sido correctamente procesados.'
        elif form.sat_catalog == 'eaccount.payment.methods':
            status = 'Los m\xc3\xa9todos de pago han sido correctamente procesados.'
        else:
            status = 'Las monedas han sido correctamente procesadas.'
        self.write(cr, uid, ids, {'action_status': status})
        return self._reopen_wizard(ids[0])



    def process_accounts(self, cr, uid, ids, context):
        user = self.pool.get('res.users').browse(cr, uid, uid)
        if user.company_id.accounts_config_done:
            self.write(cr, uid, ids, {'action_status': 'Las cuentas en su cat\xc3\xa1logo ya hab\xc3\xadan sido inicializadas. Ning\xc3\xban cambio realizado.'})
            return {'type': 'ir.actions.act_window',
             'view_mode': 'form',
             'view_type': 'form',
             'res_id': ids[0],
             'res_model': self._name,
             'target': 'new',
             'name': 'Asistente para configuraci\xc3\xb3n general'}
        form = self.browse(cr, uid, ids)[0]
        accountObj = self.pool.get('account.account')
        periodsObj = self.pool.get('account.period')
        accountIds = accountObj.search(cr, uid, [('company_id', '=', user.company_id.id)])
        accounts = accountObj.browse(cr, uid, accountIds)
        for acc in accounts:
            cr.execute("SELECT date_trunc('day', create_date) FROM account_account WHERE id = %s", (acc.id,))
            create_date = cr.fetchall()[0][0]
            if not create_date:
                raise osv.except_osv(u'Inconsistencia de informaci\xf3n', u'La cuenta %s no tiene una fecha de creaci\xf3n asignada' % acc.name_get())
            create_period_ids = [form.init_period_id.id] if form.init_period_id else periodsObj.search(cr, uid, [('date_start', '=', create_date[0:8] + '01')])
            if not len(create_period_ids):
                raise osv.except_osv(u'Informaci\xf3n faltante', 'Se necesita crear el per\xc3\xadodo fiscal %s / %s' % (self._period_names[create_date[5:7]], create_date[0:4]))
            accountObj.write(cr, uid, [acc.id], {'first_period_id': create_period_ids[0]})

        user.company_id.write({'accounts_config_done': True})
        self.write(cr, uid, ids, {'action_status': 'Todas las cuentas han sido procesadas exitosamente'})
        return self._reopen_wizard(ids[0])



    def process_reports(self, cr, uid, ids, context):

        def register_report(cr, uid, context, obj, service, name, rep_file, model):
            vals = {'jasper_output': 'pdf',
             'attachment_use': False,
             'auto': True}
            modelId = self.pool.get('ir.model').search(cr, uid, [('model', '=', model)])[0]
            vals['jasper_model_id'] = modelId
            vals['report_file'] = rep_file
            vals['name'] = name
            vals['report_name'] = service
            filename_parts = rep_file.split('/')
            report_file = open(self._find_file_in_addons(filename_parts[0] + '/' + filename_parts[1], filename_parts[2]), 'r')
            vals['jasper_file_ids'] = [(0, 0, {'default': 1,
               'file': base64.encodestring(report_file.read()),
               'filename': rep_file.split('/')[-1]})]
            obj.create(cr, uid, vals, context)


        form = self.browse(cr, uid, ids)[0]
        reports_obj = self.pool.get('ir.actions.report.xml')
        report_ids = reports_obj.search(cr, uid, [('report_name', 'ilike', 'jasper.')])
        jasper_reports = reports_obj.browse(cr, uid, report_ids)
        context['jasper_report'] = True
        at_least_one_processed = False
        if form.install_catalog_report and not len([ jr for jr in jasper_reports if jr.report_name == 'jasper.ceCatalogosContables' ]):
            register_report(cr, uid, context, reports_obj, 'jasper.ceCatalogosContables', 'Cat\xc3\xa1logos contables (CE)', 'asti_eaccounting_mx_base/report/catalogos_contables.jrxml', 'account.account')
            at_least_one_processed = True
        if form.install_trial_report and not len([ jr for jr in jasper_reports if jr.report_name == 'jasper.ceBalanzaComprobacion' ]):
            register_report(cr, uid, context, reports_obj, 'jasper.ceBalanzaComprobacion', 'Balanza de comprobaci\xc3\xb3n (CE)', 'asti_eaccounting_mx_base/report/balanza_comprobacion.jrxml', 'account.monthly_balance')
            at_least_one_processed = True
        self.write(cr, uid, ids, {'action_status': 'Los informes seleccionados han sido instalados en el sistema.' if at_least_one_processed else 'No se ha seleccionado ning\xc3\xban informe o ya se encuentran instalados.'})
        return self._reopen_wizard(ids[0])



overall_config_wizard()


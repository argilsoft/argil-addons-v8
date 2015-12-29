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

########################## STABLE RELEASE ###########################
#                                                                   #
# +Complements manual creation.                                     #
# +Complements automatic creation (invoices and vouchers).          #
# +Support for user-defined concept templates (account moves).      #
# +XML files validated against SAT web validator.                   #
# +PDF reporting capabilities (accounts catalog and trial balance)  #
# +RML reporting support when 'workers' option is enabled           # 
# +Support for automatic complements in account moves generation    #
# +Field hiding/showing accordingly with auto mode enabled/disabled #
# +Support for alternate paying methods in journal configuration    #
#                                                                   #
#####################################################################
{
    'name' : 'Contabilidad electrónica para México',
    'description' : """Adecuación para cumplir con los requisitos de la Contabilidad Electrónica
         promulgada en 2014. Este módulo añade puntos específicos requeridos para generar los documentos
         XML requeridos por SAT.
         """,
    'version' : '1.0',
    'author' : 'ASTI Services',
    'website' : 'http://www.astiservices.com',
    'license' : 'GPL-3',
    'category' : 'Accounting',
    'depends' : ['base', 'account', 'account_cancel', 'argil_mx_accounting_reports_consol', 'l10n_mx_facturae_pac_sf'],
    'data' : ['eaccount_sat_code_view.xml',
                    'eaccount_journal_type_view.xml',
                    'eaccount_bank_view.xml',
                    'account_fit_view.xml',
                    'eaccount_account_bank_view.xml',
                    'company_fit_view.xml',
                    'journal_fit_view.xml',
                    'eaccount_currency_view.xml',
                    'account_moveline_fit_view.xml',
                    'hesa_filegenerate_view.xml',
                    'eaccount_payment_methods_view.xml',
                    'account_move_fit_view.xml',
                    'wizard/files_generator_view.xml',
                    'wizard/overall_config_view.xml',
                    'wizard/movelines_info_manager_view.xml',
                    'wizard/xsdvalidation_handler_view.xml',
                    'report/trial_balance_record.xml',
                    'report/accounts_catalog_record.xml',
                    'security/groups.xml',
                    'security/ir.model.access.csv',
                    'loadable_data/complements.xml',
                    'restrictive_actions.xml',
                    'invoice_fit_view.xml',
                    'voucher_fit_view.xml',
                    'menu.xml'],
    'demo_xml' : [],
    'installable' : True,
    'auto_install' : False
}
# Revision: 2.9
# Release: 1.2

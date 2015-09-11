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
import base64

class xsdvalidation_handler_wizard(osv.osv_memory):
    _name = 'xsdvalidation.handler.wizard'
    _columns = {'error_filename': fields.char('Error filename', size=20, required=True),
     'error_file': fields.binary('Detalles del error'),
     'sample_xmlname': fields.char('Sample XML Name', size=128, required=True),
     'sample_xml': fields.binary('XML con validaci\xc3\xb3n fallida')}

xsdvalidation_handler_wizard()


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

class account_journal_types(osv.osv):
    _name = 'account.journal.types'
    _description = 'Objeto para los tipos de p\xc3\xb3lizas'
    _columns = {'name': fields.char('Nombre', size=120, required=True),
     'code': fields.char('C\xc3\xb3digo', size=20, required=True)}

    def create(self, cr, uid, vals, context):
        if 'allow_management' not in context or not context['allow_management']:
            raise osv.except_osv('Operaci\xc3\xb3n no definida', 'Los tipos de p\xc3\xb3liza no pueden ser creados manualmente.')
        return super(account_journal_types, self).create(cr, uid, vals, context)



    def write(self, cr, uid, ids, vals, context):
        if 'allow_management' not in context or not context['allow_management']:
            raise osv.except_osv('Operaci\xc3\xb3n no definida', 'Los tipos de p\xc3\xb3liza no pueden ser modificados manualmente.')
        return super(account_journal_types, self).write(cr, uid, ids, vals, context)



    def unlink(self, cr, uid, ids, context):
        if 'allow_management' not in context or not context['allow_management']:
            raise osv.except_osv('Operaci\xc3\xb3n no definida', 'Los tipos de p\xc3\xb3liza no pueden ser eliminados manualmente.')
        return super(account_journal_types, self).unlink(cr, uid, context)



account_journal_types()


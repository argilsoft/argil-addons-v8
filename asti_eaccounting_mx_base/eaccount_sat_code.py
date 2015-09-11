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

class sat_account_code(osv.osv):
    _name = 'sat.account.code'
    _description = 'C\xc3\xb3digo agrupador de SAT para las cuentas'
    _columns = {'key': fields.char('C\xc3\xb3digo agrupador', size=10, required=True),
     'name': fields.char('Nombre', size=250, required=True)}

    def name_get(self, cr, uid, ids, context):
        rs = []
        for el in ids:
            element = self.browse(cr, uid, el)
            rs.append((el, '[' + element.key + '] ' + element.name))

        return rs



    def name_search(self, cr, uid, name = '', args = None, operator = 'ilike', context = None, limit = 100):
        if args is None:
            args = []
        if context is None:
            context = {}
        args = args[:]
        if not (name == '' and operator == 'ilike'):
            args += ['|', ('key', 'ilike', name), ('name', 'ilike', name)]
        ids = self._search(cr, uid, args, limit=limit, context=context, access_rights_uid=uid)
        res = self.name_get(cr, uid, ids, context)
        return res



    def create(self, cr, uid, vals, context):
        if 'allow_management' not in context or not context['allow_management']:
            raise osv.except_osv('Operaci\xc3\xb3n no definida', 'Los c\xc3\xb3digos agrupadores no pueden ser creados manualmente.')
        return super(sat_account_code, self).create(cr, uid, vals, context)



    def write(self, cr, uid, ids, vals, context):
        if 'allow_management' not in context or not context['allow_management']:
            raise osv.except_osv('Operaci\xc3\xb3n no definida', 'Los c\xc3\xb3digos agrupadores no son directamente modificables.')
        return super(sat_account_code, self).write(cr, uid, ids, vals, context)



    def unlink(self, cr, uid, ids, context):
        if 'allow_management' not in context or not context['allow_management']:
            raise osv.except_osv('Operaci\xc3\xb3n no definida', 'Los c\xc3\xb3digos agrupadores no son directamente eliminables.')
        return super(sat_account_code, self).unlink(cr, uid, ids, context)



sat_account_code()


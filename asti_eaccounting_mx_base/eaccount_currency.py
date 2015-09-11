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

class res_currency_fit(osv.osv):
    _name = 'eaccount.currency'
    _columns = {'name': fields.char('Nombre', size=128, required=True),
     'code': fields.char('C\xc3\xb3digo SAT', size=10, required=True)}

    def name_get(self, cr, uid, ids, context):
        rs = []
        lines = self.browse(cr, uid, ids)
        for ln in lines:
            rs.append((ln.id, '(' + ln.code + ') ' + ln.name))

        return rs



    def name_search(self, cr, uid, name = '', args = None, operator = 'ilike', context = None, limit = 100):
        if args is None:
            args = []
        if context is None:
            context = {}
        args = args[:]
        if not (name == '' and operator == 'ilike'):
            args += ['|', ('name', operator, name), ('code', 'ilike', name)]
        ids = self._search(cr, uid, args, limit=limit, context=context, access_rights_uid=uid)
        res = self.name_get(cr, uid, ids, context)
        return res



    def create(self, cr, uid, vals, context):
        if 'allow_management' not in context or not context['allow_management']:
            raise osv.except_osv('Operaci\xc3\xb3n no definida', 'Las monedas no pueden ser creadas manualmente.')
        return super(res_currency_fit, self).create(cr, uid, vals, context)



    def write(self, cr, uid, ids, vals, context):
        if 'allow_management' not in context or not context['allow_management']:
            raise osv.except_osv('Operaci\xc3\xb3n no definida', 'Las monedas no pueden ser modificadas manualmente.')
        return super(res_currency_fit, self).write(cr, uid, ids, vals, context)



    def unlink(self, cr, uid, ids, context):
        if 'allow_management' not in context or not context['allow_management']:
            raise osv.except_osv('Operaci\xc3\xb3n no definida', 'Las monedas no pueden ser eliminadas manualmente.')
        return super(res_currency_fit, self).unlink(cr, uid, ids, context)



res_currency_fit()

class res_currency_sat(osv.osv):
    _inherit = 'res.currency'
    _columns = {'sat_currency_id': fields.many2one('eaccount.currency', 'C\xc3\xb3digo del SAT', required=True)}

res_currency_sat()


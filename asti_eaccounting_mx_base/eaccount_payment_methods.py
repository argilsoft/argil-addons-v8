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

class eaccount_payment_methods(osv.osv):
    _name = 'eaccount.payment.methods'
    _columns = {'code': fields.char('C\xc3\xb3digo', size=2, required=True),
     'name': fields.char('M\xc3\xa9todo', size=150, required=True)}

    def name_get(self, cr, uid, ids, context):
        rs = []
        for el in ids:
            element = self.browse(cr, uid, el)
            rs.append((el, '[' + element.code + '] ' + element.name))

        return rs



    def name_search(self, cr, uid, name = '', args = None, operator = 'ilike', context = None, limit = 100):
        if args is None:
            args = []
        if context is None:
            context = {}
        args = args[:]
        if not (name == '' and operator == 'ilike'):
            args += ['|', ('code', 'ilike', name), ('name', 'ilike', name)]
        ids = self._search(cr, uid, args, limit=limit, context=context, access_rights_uid=uid)
        res = self.name_get(cr, uid, ids, context)
        return res



    def create(self, cr, uid, vals, context):
        if 'allow_management' not in context or not context['allow_management']:
            raise osv.except_osv(u'Operaci\xf3n no definida', u'Los m\xe9todos de pago no pueden ser creados manualmente.')
        return super(eaccount_payment_methods, self).create(cr, uid, vals, context)



    def write(self, cr, uid, ids, vals, context):
        if 'allow_management' not in context or not context['allow_management']:
            raise osv.except_osv(u'Operaci\xf3n no definida', u'Los m\xe9todos de pago no pueden ser creados manualmente.')
        return super(eaccount_payment_methods, self).write(cr, uid, ids, vals, context)



    def unlink(self, cr, uid, ids, context):
        if 'allow_management' not in context or not context['allow_management']:
            raise osv.except_osv(u'Operaci\xf3n no definida', u'Los m\xe9todos de pago no pueden ser creados manualmente.')
        return super(eaccount_payment_methods, self).unlink(cr, uid, ids, context)



eaccount_payment_methods()


from openerp.osv import fields, osv

class account_banks(osv.osv):
    _name = 'eaccount.bank'
    _columns = {'name': fields.char('Raz\xc3\xb3n social', size=250, required=True),
     'code': fields.char('Nombre corto', size=250, required=True),
     'bic': fields.char('Clave', size=11, required=True)}

    def name_get(self, cr, uid, ids, context):
        rs = []
        for el in ids:
            element = self.browse(cr, uid, el)
            rs.append((el, '[' + element.bic + '] ' + element.code))

        return rs



    def name_search(self, cr, uid, name = '', args = None, operator = 'ilike', context = None, limit = 100):
        if args is None:
            args = []
        if context is None:
            context = {}
        args = args[:]
        if not (name == '' and operator == 'ilike'):
            args += ['|', ('code', 'ilike', name), ('bic', 'ilike', name)]
        ids = self._search(cr, uid, args, limit=limit, context=context, access_rights_uid=uid)
        res = self.name_get(cr, uid, ids, context)
        return res



    def create(self, cr, uid, vals, context):
        if 'allow_management' not in context or not context['allow_management']:
            raise osv.except_osv('Operaci\xc3\xb3n no definida', 'Los bancos no pueden ser creados manualmente.')
        return super(account_banks, self).create(cr, uid, vals, context)



    def write(self, cr, uid, ids, vals, context):
        if 'allow_management' not in context or not context['allow_management']:
            raise osv.except_osv('Operaci\xc3\xb3n no definida', 'Los bancos no son directamente modificables.')
        return super(account_banks, self).write(cr, uid, ids, vals, context)



    def unlink(self, cr, uid, ids, context):
        if 'allow_management' not in context or not context['allow_management']:
            raise osv.except_osv('Operaci\xc3\xb3n no definida', 'Los bancos no son directamente eliminables.')
        return super(account_banks, self).unlink(cr, uid, ids, context)



account_banks()

class res_bank_sat(osv.osv):
    _inherit = 'res.bank'
    _columns = {'sat_bank_id': fields.many2one('eaccount.bank', 'C\xc3\xb3digo del SAT', required=True)}

res_bank_sat()


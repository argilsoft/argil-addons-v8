# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2014 Argil Consulting - http://www.argil.mx
############################################################################
#    Coded by: Israel Cruz Argil (israel.cruz@argil.mx)
############################################################################
#
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

from openerp.osv import fields, osv, expression
from openerp.tools.translate import _

class account_move_line(osv.osv):
    _inherit = "account.move.line"


    def _query_get(self, cr, uid, obj='l', context=None):
        fiscalyear_obj = self.pool.get('account.fiscalyear')
        fiscalperiod_obj = self.pool.get('account.period')
        account_obj = self.pool.get('account.account')
        fiscalyear_ids = []
        if context is None:
            context = {}
        ctx = context.copy()
        initial_bal = context.get('initial_bal', False)
        company_clause = " "
        if context.get('company_id', False):
            # Commented by Argil Consulting
            # company_clause = " AND " +obj+".company_id = %s" % context.get('company_id', False)
            # End Comment
            # Added by Argil Consulting
            if context.get('argil_revaluation', False):
                company_clause = " AND " +obj+".company_id = %s" % context.get('company_id', False)
            else:
                company_clause = " AND " +obj+".company_id in %s" % tuple([x.id for x in self.pool.get('res.users').browse(cr, uid, uid, context=context).company_ids]),
        if not context.get('fiscalyear', False):
            if context.get('all_fiscalyear', False):
                #this option is needed by the aged balance report because otherwise, if we search only the draft ones, an open invoice of a closed fiscalyear won't be displayed
                fiscalyear_ids = fiscalyear_obj.search(cr, uid, [])
            else:
                # Commented by Argil Consulting
                # fiscalyear_ids = fiscalyear_obj.search(cr, uid, [('state', '=', 'draft')])
                # End Comment
                # Added by Argil Consulting
                if context.get('argil_revaluation', False):
                    fiscalyear_ids = fiscalyear_obj.search(cr, uid, [('state', '=', 'draft'),('company_id','=',self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id)])
                else:
                    fiscalyear_ids = fiscalyear_obj.search(cr, uid, [('state', '=', 'draft')])
        else:
            #for initial balance as well as for normal query, we check only the selected FY because the best practice is to generate the FY opening entries
            # Commented by Argil Consulting
            # fiscalyear_ids = [context['fiscalyear']]
            # End Comment
            # Added by Argil Consulting            
            if context.get('argil_revaluation', False):
                fiscalyear_ids = [context['fiscalyear']]
            else:
                cr.execute("select name from account_fiscalyear where id in (%s) limit 1" % ((','.join([str(x) for x in [context['fiscalyear']]])) or '0'))
                ydata = cr.fetchone()
                fiscalyear_name = ydata[0] or ''
                companies = [x.id for x in self.pool.get('res.users').browse(cr, uid, uid, context=context).company_ids]
                fiscalyear_ids = fiscalyear_obj.search(cr, uid, [('company_id','in', tuple(companies),),
                                                                ('name','=', fiscalyear_name)
                                                                ])

        fiscalyear_clause = (','.join([str(x) for x in fiscalyear_ids])) or '0'
        state = context.get('state', False)
        where_move_state = ''
        where_move_lines_by_date = ''

        if context.get('date_from', False) and context.get('date_to', False):
            if initial_bal:
                where_move_lines_by_date = " AND " +obj+".move_id IN (SELECT id FROM account_move WHERE date < '" +context['date_from']+"')"
            else:
                where_move_lines_by_date = " AND " +obj+".move_id IN (SELECT id FROM account_move WHERE date >= '" +context['date_from']+"' AND date <= '"+context['date_to']+"')"

        if state:
            if state.lower() not in ['all']:
                where_move_state= " AND "+obj+".move_id IN (SELECT id FROM account_move WHERE account_move.state = '"+state+"')"
        if context.get('period_from', False) and context.get('period_to', False) and not context.get('periods', False):
            if initial_bal:
                period_company_id = fiscalperiod_obj.browse(cr, uid, context['period_from'], context=context).company_id.id
                first_period = fiscalperiod_obj.search(cr, uid, [('company_id', '=', period_company_id)], order='date_start', limit=1)[0]
                ctx['periods'] = fiscalperiod_obj.build_ctx_periods(cr, uid, first_period, context['period_from'])
            else:
                ctx['periods'] = fiscalperiod_obj.build_ctx_periods(cr, uid, context['period_from'], context['period_to'])                
        if ctx.get('periods', False):
            xperiods = fiscalperiod_obj.read(cr, uid, ctx['periods'], ['name'])
            ctx['periods'] = fiscalperiod_obj.search(cr, uid, [('name','in',tuple([x['name'] for x in xperiods]),)])
            
            if initial_bal:
                query = obj+".state <> 'draft' AND "+obj+".period_id IN (SELECT id FROM account_period WHERE fiscalyear_id IN (%s)) %s %s" % (fiscalyear_clause, where_move_state, where_move_lines_by_date)
                period_ids = fiscalperiod_obj.search(cr, uid, [('id', 'in', context['periods'])], order='date_start', limit=1)
                if period_ids and period_ids[0]:
                    first_period = fiscalperiod_obj.browse(cr, uid, period_ids[0], context=ctx)
                    ids = ','.join([str(x) for x in ctx['periods']])
                    query = obj+".state <> 'draft' AND "+obj+".period_id IN (SELECT id FROM account_period WHERE fiscalyear_id IN (%s) AND date_start <= '%s' AND id NOT IN (%s)) %s %s" % (fiscalyear_clause, first_period.date_start, ids, where_move_state, where_move_lines_by_date)
            else:
                ids = ','.join([str(x) for x in ctx['periods']])
                query = obj+".state <> 'draft' AND "+obj+".period_id IN (SELECT id FROM account_period WHERE fiscalyear_id IN (%s) AND id IN (%s)) %s %s" % (fiscalyear_clause, ids, where_move_state, where_move_lines_by_date)
        else:
            query = obj+".state <> 'draft' AND "+obj+".period_id IN (SELECT id FROM account_period WHERE fiscalyear_id IN (%s)) %s %s" % (fiscalyear_clause, where_move_state, where_move_lines_by_date)

        if initial_bal and not ctx.get('periods', False) and not where_move_lines_by_date:
            #we didn't pass any filter in the context, and the initial balance can't be computed using only the fiscalyear otherwise entries will be summed twice
            #so we have to invalidate this query
            raise osv.except_osv(_('Warning!'),_("You have not supplied enough arguments to compute the initial balance, please select a period and a journal in the context."))


        if context.get('journal_ids', False):
            query += ' AND '+obj+'.journal_id IN (%s)' % ','.join(map(str, context['journal_ids']))

        if context.get('chart_account_id', False):
            child_ids = account_obj._get_children_and_consol(cr, uid, [context['chart_account_id']], context=ctx)
            query += ' AND '+obj+'.account_id IN (%s)' % ','.join(map(str, child_ids))

        query += company_clause
        return query


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

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

from openerp import tools, release
from openerp import SUPERUSER_ID
from openerp.osv import fields, osv, expression
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
import openerp.addons.decimal_precision as dp
import time


class account_account(osv.osv):
    _inherit = "account.account"
    
    def __compute_argil(self, cr, uid, ids, field_names, arg=None, context=None, query=''):
        if context is None:
            context = {}
        res = {}.fromkeys(ids, {}.fromkeys(field_names, 0))
        #print "context", context
        context2 = context.copy()
        periods = context.get('periods', False)
        #date = context.get('date_from', False)
        #print "periods: ", periods    
        if periods:
            subquery = """SELECT distinct period_past.id
                    FROM account_period period_past
                    INNER JOIN 
                      (
                        SELECT *
                        FROM account_period
                        WHERE id in %s
                      ) period_current
                    ON --period_current.fiscalyear_id = period_past.fiscalyear_id AND
                     period_current.date_start > period_past.date_start AND
                     period_current.date_stop > period_past.date_stop
                """ % ( tuple(periods), )
            #print "subquery: \n", subquery
            cr.execute( subquery )
            period_ids = [ period_id[0] for period_id in cr.fetchall() ]
            #print "period_ids: ", period_ids
            if period_ids:
                context2.update( {'periods': period_ids, 'period_id': False} )
                #print "context2: ", context2
                res = self.__compute(cr, uid, ids, field_names=['balance'], arg=arg, context=context2, query=query)
        #elif date:
        #    date_obj = datetime.strptime(date, '%Y-%m-%d')
        #    date_from = date_obj.strftime('%Y-01-01')
        #    date_to_obj = date_obj + relativedelta(days=-1)
        #    date_to =  date_to_obj.strftime('%Y-%m-%d')
        #    context2.update( {'date_from': date_from, 'date_to': date_to} )
        #    res = self.__compute(cr, uid, ids, field_names=['balance'], arg=arg, context=context2, query=query)
        #print "context2",context2
        #print "==========================="
        #print "res: ", res
        #print "==========================="
        #for r in res:
            #print "r: ", r
            #print "res[r]: ", res[r]
        #print "==========================="
        res_original = self.__compute(cr, uid, ids, field_names=['balance'], arg=arg, context=context, query=query)
        #print "res_original: ", res_original
        res2 = {}
        #print "==========================="
        for r in res:
            #print "res[r]: ", res[r]
            res2[r] = {
                'argil_initial_balance': res[r]['balance'] if 'balance' in res[r] else 0.0,
                'argil_balance_all': res_original[r]['balance'] + (res[r]['balance'] if 'balance' in res[r] else 0.0),
            }
        res = res2
        return res
    
    
    
    
    
    
    def x__compute_argil(self, cr, uid, ids, field_names, arg=None, context=None,
                  query='', query_params=()):
        """ compute the balance, debit and/or credit for the provided
        account ids
        Arguments:
        `ids`: account ids
        `field_names`: the fields to compute (a list of any of
                       'balance', 'debit' and 'credit')
        `arg`: unused fields.function stuff
        `query`: additional query filter (as a string)
        `query_params`: parameters for the provided query string
                        (__compute will handle their escaping) as a
                        tuple
        """
        mapping = {            
            'argil_balance': "COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as argil_balance",
            'argil_debit': "COALESCE(SUM(l.debit), 0) as argil_debit",
            'argil_credit': "COALESCE(SUM(l.credit), 0) as argil_credit",
            # by convention, foreign_balance is 0 when the account has no secondary currency, because the amounts may be in different currencies
            #'foreign_balance': "(SELECT CASE WHEN currency_id IS NULL THEN 0 ELSE COALESCE(SUM(l.amount_currency), 0) END FROM account_account WHERE id IN (l.account_id)) as foreign_balance",
        }
        #get all the necessary accounts
        children_and_consolidated = self._get_children_and_consol(cr, uid, ids, context=context)
        #compute for each account the balance/debit/credit from the move lines
        accounts = {}
        res = {}
        null_result = dict((fn, 0.0) for fn in field_names)
        if children_and_consolidated:
            aml_query = self.pool.get('account.move.line')._query_get(cr, uid, context=context)
            wheres = [""]
            if query.strip():
                wheres.append(query.strip())
            if aml_query.strip():
                wheres.append(aml_query.strip())
            filters = " AND ".join(wheres)
            # IN might not work ideally in case there are too many
            # children_and_consolidated, in that case join on a
            # values() e.g.:
            # SELECT l.account_id as id FROM account_move_line l
            # INNER JOIN (VALUES (id1), (id2), (id3), ...) AS tmp (id)
            # ON l.account_id = tmp.id
            # or make _get_children_and_consol return a query and join on that
            request = ("SELECT l.account_id as id, " +\
                       ', '.join(mapping.values()) +
                       " FROM account_move_line l" \
                       " WHERE l.account_id IN %s " \
                            + filters +
                       " GROUP BY l.account_id")
            params = (tuple(children_and_consolidated),) + query_params
            #print "======================"
            #print "request: ", request
            #print "======================"
            #print "params: ", params
            #print "======================"
            cr.execute(request, params)

            for row in cr.dictfetchall():
                accounts[row['id']] = row

            # consolidate accounts with direct children
            children_and_consolidated.reverse()
            brs = list(self.browse(cr, uid, children_and_consolidated, context=context))
            sums = {}
            currency_obj = self.pool.get('res.currency')
            while brs:
                current = brs.pop(0)
#                can_compute = True
#                for child in current.child_id:
#                    if child.id not in sums:
#                        can_compute = False
#                        try:
#                            brs.insert(0, brs.pop(brs.index(child)))
#                        except ValueError:
#                            brs.insert(0, child)
#                if can_compute:
                for fn in field_names:
                    sums.setdefault(current.id, {})[fn] = accounts.get(current.id, {}).get(fn, 0.0)
                    for child in current.child_id:
                        if child.company_id.currency_id.id == current.company_id.currency_id.id:
                            sums[current.id][fn] += sums[child.id][fn]
                        else:
                            sums[current.id][fn] += currency_obj.compute(cr, uid, child.company_id.currency_id.id, current.company_id.currency_id.id, sums[child.id][fn], context=context)

                # as we have to relay on values computed before this is calculated separately than previous fields
                if current.currency_id and current.exchange_rate and \
                            ('adjusted_balance' in field_names or 'unrealized_gain_loss' in field_names):
                    # Computing Adjusted Balance and Unrealized Gains and losses
                    # Adjusted Balance = Foreign Balance / Exchange Rate
                    # Unrealized Gains and losses = Adjusted Balance - Balance
                    adj_bal = sums[current.id].get('foreign_balance', 0.0) / current.exchange_rate
                    sums[current.id].update({'adjusted_balance': adj_bal, 'unrealized_gain_loss': adj_bal - sums[current.id].get('balance', 0.0)})

            for id in ids:
                res[id] = sums.get(id, null_result)
        else:
            for id in ids:
                res[id] = null_result
        return res

    
    
    _columns = {
        'argil_initial_balance' : fields.function(__compute_argil, digits_compute=dp.get_precision('Account'), string='Initial Balance', multi='argil_initial_balance'),
#        'argil_debit'           : fields.function(__compute_argil, digits_compute=dp.get_precision('Account'), string='Debit', multi='argil_initial_balance'),
#        'argil_credit'          : fields.function(__compute_argil, digits_compute=dp.get_precision('Account'), string='Credit', multi='argil_initial_balance'),
#        'argil_balance'         : fields.function(__compute_argil, digits_compute=dp.get_precision('Account'), string='Balance', multi='argil_initial_balance'),
        'argil_balance_all'     : fields.function(__compute_argil, digits_compute=dp.get_precision('Account'), string='Balance All', multi='argil_initial_balance'),
    }




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

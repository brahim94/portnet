# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (http://tiny.be). All Rights Reserved
#
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

import time

from lxml import etree
from datetime import datetime
from openerp.osv import fields, orm
from openerp.tools.translate import _

class trial_balance_wizard_inherit(orm.TransientModel):
    _inherit = 'trial.balance.webkit'

    _columns = {
        'under_account':fields.boolean("Filter sur les sous comptes"),
    }

    def check_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids, ['date_from',  'date_to',  'fiscalyear_id', 'journal_ids', 'period_from', 'period_to',  'filter',  'chart_account_id', 'target_move','under_account'], context=context)[0]
        for field in ['fiscalyear_id', 'chart_account_id', 'period_from', 'period_to']:
            if isinstance(data['form'][field], tuple):
                data['form'][field] = data['form'][field][0]
        used_context = self._build_contexts(cr, uid, ids, data, context=context)
        data['form']['periods'] = used_context.get('periods', False) and used_context['periods'] or []
        data['form']['used_context'] = dict(used_context, lang=context.get('lang', 'en_US'))
        return self._print_report(cr, uid, ids, data, context=context)

    def _print_report(self, cr, uid, ids, data, context=None):
        context = context or {}
        if context.get('xls_export'):
            # we update form with display account value
            data = self.pre_print_report(cr, uid, ids, data, context=context)
            return {'type': 'ir.actions.report.xml',
                    'report_name': 'account.account_report_trial_balance_inherit_xls',
                    'datas': data}
        else:
            return super(trial_balance_wizard_inherit, self)._print_report(
                cr, uid, ids, data, context=context)
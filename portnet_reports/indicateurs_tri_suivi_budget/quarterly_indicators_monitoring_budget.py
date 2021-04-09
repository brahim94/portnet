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


from openerp import models, fields, api, _, exceptions


class quarterly_indicators_monitoring_budget_report(models.Model):
    
    _name="quarterly.indicators.monitoring.budget.report"

    name = fields.Char(string="Période")
    rubrique=fields.Char(srting='Rubriques')
    initial_credit=fields.Float(srting='Crédit initial')
    engagement=fields.Float(srting='Engagement')
    taux=fields.Float(srting='Taux')
    comment=fields.Text(srting='Commentaire')
    line_id = fields.Many2one(comodel_name = 'crossovered.budget.lines', string = 'Budget')

quarterly_indicators_monitoring_budget_report()


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

class monthly_monitoring_treasury_report(models.Model):

    _name = 'monthly.monitoring.treasury.report'


    period_id = fields.Many2one(comodel_name="account.period", string="Période")
    name = fields.Char(string='Type d opération')
    initial_solde = fields.Float(string='Solde initial')
    encais = fields.Float(string='Encaissement')
    dencais = fields.Float(string='Décaissement')
    final_solde = fields.Float(string='Solde Final')

monthly_monitoring_treasury_report()

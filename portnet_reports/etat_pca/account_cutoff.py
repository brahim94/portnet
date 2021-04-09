# -*- encoding: utf-8 -*-
##############################################################################
#
#    Account Cut-off Prepaid module for OpenERP
#    Copyright (C) 2013 Akretion (http://www.akretion.com)
#    @author Alexis de Lattre <alexis.delattre@akretion.com>
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


from openerp.osv import orm, fields
from openerp.tools.translate import _
from datetime import datetime


class account_cutoff_line(orm.Model):
    _inherit = 'account.cutoff.line'

    _columns = {

        'cutoff_date': fields.related(
            'parent_id', 'cutoff_date', type='date', string="Date de l'arrêté", readonly=True),

        'number': fields.related(
            'invoice_id', 'number', type='char', string='Numéro Facture', readonly=True),

        'product_id': fields.related(
            'move_line_id', 'product_id', type='many2one',
            relation='product.product', string='Produit', readonly=True),

        'periodicity_id': fields.related(
            'product_id', 'periodicity_id', type='many2one',
            relation='res.periodicity', string='Périodicité', readonly=True,store=True),

    }

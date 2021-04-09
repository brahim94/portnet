
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

from openerp import models, fields, api, exceptions, _
import datetime

class config_table_xls(models.Model):

    _name="config.table.xls"

    name = fields.Char(string="Nom du Rapports Excel", required=True)
    code = fields.Char(string="Code", required=True)
    title_report = fields.Char(string="Titre du Rapport")
    title_feuille_report = fields.Char(string="Titre feuille excel")
    name_report_out = fields.Char(string="Nom du fichier de sortie")
    row_start = fields.Integer(string="Ligne de débart")
    column_start = fields.Integer(string="Cellule de débart")
    couleur_tableau_header = fields.Char(string="Couleur Entête Tableau (en HEX #000000)")

config_table_xls()
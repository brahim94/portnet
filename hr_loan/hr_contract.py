# -*- coding: utf-8 -*-
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta

from openerp import fields, models, api
from openerp import exceptions
from openerp.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    )


class Contract(models.Model):
    _inherit = 'hr.contract'

    status = fields.Selection([
        ('brouillon', "Brouillon"),
        ('valide', "Validé"),
        ], default='brouillon')

    @api.multi
    def action_valider(self):
        self.status= 'valide'


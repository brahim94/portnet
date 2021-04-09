# -*- encoding: utf-8 -*-

from openerp import models, fields, api, exceptions, _
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from dateutil import parser

class rescontract(models.Model):
      _inherit = "res.contract"

      compte_active = fields.Boolean(string='Activé',default=True)

# -*- encoding: utf-8 -*-

from openerp.osv import osv
from openerp import SUPERUSER_ID,models, fields, api, _, exceptions
import openerp.addons.decimal_precision as dp
import datetime

from string import Template
import requests
import time
import concurrent.futures
import xml.etree.ElementTree as ET

class ResPartnerCategory(models.Model):
    _inherit = 'res.partner.category'

    auto_activation = fields.Boolean(string="Activation Automatique",default=False)


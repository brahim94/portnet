# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#
#    Copyright (c) 2009-2016 Noviat nv/sa (www.noviat.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

try:
    import cStringIO as StringIO
except ImportError:
    import StringIO
import base64
import csv
import time
from datetime import datetime
from sys import exc_info
from traceback import format_exception
from dateutil import parser, rrule, relativedelta
from openerp import api, fields, models, exceptions, _
from openerp.exceptions import Warning
import tempfile
import logging
import os
_logger = logging.getLogger(__name__)


class partner_update_wizard(models.TransientModel):
    _name = 'partner.update.wizard'

    aml_data = fields.Binary(string='File', required=True)
    aml_fname = fields.Char(string='Filename')


    @api.multi
    def action_update(self):

        time_start = time.time()
        filepath = tempfile.gettempdir()+'/'+self.aml_fname
        data = self.aml_data
        f = open(filepath,'wb')
        data=base64.decodestring(data)
        f.write(data)
        f.close()
        csvfile=open(filepath)
        dialect = csv.Sniffer().sniff(csvfile.read(1024))
        csvfile.seek(0)
        reader = csv.reader(csvfile, dialect)
        not_loaded=[]
        i=0
        #path = os.path.expanduser("~")
        #os.chdir(path)
        #csv_file = csv.writer(open("updated_partners_"+str(self.aml_fname), "wb"))
        #csv_file.writerow(["ID_piece","account","partner","date","name","journal","period","debit","credit","Motif"])
        found = 0
        not_found = 0
        updated = 0
        for line in reader:
            if i==0:
                i+=1
                continue
            print "iteration",i
            phone = False
            email = False
            code = False
            code=line[0]
            phone=line[3]
            email = line[4]
            if code:
                print code,phone,email
                partners = self.env['res.partner'].search([('is_company','=',True),('code','=',str(code))])
                if partners: found+=1
                for part in partners:
                    if not part.email:
                        updated+=1
                        part.write({'email':email})
                    if not part.phone:
                        part.write({'phone':phone})
                    if not part.mobile:
                        part.write({'mobile':phone})
            else:
                not_found+=1
            i+=1

        print "found ==",found
        print "updated ==",updated
        print "not_found ==",not_found

partner_update_wizard()
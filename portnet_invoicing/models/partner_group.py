# -*- encoding: utf-8 -*-

from openerp import models, fields, api

class res_partner_group(models.Model):
    _name = 'res.partner.group'

    name = fields.Char(string="Nom",required=True)
    code = fields.Char(string="Code",required=True)
    partner_ids = fields.One2many(comodel_name="res.partner", inverse_name="partner_group_id", string="Partenaires", required=False,domain= ['|',('customer','=',True),('supplier','=',True)] )

    _sql_constraints = [

        ("unique_code","UNIQUE(code)","Le code de la société mère est unique"),
    ]

    @api.model
    def _action_create_groups(self):
        req = "SELECT code FROM res_partner WHERE is_company = true AND parent_id IS NULL AND code IS NOT NULL "
        self._cr.execute(req)
        all_partner_codes = [x[0] for x in self._cr.fetchall()]
        duplicate_codes = [x for x in all_partner_codes if all_partner_codes.count(x) >= 2]
        for code in duplicate_codes:
            req = "SELECT id, name FROM res_partner WHERE is_company = true AND parent_id IS NULL AND partner_group_id IS NULL AND code = '"+str(code)+"' "
            self._cr.execute(req)
            dict_result = self._cr.dictfetchall()
            for partner in dict_result:
                groups = []
                req = "SELECT id FROM res_partner_group WHERE code = '"+str(code)+"' "
                self._cr.execute(req)
                groups = [x[0] for x in self._cr.fetchall()]
                if groups:
                    req = "UPDATE res_partner set partner_group_id = "+str(groups[0])+" WHERE id = "+str(partner['id'])
                    self._cr.execute(req)
                else:
                    new_group = self.create({'name':partner['name'],'code':code})
                    req = "UPDATE res_partner set partner_group_id = "+str(new_group.id)+" WHERE id = "+str(partner['id'])
                    self._cr.execute(req)
        return True

res_partner_group()
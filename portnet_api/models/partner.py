# -*- encoding: utf-8 -*-

from openerp import api, fields, models, _


class ResPartner(models.Model):
     _inherit = 'res.partner'

     @api.model
     def create_partner(self, vals):
        partner_id = False
        if vals:
            custom_office_obj = self.env['custom.office']
            if vals.get('portnet_user_ids'):
                for line in vals['portnet_user_ids']:
                    if line[2].get('custom_office_id'):
                        cstm_office_id = custom_office_obj.search([('code', '=', line[2]['custom_office_id'])], limit=1)
                        if not cstm_office_id:
                            return {'faultCode': 0, 'faultString': "office code doesn’t exist in Odoo db."}
                        line[2].update({'custom_office_id': cstm_office_id.id})

            if vals.get('country_id'):
                country_id = self.env['res.country'].search([('code', '=', vals['country_id'])], limit=1)
                if not country_id:
                    return {'faultCode': 0, 'faultString': "country code doesn’t exist in Odoo db."}
                vals.update({'country_id': country_id.id})

            if vals.get('categ_id'):
                categ_id = self.env['res.partner.category'].search([('code', '=', vals['categ_id'])], limit=1)
                if not categ_id:
                    return {'faultCode': 0, 'faultString': "category code doesn’t exist in Odoo db."}
                vals.update({'categ_id': categ_id.id})

            if vals.get('code_port'):
                code_port = self.env['code.port'].search([('code', '=', vals['code_port'])], limit=1)
                if not code_port:
                    return {'faultCode': 0, 'faultString': "code port doesn’t exist in Odoo db."}
                vals.update({'code_port': code_port.id})
            
            if vals.get('custom_office_line_ids'):
                office_lines = []
                for line in vals['custom_office_line_ids']:
                    office_code = line[0].get('custom_office_id')
                    custom_office_id = custom_office_obj.search([('code', '=', office_code)], limit=1)
                    if not custom_office_id:
                        return {'faultCode': 0, 'faultString': "office code doesn’t exist in Odoo db."}
                    office_lines.append((0, 0, {'custom_office_id': custom_office_id.id, 'custom_office_cin_code': line[0].get('custom_office_cin_code')}))
                vals.update({'custom_office_line_ids': office_lines})
           
            partner_id = self.create(vals)
            
        if partner_id:
            return {'success': partner_id.id}
        else:
            return {'faultCode': 0, 'faultString': 'Something went wrong!'}

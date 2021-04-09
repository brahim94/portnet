# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError

_STATES = [
    ("draft", "Draft"),
    ("to_be_approve", "Approve"),
    ("to_approve", "Validated"),
    ("approved", "Qualified"),
    ("done", "Closed"),
    ("rejected", "Refusé"),
    ("cancelled", "Annulé")
]


class PurchaseRequest(models.Model):
    _inherit = 'purchase.request'

    qualifier_id = fields.Many2one("res.users", string="Qualifier", track_visibility="onchange",
        domain=lambda self: [("groups_id", "in", self.env.ref("wt_purchase_request_extend.group_purchase_request_qualifer").id)])
    financement_type = fields.Selection([('CHB', 'CHB'),('Sur Budget', 'Sur Budget')], string="Type de Financement")   
    # programme_chb = fields.Many2one("purchase.financement", string="Programme CHB")
    
    #override
    assigned_to = fields.Many2one(comodel_name="res.users", string="Responsible", track_visibility="onchange",
        domain=lambda self: [("groups_id", "in", self.env.ref("wt_purchase_request_extend.group_purchase_request_responsible").id)],
        default=lambda self:self.env.uid)
    state = fields.Selection(selection=_STATES, string="Status", index=True, track_visibility="onchange",
        required=True, copy=False, default="draft")
    validator_id = fields.Many2one(comodel_name="res.users", string="Validator", track_visibility="onchange",
        domain=lambda self: [("groups_id", "in", self.env.ref("purchase_request.group_purchase_request_manager").id)])

    # @api.onchange('financement_type')
    # def onchange_financement_type(self):
    #     if self.financement_type != 'CHB':
    #         self.programme_chb = ''

    def button_to_approve(self):
        if not self.assigned_to.employee_ids:
            raise UserError(_('There is no employee found for responsible user.'))
        if not self.assigned_to.employee_ids[0].department_id:
            raise UserError(_('There is no employee department found for responsible user.'))
        if not self.assigned_to.employee_ids[0].department_id == self.department_id:
            raise UserError(_('There is no matching employee department found for responsible user.'))
        if not self.validator_id:
            raise UserError(_('Please assign Validator before process.'))
        return super(PurchaseRequest, self).button_to_approve()

    @api.onchange('department_id')
    def onchange_department(self):
        if self.department_id and self.department_id.manager_id:
            self.assigned_to = self.department_id.manager_id.user_id.id if self.department_id.manager_id.user_id else False

    def button_to_be_approve(self):
        if self.viewd_approved == False:
            raise UserError(_('La demande doit etre vue et approvée par le responsable.'))
        return self.write({"state": "to_be_approve"})
         
    def button_approved(self):
        if not self.qualifier_id:
            raise UserError(_('Please assign Qualificateur before process.'))
        return self.write({"state": "approved"})

    def button_rejected(self):
        return self.write({"state": "rejected"})

    def button_cancelled(self):
        if not self.env.user.has_group('wt_purchase_request_extend.group_purchase_request_responsible'):
            self.mapped("line_ids").do_cancel()
        return self.write({"state": "cancelled"})

    @api.depends("state", "line_ids.product_qty", "line_ids.cancelled")
    def _compute_to_approve_allowed(self):
        for rec in self:
            rec.to_approve_allowed = rec.state == "to_be_approve" and any(
                [not line.cancelled and line.product_qty for line in rec.line_ids]
            )

   
class PurchaseFinancement(models.Model):
    _name = 'purchase.financement'
    _description = 'Purchase Financement'

    name = fields.Char(string="Name", required=True)


class PurchasePrevisionnel(models.Model):
    _name = 'purchase.previsionnel'
    _description = 'Purchase Previsionnel'

    name = fields.Char(string="Name", required=True)



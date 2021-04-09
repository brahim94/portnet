# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import datetime, date, timedelta


class SubmissionIncrement(models.TransientModel):
    _name = "submission.increment"
    _description = "Submission date Increment Wizard"

    name = fields.Integer(string="Postponement Deadline", required=True)

    def action_validate(self):
        rectification_active_id = self._context.get('active_id', [])
        rectification_id = self.env['tender.rectification'].browse(rectification_active_id)
        if self.name > 0:
            
            rectification_id.requisition_id.submission_days = rectification_id.requisition_id.submission_days + self.name
            rectification_id.requisition_id.onchange_submission_days()
            
            if rectification_id.requisition_id.site_visit_date and (rectification_id.date < rectification_id.requisition_id.site_visit_date):
                rectification_id.requisition_id.site_visit_days = rectification_id.requisition_id.site_visit_days + (self.name/2)
            rectification_id.requisition_id.onchange_site_visit_days()

            if rectification_id.requisition_id.convocation_date and (rectification_id.date < rectification_id.requisition_id.convocation_date):
                rectification_id.requisition_id.convocation_days = rectification_id.requisition_id.convocation_days + self.name
            rectification_id.requisition_id.onchange_convocation_days()

            rectification_id.write({
                'date_should_be': rectification_id.requisition_id.submission_date,
                'original_updated_days': self.name,
                'deadline_days': 0,
                })

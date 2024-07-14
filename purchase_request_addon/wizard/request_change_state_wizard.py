from odoo import fields, models

class ChangeState(models.TransientModel):
    _name = 'change.state'

    rejection_reason = fields.Text(string="Rejection Reason", required=True)

    def reject_order(self):
        active_ids = self.env.context.get('active_ids', [])
        requests = self.env['purchase.request'].browse(active_ids)
        for request in requests:
            request.write({'state': 'reject', 'rejection_reason': self.rejection_reason})

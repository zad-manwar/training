from odoo import models, api, fields, exceptions


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    # @api.onchange('product_qty')
    # def _check_order_product_qty_against_request(self):
    #     for line in self:
    #         if line.product_id and line.product_qty > 0:
    #             pr_line = self.env['purchase.request.line'].search([
    #                 ('request_id.name','=', line.order_id.name),
    #                 ('request_id.state', 'not in', ['to be approved', 'draft','reject','cancel']),
    #                 ('product_id', '=', line.product_id.id),
    #                 ('quantity', '<=', line.product_qty),
    #             ],)
    #             if pr_line:
    #                 raise exceptions.ValidationError(
    #                     f"Quantity in PO line ({line.product_qty}) exceeds quantity requested in PR ({pr_line.quantity})."
    #                 )

    @api.constrains('product_qty','state')
    def _check_order_product_qty_against_request(self):
        for line in self:
            if line.product_id and line.product_qty > 0:
                po = self.env['purchase.order'].search([
                    ('name', '=', line.order_id.name),
                    ('order_line.product_id', '=', line.product_id.id),
                    ('state', 'in', ['purchase']),
                    ('id', '!=', line._origin.order_id.id),
                ], )
                print(po)
                total_qty = 0
                total_qty += line.product_qty
                for rec in po:
                    for ord_line in rec.order_line:
                        if ord_line.product_id == line.product_id:
                            print(ord_line.product_qty)
                            total_qty += ord_line.product_qty
                print(total_qty)
                print(line.order_id.name)
                print(line.product_id.id)

                pr_line = self.env['purchase.request.line'].search([
                    ('request_id.name', '=', line.order_id.name),
                    ('request_id.state', 'not in', ['to be approved', 'draft', 'reject', 'cancel']),
                    ('product_id', '=', line.product_id.id),
                ], limit=1)
                print(f"Quantity in PO line ({line.product_id.name}:{total_qty}) quantity requested in PR ({pr_line.product_id.name}:{pr_line.quantity}).")
                if (pr_line.quantity - total_qty) < 0:
                    raise exceptions.ValidationError(
                        f"Quantity in PO line ({line.product_id.name}:{total_qty}) exceeds quantity requested in PR ({pr_line.product_id.name}:{pr_line.quantity})."
                    )

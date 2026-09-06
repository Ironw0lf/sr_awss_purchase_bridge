# -*- coding: utf-8 -*-
from odoo import fields, models


class AwssPurchaseRequest(models.Model):
    _inherit = 'awss.purchase.request'

    sr_workorder_id = fields.Many2one(
        'sr.workorder',
        string='SR Work Order',
        index=True,
        tracking=True,
        help='The SR Maintenance work order this purchase request was raised from.',
    )

    def _prepare_purchase_order_vals(self, buyer):
        # Reuses sr_maintenance's own purchase.order.sr_workorder_id field
        # (added for its native "create a PO directly from a WO" flow)
        # instead of introducing a second link field on purchase.order. This
        # is v19.0.4.9's purpose-built override point for this exact case
        # (see its docstring).
        vals = super()._prepare_purchase_order_vals(buyer)
        if self.sr_workorder_id:
            vals['sr_workorder_id'] = self.sr_workorder_id.id
        return vals

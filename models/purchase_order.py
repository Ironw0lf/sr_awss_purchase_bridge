# -*- coding: utf-8 -*-
from odoo import _, api, models
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # AWSS never allows a raw purchase order: every purchase goes through a
    # Purchase Request (PR) and the order is created when the PR is approved,
    # with awss_source_request_id set. A purchase order linked to a work order
    # without that source request would be an RFQ raised outside the approval
    # flow (the "Add a line" pop-up of the work order's Purchases tab used to
    # create exactly that), so refuse it whichever way it is attempted.
    def _check_sr_workorder_from_request(self, vals_list=None):
        message = _(
            "A purchase for a work order goes through a Purchase Request. "
            "Use the Create Purchase button of the work order."
        )
        if vals_list is not None:
            for vals in vals_list:
                if vals.get('sr_workorder_id') and not vals.get('awss_source_request_id'):
                    raise UserError(message)
            return
        if any(not order.awss_source_request_id for order in self):
            raise UserError(message)

    @api.model_create_multi
    def create(self, vals_list):
        self._check_sr_workorder_from_request(vals_list)
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('sr_workorder_id'):
            self._check_sr_workorder_from_request()
        return super().write(vals)

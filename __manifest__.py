{
    'name': 'SR Maintenance - AWSS Purchase Request Bridge',
    'version': '19.0.1.2.1',
    'summary': 'Links SR Maintenance work orders to AWSS Purchase Request instead of a raw Purchase Order',
    'description': """
SR Maintenance - AWSS Purchase Request Bridge
==============================================

Connects sr_maintenance's work orders to awss_purchase_request instead of
creating a native Purchase Order directly, so parts requested from a work
order go through AWSS's approval flow (department manager, Supply Chain,
CEO, Board) like every other purchase.

Entirely additive on both sides - awss_purchase_request and sr_maintenance
are not modified, only extended:

- Adds `sr_workorder_id` on `awss.purchase.request`, carried over to the
  `purchase.order` created on approval (sr_maintenance already has a
  `sr_workorder_id` field on `purchase.order` for its native flow - this
  reuses it instead of adding a second one).
- Overrides `sr.workorder.action_create_purchase()` to open a Purchase
  Request instead of a Purchase Order, pre-filled with the work order's
  parts and analytic distribution, opened with `analytic_locked` set so
  the department default never overwrites it.
- Overrides `sr.workorder.action_view_purchases()` to list the work
  order's Purchase Requests instead of Purchase Orders (a request already
  gives access to the resulting order once approved, via its own smart
  button).

Requires both sr_maintenance and awss_purchase_request >= 19.0.4.9
(analytic_locked and _prepare_purchase_order_vals were added in 4.9).
""",
    'author': 'Serge Rivoallan',
    'license': 'LGPL-3',
    'depends': [
        'sr_maintenance',
        'awss_purchase_request',
    ],
    'data': [
        'views/awss_purchase_request_views.xml',
        'views/sr_workorder_views.xml',
    ],
    'installable': True,
    'application': False,
}

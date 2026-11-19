# SR Maintenance - AWSS Purchase Request Bridge

Connects SR Maintenance's work orders to AWSS's Purchase Request
approval flow instead of creating a raw Purchase Order directly, so
parts requested from a work order go through the same approval chain
(department manager, Supply Chain, CEO, Board) as every other purchase
at AWSS.

## What it's for

SR Maintenance's native "New Purchase Order" button on a work order
creates a `purchase.order` directly. AWSS never allows that - every
purchase must go through `awss.purchase.request` first. This module is
a client-specific integration that bridges the two, entirely additively:
neither `sr_maintenance` nor `awss_purchase_request`'s own code is
modified, only extended.

## Features

- Adds `sr_workorder_id` on `awss.purchase.request` (surfaced on its
  form and list views), carried over to the resulting `purchase.order`
  once approved - reusing the `sr_workorder_id` field SR Maintenance
  already has on `purchase.order` for its native flow, instead of
  introducing a second one.
- Overrides `sr.workorder.action_create_purchase()` to open a Purchase
  Request instead of a Purchase Order, pre-filled with the work order's
  parts (product, quantity, unit price) and its analytic distribution on
  every line - opened with `analytic_locked` set so the requester's
  department default never overwrites it.
- Only real purchases go to approval. Parts the warehouse already holds
  (free quantity covers the need) are left out and issued from stock with
  Stock Issue; stocked parts running short that have an active Min/Max
  (reordering) rule are left out too and follow the replenishment process;
  a stocked part short with no Min/Max rule is requested for the missing
  quantity only; products that are not stocked (services...) are requested
  in full. Parts already issued are ignored. When nothing needs buying, a
  message says so instead of opening an empty request, and a note in the
  work order's chatter lists what was left out and why.
- Falls back to the current user's own employee record when the work
  order's requester has none linked, so the request can still resolve a
  department/approver.
- Overrides `sr.workorder.action_view_purchases()` to list the work
  order's Purchase Requests instead of Purchase Orders - a request
  already gives access to the resulting order once approved, via its own
  smart button.

## Dependencies

- `sr_maintenance`
- `awss_purchase_request` **>= 19.0.4.9** - `analytic_locked` and
  `_prepare_purchase_order_vals()` (the hook this module overrides) were
  both added in that version.

Targets **Odoo 19**.

## Installation

1. Place this module in the addons path, alongside SR Maintenance and
   AWSS's own `awss_purchase_request` module.
2. Restart Odoo.
3. Apps → Update Apps List → Install "SR Maintenance - AWSS Purchase
   Request Bridge".

## License

LGPL-3

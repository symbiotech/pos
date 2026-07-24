## Actions → Create Order

This path is available when **Create Sale Order when paying with
Customer Account** is disabled.

- Open your Point of Sale
- Create a new order and select products
- Select a customer
- Click on the **Create Order** button (under Actions)

![](../static/description/pos_frontend_button.png)

What happens next depends on **Default Sale Order Creation** in the PoS
settings:

- If set to **Ask** (default), a popup offers the options enabled for
  that PoS (see below).
- If set to a concrete state (**Draft**, **Confirmed**, **Delivered**,
  or **Invoiced**), the sale order is created immediately in that state
  and the current PoS order is discarded (no popup).

When **Ask** is selected, these options can be available (depending on
the PoS settings):

- **Create a draft Order** A new sale order in a draft mode will be
  created that can be changed later.
- **Create a Confirmed Order** A new sale order will be created and
  confirmed.
- **Create Delivered Sale Order** A new sale order will be created and
  confirmed. The associated picking will be marked as delivered.
- **Create Invoiced Sale Order** A new sale order will be created and
  confirmed. The associated picking will be marked as delivered. An
  invoice will be created and confirmed.

![](../static/description/pos_frontend_popup.png)

## Paying with Customer Account (optional)

When **Create Sale Order when paying with Customer Account** is enabled
and **Default Sale Order Creation** is a concrete state:

- The Actions → **Create Order** button is hidden
- Add products and select a customer
- Go to Payment, choose **Customer Account**, then **Validate**
- A sale order is created in the default state and the receipt screen
  is shown (as for a normal PoS payment)
- No Point of Sale order is saved
- Receipt email / SMS is hidden (there is no synced PoS order to send)

## Finding sale orders created from PoS

On Sales → Orders / Quotations:

- Use the **From Point of Sale** filter
- Optionally show the **PoS Session** column (list optional columns)
- On the order form (Other Info → Tracking), **PoS Session** is shown
  when set; **Source Document** also mentions the PoS session

## Daily shop sales

Point of Sale → Reporting → **Shop Sales (POS + Sale Orders)** shows
paid PoS orders and sale orders created from PoS in one list (default
filter: today). Use the pivot/graph views to total by day or source.
Open a row to jump to the related PoS order or sale order.

On Point of Sale → Orders → **Sessions**, the list also shows
**Shop Sales Amount** and **Shop Sales Count** (paid PoS orders plus
non-cancelled sale orders linked to each session).

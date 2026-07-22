/** @odoo-module **/

const CREATE_SALE_ORDER_DEFAULT_FLAGS = {
    draft: "iface_create_draft_sale_order",
    confirmed: "iface_create_confirmed_sale_order",
    delivered: "iface_create_delivered_sale_order",
    invoiced: "iface_create_invoiced_sale_order",
};

/**
 * Return the one-shot creation state from PoS config, or null to open the popup.
 */
export function getDefaultCreateSaleOrderState(config) {
    const orderState = config.iface_create_sale_order_default;
    const flag = CREATE_SALE_ORDER_DEFAULT_FLAGS[orderState];
    if (flag && config[flag]) {
        return orderState;
    }
    return null;
}

/**
 * Whether paying fully with Customer Account should create a sale order.
 */
export function shouldCreateSaleOrderOnValidate(config, order) {
    if (
        !config.iface_create_sale_order_on_validate ||
        !config.iface_create_sale_order ||
        !getDefaultCreateSaleOrderState(config)
    ) {
        return false;
    }
    if (!order?.getPartner?.() || !order.getOrderlines?.()?.length) {
        return false;
    }
    const payments = order.payment_ids || [];
    if (!payments.length) {
        return false;
    }
    return payments.every((payment) => payment.payment_method_id?.type === "pay_later");
}

/**
 * Create a sale order from the current PoS order.
 *
 * @param {Object} options
 * @param {Boolean} [options.removeOrder=true] Remove the PoS order after create.
 */
export async function createSaleOrderFromPos(pos, orm, ui, orderState, options = {}) {
    const {removeOrder = true} = options;
    const currentOrder = pos.getOrder();
    ui.block();
    try {
        await orm.call("sale.order", "create_order_from_pos", [
            currentOrder.serializeForORM({orm: true}),
            orderState,
        ]);
        if (removeOrder) {
            pos.removeOrder(currentOrder);
            pos.addNewOrder();
        }
    } finally {
        ui.unblock();
    }
}

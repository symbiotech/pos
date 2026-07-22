/** @odoo-module **/

import {
    getDefaultCreateSaleOrderState,
    shouldCreateSaleOrderOnValidate,
} from "@pos_order_to_sale_order/utils/create_sale_order_from_pos.esm";
import OrderPaymentValidation from "@point_of_sale/app/utils/order_payment_validation";
import {patch} from "@web/core/utils/patch";
import {serializeDateTime} from "@web/core/l10n/dates";

patch(OrderPaymentValidation.prototype, {
    shouldCreateSaleOrderOnValidate() {
        return shouldCreateSaleOrderOnValidate(this.pos.config, this.order);
    },

    async finalizeValidation() {
        if (this.shouldCreateSaleOrderOnValidate()) {
            return await this.finalizeSaleOrderFromPos();
        }
        return await super.finalizeValidation(...arguments);
    },

    async finalizeSaleOrderFromPos() {
        const order = this.order;
        const orderState = getDefaultCreateSaleOrderState(this.pos.config);

        // Already converted in this browser session (double Validate).
        if (order.uiState?.saleOrderConverted) {
            if (this.canPrintReceipt) {
                await this.pos.printReceipt({order});
            }
            return true;
        }

        try {
            // Ui.block is already held by shouldHideValidationBehindFeedbackScreen.
            const result = await this.pos.data.call(
                "sale.order",
                "create_order_from_pos",
                [order.serializeForORM({orm: true}), orderState]
            );

            order.date_order = serializeDateTime(luxon.DateTime.now());
            order.state = "paid";
            order.uiState.saleOrderConverted = true;
            order.uiState.saleOrderId = result?.sale_order_id;

            // Keep the order in memory for the receipt, but drop IndexedDB so a
            // reload cannot revive it as a pending pos.order.
            this.pos.forgetConvertedOrderFromIndexedDB(order);

            // Match afterOrderValidation print behavior without syncing a POS order.
            if (this.canPrintReceipt) {
                await this.pos.printReceipt({order});
            }
            return true;
        } catch (error) {
            return this.handleValidationError(error);
        }
    },
});

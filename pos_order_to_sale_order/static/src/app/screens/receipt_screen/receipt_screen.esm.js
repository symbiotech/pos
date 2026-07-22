/** @odoo-module **/

import {ReceiptScreen} from "@point_of_sale/app/screens/receipt_screen/receipt_screen";
import {patch} from "@web/core/utils/patch";

patch(ReceiptScreen.prototype, {
    /**
     * Converted orders are never synced as pos.order, so receipt email/SMS
     * cannot work (server needs a real pos.order id).
     */
    get canSendReceipt() {
        return !this.currentOrder?.uiState?.saleOrderConverted;
    },

    async _sendReceiptToCustomer() {
        if (!this.canSendReceipt) {
            return Promise.reject();
        }
        return await super._sendReceiptToCustomer(...arguments);
    },
});

/** @odoo-module **/

import {PosStore} from "@point_of_sale/app/services/pos_store";
import {patch} from "@web/core/utils/patch";

patch(PosStore.prototype, {
    /**
     * Finish core receipt navigation first, then drop the local draft.
     * Deleting before super.orderDone would break order.setScreenData().
     */
    orderDone(order) {
        const converted = order?.uiState?.saleOrderConverted && !order.isSynced;
        const result = super.orderDone(...arguments);
        if (converted) {
            this.data.localDeleteCascade(order);
        }
        return result;
    },

    /**
     * Converted orders have no server pos.order; editing payments is invalid.
     */
    canEditPayment(order) {
        if (order?.uiState?.saleOrderConverted) {
            return false;
        }
        return super.canEditPayment(...arguments);
    },

    /**
     * Never queue sale-order-converted drafts for POS sync.
     */
    addPendingOrder(orderIds, remove = false) {
        const filteredIds = (orderIds || []).filter((id) => {
            const order = this.models["pos.order"].get(id);
            return !(order?.uiState?.saleOrderConverted && !order.isSynced);
        });
        if (!filteredIds.length && !remove) {
            return;
        }
        return super.addPendingOrder(filteredIds, remove);
    },

    /**
     * Remove a converted order from IndexedDB but keep it in memory for the
     * receipt screen. Prevents a page reload from restoring a paid draft that
     * would sync as a real pos.order after the sale order already exists.
     */
    forgetConvertedOrderFromIndexedDB(order) {
        if (!order?.uuid || !this.data?.indexedDB?.delete) {
            return;
        }
        const toDelete = [["pos.order", order.uuid]];
        for (const line of order.lines || []) {
            if (line?.uuid) {
                toDelete.push(["pos.order.line", line.uuid]);
            }
        }
        for (const payment of order.payment_ids || []) {
            if (payment?.uuid) {
                toDelete.push(["pos.payment", payment.uuid]);
            }
        }
        for (const [model, uuid] of toDelete) {
            this.data.indexedDB.delete(model, [uuid]);
        }
    },
});

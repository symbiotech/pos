/** @odoo-module **/

import {PosStore} from "@point_of_sale/app/services/pos_store";
import {patch} from "@web/core/utils/patch";

patch(PosStore.prototype, {
    /**
     * Drop locally converted sale-order drafts without syncing a POS order.
     */
    orderDone(order) {
        if (order?.uiState?.saleOrderConverted && !order.isSynced) {
            this.data.localDeleteCascade(order);
        }
        return super.orderDone(...arguments);
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
});

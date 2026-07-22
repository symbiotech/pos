/** @odoo-module **/

import {
    createSaleOrderFromPos,
    getDefaultCreateSaleOrderState,
} from "@pos_order_to_sale_order/utils/create_sale_order_from_pos.esm";
import {Component} from "@odoo/owl";
import {CreateOrderPopup} from "@pos_order_to_sale_order/components/create_order_popup/create_order_popup.esm";
import {usePos} from "@point_of_sale/app/hooks/pos_hook";
import {useService} from "@web/core/utils/hooks";

export class CreateOrderButton extends Component {
    static template = "pos_order_to_sale_order.CreateOrderButton";
    static props = {
        close: {type: Function, optional: true},
    };
    setup() {
        this.pos = usePos();
        this.dialog = useService("dialog");
        this.orm = useService("orm");
        this.ui = useService("ui");
    }

    isEnabled() {
        const pos = this.pos;
        return (
            pos.config.iface_create_sale_order &&
            this.pos.getOrder().getPartner() &&
            this.pos.getOrder().getOrderlines().length !== 0
        );
    }

    async onClick(ev) {
        const orderState = getDefaultCreateSaleOrderState(this.pos.config);
        if (orderState) {
            // Keep Actions dialog mounted until create finishes (Dialog closes on click).
            ev.stopPropagation();
            await createSaleOrderFromPos(this.pos, this.orm, this.ui, orderState);
            this.props.close?.();
            return;
        }
        this.dialog.add(CreateOrderPopup);
    }
}

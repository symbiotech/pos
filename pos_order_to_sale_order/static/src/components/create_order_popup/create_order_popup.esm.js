/** @odoo-module **/

import {Component} from "@odoo/owl";
import {Dialog} from "@web/core/dialog/dialog";
import {createSaleOrderFromPos} from "@pos_order_to_sale_order/utils/create_sale_order_from_pos.esm";
import {usePos} from "@point_of_sale/app/hooks/pos_hook";
import {useService} from "@web/core/utils/hooks";

export class CreateOrderPopup extends Component {
    static template = "pos_order_to_sale_order.CreateOrderPopup";
    static components = {Dialog};
    static props = ["close"];

    setup() {
        super.setup();
        this.pos = usePos();
        this.ui = useService("ui");
        this.orm = useService("orm");
    }

    async createDraftSaleOrder() {
        await this._actionCreateSaleOrder("draft");
    }

    async createConfirmedSaleOrder() {
        await this._actionCreateSaleOrder("confirmed");
    }

    async createDeliveredSaleOrder() {
        await this._actionCreateSaleOrder("delivered");
    }

    async createInvoicedSaleOrder() {
        await this._actionCreateSaleOrder("invoiced");
    }

    async _actionCreateSaleOrder(orderState) {
        await createSaleOrderFromPos(this.pos, this.orm, this.ui, orderState);
        return this.props.close();
    }
}

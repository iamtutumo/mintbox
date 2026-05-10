odoo.define('risk_register.basic_action', function (require) {
    "use strict";

    console.log('BASIC ACTION: Loading basic action');

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');

    var BasicAction = AbstractAction.extend({
        start: function () {
            console.log('BASIC ACTION: Starting basic action');
            this.$el.html('<div class="container"><h1>Risk Dashboard</h1><p>Dashboard content goes here.</p></div>');
            return this._super.apply(this, arguments);
        }
    });

    // Register the action
    core.action_registry.add('risk_dashboard_action', BasicAction);
    console.log('BASIC ACTION: Action registered successfully');

    return BasicAction;
});

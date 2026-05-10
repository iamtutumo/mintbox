odoo.define('risk_register.dashboard_action_debug', ['web.core'], function (require) {
    "use strict";
    
    var core = require('web.core');
    
    console.log('Risk Dashboard Debug: Starting to load');
    
    var RiskDashboardActionDebug = core.Class.extend({
        init: function (parent, action) {
            this._super.apply(this, arguments);
            console.log('Risk Dashboard Debug: Initialized');
        },
        
        start: function () {
            console.log('Risk Dashboard Debug: Started');
            return this._super.apply(this, arguments);
        },
    });
    
    console.log('Risk Dashboard Debug: Registering action');
    core.action_registry.add('risk_dashboard_action', RiskDashboardActionDebug);
    console.log('Risk Dashboard Debug: Action registered successfully');
    
    return RiskDashboardActionDebug;
});

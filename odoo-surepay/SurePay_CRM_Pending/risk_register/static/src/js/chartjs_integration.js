odoo.define('risk_register.chartjs_integration', [], function (require) {
    "use strict";

    // Load Chart.js from CDN if not already loaded
    function loadChartJS() {
        return new Promise(function (resolve, reject) {
            if (typeof Chart !== 'undefined') {
                resolve();
                return;
            }

            var script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/chart.js';
            script.onload = function () {
                resolve();
            };
            script.onerror = function () {
                reject(new Error('Failed to load Chart.js'));
            };
            document.head.appendChild(script);
        });
    }

    return {
        loadChartJS: loadChartJS,
    };
});

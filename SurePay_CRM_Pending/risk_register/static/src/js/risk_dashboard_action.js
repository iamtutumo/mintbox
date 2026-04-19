odoo.define('risk_register.dashboard_action', ['web.core', 'web.rpc', 'web.Widget', 'web.field_utils', 'risk_register.chartjs_integration'], function (require) {
    "use strict";
    
    var core = require('web.core');
    var rpc = require('web.rpc');
    var Widget = require('web.Widget');
    var field_utils = require('web.field_utils');
    var chartjs_integration = require('risk_register.chartjs_integration');
    
    var RiskDashboardAction = Widget.extend({
        template: 'risk_dashboard_template',
        events: {
            'click .o_risk_refresh_btn': '_onRefresh',
        },
        
        /**
         * @override
         */
        init: function (parent, action) {
            this._super.apply(this, arguments);
            this.action = action;
            this.charts = {};
            this.auto_refresh_interval = null;
        },
        
        /**
         * @override
         */
        willStart: function () {
            var self = this;
            return chartjs_integration.loadChartJS()
                .then(function () {
                    return self._loadDashboardData();
                });
        },
        
        /**
         * @override
         */
        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                self._renderDashboard();
                self._startAutoRefresh();
            });
        },
        
        /**
         * @override
         */
        destroy: function () {
            this._stopAutoRefresh();
            this._destroyCharts();
            this._super.apply(this, arguments);
        },
        
        /**
         * Load dashboard data from server
         * @private
         */
        _loadDashboardData: function () {
            var self = this;
            return rpc.query({
                model: 'risk.register',
                method: 'get_dashboard_data',
                args: [],
                kwargs: {},
            }).then(function (result) {
                self.dashboard_data = result;
                return result;
            });
        },
        
        /**
         * Render the dashboard
         * @private
         */
        _renderDashboard: function () {
            if (!this.dashboard_data) {
                return;
            }
            
            this._renderStatsCards();
            this._renderRiskLevelChart();
            this._renderDepartmentChart();
            this._renderStatusChart();
            this._renderTimelineChart();
            this._renderDepartmentStatusChart();
            this._renderImpactLikelihoodChart();
            this._renderRiskDistributionChart();
            this._renderOverdueAnalysis();
            this._renderTopHighRisks();
            this._renderRecentActivities();
        },
        
        /**
         * Render statistics cards
         * @private
         */
        _renderStatsCards: function () {
            var data = this.dashboard_data;
            
            this.$('.o_risk_total_risks').text(data.total_risks || 0);
            this.$('.o_risk_overdue_risks').text(data.overdue_risks || 0);
            this.$('.o_risk_mitigated_risks').text(data.mitigated_risks || 0);
            this.$('.o_risk_avg_risk_score').text((data.avg_risk_score || 0).toFixed(1));
        },
        
        /**
         * Render risk level chart
         * @private
         */
        _renderRiskLevelChart: function () {
            var canvas = this.$('#risk_level_chart')[0];
            if (!canvas) return;
            
            var data = this.dashboard_data.risk_level_data;
            if (!data) return;
            
            this._destroyChart('risk_level');
            
            this.charts.risk_level = new Chart(canvas, {
                type: 'pie',
                data: {
                    labels: data.labels || [],
                    datasets: [{
                        data: data.values || [],
                        backgroundColor: [
                            '#28a745', // Low - Green
                            '#ffc107', // Medium - Yellow
                            '#fd7e14', // High - Orange
                            '#dc3545', // Critical - Red
                        ],
                    }],
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom',
                        },
                        title: {
                            display: true,
                            text: 'Risks by Level',
                        },
                    },
                },
            });
        },
        
        /**
         * Render department chart
         * @private
         */
        _renderDepartmentChart: function () {
            var canvas = this.$('#department_chart')[0];
            if (!canvas) return;
            
            var data = this.dashboard_data.department_data;
            if (!data) return;
            
            this._destroyChart('department');
            
            this.charts.department = new Chart(canvas, {
                type: 'bar',
                data: {
                    labels: data.labels || [],
                    datasets: [{
                        label: 'Number of Risks',
                        data: data.values || [],
                        backgroundColor: '#007bff',
                    }],
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            display: false,
                        },
                        title: {
                            display: true,
                            text: 'Risks by Department',
                        },
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                stepSize: 1,
                            },
                        },
                    },
                },
            });
        },
        
        /**
         * Render status chart
         * @private
         */
        _renderStatusChart: function () {
            var canvas = this.$('#status_chart')[0];
            if (!canvas) return;
            
            var data = this.dashboard_data.status_data;
            if (!data) return;
            
            this._destroyChart('status');
            
            this.charts.status = new Chart(canvas, {
                type: 'doughnut',
                data: {
                    labels: data.labels || [],
                    datasets: [{
                        data: data.values || [],
                        backgroundColor: [
                            '#17a2b8', // Identified - Cyan
                            '#ffc107', // Assessed - Yellow
                            '#fd7e14', // Mitigated - Orange
                            '#28a745', // Accepted - Green
                            '#dc3545', // Rejected - Red
                        ],
                    }],
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom',
                        },
                        title: {
                            display: true,
                            text: 'Risks by Status',
                        },
                    },
                },
            });
        },
        
        /**
         * Render timeline chart
         * @private
         */
        _renderTimelineChart: function () {
            var canvas = this.$('#timeline_chart')[0];
            if (!canvas) return;
            
            var data = this.dashboard_data.timeline_data;
            if (!data) return;
            
            this._destroyChart('timeline');
            
            this.charts.timeline = new Chart(canvas, {
                type: 'line',
                data: {
                    labels: data.labels || [],
                    datasets: [{
                        label: 'Risks Created',
                        data: data.values || [],
                        borderColor: '#007bff',
                        backgroundColor: 'rgba(0, 123, 255, 0.1)',
                        fill: true,
                    }],
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            display: false,
                        },
                        title: {
                            display: true,
                            text: 'Risks Created Over Time',
                        },
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                stepSize: 1,
                            },
                        },
                    },
                },
            });
        },
        
        /**
         * Render department status chart
         * @private
         */
        _renderDepartmentStatusChart: function () {
            var canvas = this.$('#department_status_chart')[0];
            if (!canvas) return;
            
            var data = this.dashboard_data.department_status_data;
            if (!data) return;
            
            this._destroyChart('department_status');
            
            var datasets = [];
            var colors = ['#17a2b8', '#ffc107', '#fd7e14', '#28a745', '#dc3545'];
            
            if (data.datasets) {
                for (var i = 0; i < data.datasets.length; i++) {
                    datasets.push({
                        label: data.datasets[i].label,
                        data: data.datasets[i].data,
                        backgroundColor: colors[i % colors.length],
                    });
                }
            }
            
            this.charts.department_status = new Chart(canvas, {
                type: 'bar',
                data: {
                    labels: data.labels || [],
                    datasets: datasets,
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom',
                        },
                        title: {
                            display: true,
                            text: 'Department Status Matrix',
                        },
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                stepSize: 1,
                            },
                        },
                    },
                },
            });
        },
        
        /**
         * Render impact vs likelihood chart
         * @private
         */
        _renderImpactLikelihoodChart: function () {
            var canvas = this.$('#impact_likelihood_chart')[0];
            if (!canvas) return;
            
            var data = this.dashboard_data.impact_likelihood_data;
            if (!data) return;
            
            this._destroyChart('impact_likelihood');
            
            var datasets = [];
            for (var i = 0; i < data.datasets.length; i++) {
                var dataset = data.datasets[i];
                datasets.push({
                    label: dataset.label,
                    data: dataset.data,
                    backgroundColor: dataset.backgroundColor,
                });
            }
            
            this.charts.impact_likelihood = new Chart(canvas, {
                type: 'bubble',
                data: {
                    datasets: datasets,
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom',
                        },
                        title: {
                            display: true,
                            text: 'Impact vs Likelihood',
                        },
                    },
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: 'Likelihood',
                            },
                            min: 1,
                            max: 5,
                        },
                        y: {
                            title: {
                                display: true,
                                text: 'Impact',
                            },
                            min: 1,
                            max: 5,
                        },
                    },
                },
            });
        },
        
        /**
         * Render risk distribution chart
         * @private
         */
        _renderRiskDistributionChart: function () {
            var canvas = this.$('#risk_distribution_chart')[0];
            if (!canvas) return;
            
            var data = this.dashboard_data.risk_distribution_data;
            if (!data) return;
            
            this._destroyChart('risk_distribution');
            
            this.charts.risk_distribution = new Chart(canvas, {
                type: 'polarArea',
                data: {
                    labels: data.labels || [],
                    datasets: [{
                        data: data.values || [],
                        backgroundColor: [
                            'rgba(40, 167, 69, 0.7)',
                            'rgba(255, 193, 7, 0.7)',
                            'rgba(253, 126, 20, 0.7)',
                            'rgba(220, 53, 69, 0.7)',
                            'rgba(108, 117, 125, 0.7)',
                        ],
                    }],
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom',
                        },
                        title: {
                            display: true,
                            text: 'Risk Distribution',
                        },
                    },
                    scales: {
                        r: {
                            beginAtZero: true,
                        },
                    },
                },
            });
        },
        
        /**
         * Render overdue analysis
         * @private
         */
        _renderOverdueAnalysis: function () {
            var data = this.dashboard_data;
            
            this.$('.o_risk_overdue_percentage').text((data.overdue_percentage || 0).toFixed(1) + '%');
            this.$('.o_risk_overdue_avg_days').text((data.overdue_avg_days || 0).toFixed(1));
        },
        
        /**
         * Render top high risks
         * @private
         */
        _renderTopHighRisks: function () {
            var data = this.dashboard_data.top_high_risks || [];
            var container = this.$('.o_risk_top_high_risks_list');
            
            container.empty();
            
            if (data.length === 0) {
                container.append('<p class="text-muted">No high risks found.</p>');
                return;
            }
            
            for (var i = 0; i < data.length; i++) {
                var risk = data[i];
                var item = $('<div class="list-group-item">');
                item.append('<h6 class="mb-1">' + (risk.name || 'Unnamed Risk') + '</h6>');
                item.append('<small class="text-muted">Risk Score: ' + (risk.risk_score || 0) + '</small>');
                if (risk.department_name) {
                    item.append('<br><small class="text-muted">Department: ' + risk.department_name + '</small>');
                }
                container.append(item);
            }
        },
        
        /**
         * Render recent activities
         * @private
         */
        _renderRecentActivities: function () {
            var data = this.dashboard_data.recent_activities || [];
            var container = this.$('.o_risk_recent_activities_list');
            
            container.empty();
            
            if (data.length === 0) {
                container.append('<p class="text-muted">No recent activities.</p>');
                return;
            }
            
            for (var i = 0; i < data.length; i++) {
                var activity = data[i];
                var item = $('<div class="list-group-item">');
                item.append('<h6 class="mb-1">' + (activity.description || 'Activity') + '</h6>');
                item.append('<small class="text-muted">' + (activity.date || '') + '</small>');
                if (activity.user_name) {
                    item.append('<br><small class="text-muted">By: ' + activity.user_name + '</small>');
                }
                container.append(item);
            }
        },
        
        /**
         * Start auto refresh
         * @private
         */
        _startAutoRefresh: function () {
            var self = this;
            this.auto_refresh_interval = setInterval(function () {
                self._refreshDashboard();
            }, 300000); // 5 minutes
        },
        
        /**
         * Stop auto refresh
         * @private
         */
        _stopAutoRefresh: function () {
            if (this.auto_refresh_interval) {
                clearInterval(this.auto_refresh_interval);
                this.auto_refresh_interval = null;
            }
        },
        
        /**
         * Refresh dashboard
         * @private
         */
        _refreshDashboard: function () {
            var self = this;
            this._loadDashboardData().then(function () {
                self._renderDashboard();
            });
        },
        
        /**
         * Handle refresh button click
         * @private
         */
        _onRefresh: function () {
            this._refreshDashboard();
        },
        
        /**
         * Destroy a specific chart
         * @param {string} chartName
         * @private
         */
        _destroyChart: function (chartName) {
            if (this.charts[chartName]) {
                this.charts[chartName].destroy();
                this.charts[chartName] = null;
            }
        },
        
        /**
         * Destroy all charts
         * @private
         */
        _destroyCharts: function () {
            for (var chartName in this.charts) {
                this._destroyChart(chartName);
            }
        },
    });
    
    core.action_registry.add('risk_dashboard_action', RiskDashboardAction);
    return RiskDashboardAction;
});

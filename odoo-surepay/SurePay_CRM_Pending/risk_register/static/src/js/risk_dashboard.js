odoo.define('risk_register.dashboard', ['web.core', 'web.rpc', 'web.Widget', 'web.field_utils', 'risk_register.chartjs_integration'], function (require) {
    "use strict";

    var core = require('web.core');
    var rpc = require('web.rpc');
    var Widget = require('web.Widget');
    var field_utils = require('web.field_utils');
    var chartjs_integration = require('risk_register.chartjs_integration');

    var RiskDashboard = Widget.extend({
        template: 'risk_dashboard_template',
        events: {
            'click .refresh-dashboard': '_onRefreshDashboard',
        },

        init: function (parent, options) {
            this._super.apply(this, arguments);
            this.risk_data = {};
            this.charts = {};
            this.auto_refresh_interval = null;
        },

        willStart: function () {
            var self = this;
            return chartjs_integration.loadChartJS().then(function () {
                return self._loadDashboardData();
            }).then(function () {
                return self._super.apply(self, arguments);
            });
        },

        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                self._renderDashboard();
                self._startAutoRefresh();
                self._setupRealtimeUpdates();
            });
        },

        _loadDashboardData: function () {
            var self = this;
            return rpc.query({
                model: 'risk.register',
                method: 'get_dashboard_data',
                args: [],
            }).then(function (result) {
                self.risk_data = result;
            });
        },

        _renderDashboard: function () {
            this._updateStatsCards();
            this._renderRiskLevelChart();
            this._renderDepartmentChart();
            this._renderStatusChart();
            this._renderTimelineChart();
            this._renderDepartmentStatusChart();
            this._renderImpactLikelihoodChart();
            this._renderRiskDistributionChart();
            this._updateOverdueAnalysis();
            this._renderTopHighRisks();
            this._renderRecentActivities();
        },

        _updateStatsCards: function () {
            var data = this.risk_data;
            
            // Update total risks
            $('#total_risks').text(data.total_risks || 0);
            
            // Update overdue risks
            $('#overdue_risks').text(data.overdue_risks || 0);
            
            // Update mitigated risks
            $('#mitigated_risks').text(data.mitigated_risks || 0);
            
            // Update average risk score
            $('#avg_risk_score').text(data.avg_risk_score || 0);
        },

        _renderRiskLevelChart: function () {
            var data = this.risk_data.risks_by_level || {};
            var ctx = document.getElementById('risk_level_chart');
            if (!ctx) return;

            if (this.charts.risk_level) {
                this.charts.risk_level.destroy();
            }

            this.charts.risk_level = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: Object.keys(data),
                    datasets: [{
                        data: Object.values(data),
                        backgroundColor: [
                            '#28a745', // Low - Green
                            '#ffc107', // Medium - Yellow
                            '#dc3545', // High - Red
                            '#343a40'  // Critical - Dark
                        ],
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Risks by Level'
                        },
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        },

        _renderDepartmentChart: function () {
            var data = this.risk_data.risks_by_department || {};
            var ctx = document.getElementById('department_chart');
            if (!ctx) return;

            if (this.charts.department) {
                this.charts.department.destroy();
            }

            this.charts.department = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: Object.keys(data),
                    datasets: [{
                        label: 'Number of Risks',
                        data: Object.values(data),
                        backgroundColor: '#007bff',
                        borderColor: '#0056b3',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Risks by Department'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                stepSize: 1
                            }
                        }
                    }
                }
            });
        },

        _renderStatusChart: function () {
            var data = this.risk_data.risks_by_status || {};
            var ctx = document.getElementById('status_chart');
            if (!ctx) return;

            if (this.charts.status) {
                this.charts.status.destroy();
            }

            this.charts.status = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: Object.keys(data),
                    datasets: [{
                        data: Object.values(data),
                        backgroundColor: [
                            '#6c757d', // Draft - Gray
                            '#007bff', // Active - Blue
                            '#ffc107', // Mitigated - Yellow
                            '#28a745'  // Closed - Green
                        ],
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Risks by Status'
                        },
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        },

        _renderTimelineChart: function () {
            var data = this.risk_data.risks_over_time || {};
            var ctx = document.getElementById('timeline_chart');
            if (!ctx) return;

            if (this.charts.timeline) {
                this.charts.timeline.destroy();
            }

            this.charts.timeline = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: Object.keys(data),
                    datasets: [{
                        label: 'Risks Created',
                        data: Object.values(data),
                        borderColor: '#007bff',
                        backgroundColor: 'rgba(0, 123, 255, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Risks Created Over Time'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                stepSize: 1
                            }
                        }
                    }
                }
            });
        },

        _onRefreshDashboard: function () {
            var self = this;
            this._loadDashboardData().then(function () {
                self._renderDashboard();
            });
        },

        _startAutoRefresh: function () {
            var self = this;
            // Clear any existing interval
            if (this.auto_refresh_interval) {
                clearInterval(this.auto_refresh_interval);
            }
            // Auto-refresh every 30 seconds
            this.auto_refresh_interval = setInterval(function () {
                self._onRefreshDashboard();
            }, 30000);
        },

        _setupRealtimeUpdates: function () {
            var self = this;
            // Listen for model changes using Odoo's bus
            if (this.env && this.env.bus) {
                this.env.bus.on('risk_register_updated', this, function (data) {
                    self._loadDashboardData().then(function () {
                        self._renderDashboard();
                    });
                });
            }
            
            // Fallback: periodic checks for new records
            this._startPeriodicChecks();
        },

        _startPeriodicChecks: function () {
            var self = this;
            var last_check = new Date();
            
            // Check for new records every 10 seconds
            setInterval(function () {
                rpc.query({
                    model: 'risk.register',
                    method: 'search_read',
                    args: [[['write_date', '>', last_check.toISOString()]]],
                    fields: ['id', 'name', 'write_date'],
                    limit: 1
                }).then(function (records) {
                    if (records.length > 0) {
                        last_check = new Date();
                        self._onRefreshDashboard();
                    }
                });
            }, 10000);
        },

        _renderDepartmentStatusChart: function () {
            var data = this.risk_data.department_status_breakdown || {};
            var ctx = document.getElementById('department_status_chart');
            if (!ctx) return;

            if (this.charts.department_status) {
                this.charts.department_status.destroy();
            }

            var departments = Object.keys(data);
            var statuses = ['draft', 'active', 'mitigated', 'closed'];
            var datasets = [];
            var colors = {
                'draft': '#6c757d',
                'active': '#dc3545',
                'mitigated': '#ffc107',
                'closed': '#28a745'
            };

            statuses.forEach(function (status) {
                var status_data = departments.map(function (dept) {
                    return data[dept][status] || 0;
                });
                datasets.push({
                    label: status.charAt(0).toUpperCase() + status.slice(1),
                    data: status_data,
                    backgroundColor: colors[status],
                    borderColor: colors[status],
                    borderWidth: 1
                });
            });

            this.charts.department_status = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: departments,
                    datasets: datasets
                },
                options: {
                    responsive: true,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Risk Status by Department'
                        },
                        legend: {
                            display: true,
                            position: 'top'
                        }
                    },
                    scales: {
                        x: {
                            stacked: true,
                            title: {
                                display: true,
                                text: 'Department'
                            }
                        },
                        y: {
                            stacked: true,
                            title: {
                                display: true,
                                text: 'Number of Risks'
                            },
                            beginAtZero: true
                        }
                    }
                }
            });
        },

        _renderImpactLikelihoodChart: function () {
            var data = this.risk_data.impact_likelihood_matrix || {};
            var ctx = document.getElementById('impact_likelihood_chart');
            if (!ctx) return;

            if (this.charts.impact_likelihood) {
                this.charts.impact_likelihood.destroy();
            }

            var impacts = ['Low', 'Medium', 'High'];
            var likelihoods = ['Low', 'Medium', 'High'];
            var matrix_data = [];

            impacts.forEach(function (impact) {
                likelihoods.forEach(function (likelihood) {
                    var key = impact + '_' + likelihood;
                    matrix_data.push({
                        x: likelihood,
                        y: impact,
                        v: data[key] || 0
                    });
                });
            });

            this.charts.impact_likelihood = new Chart(ctx, {
                type: 'bubble',
                data: {
                    datasets: [{
                        label: 'Risk Count',
                        data: matrix_data.map(function (item) {
                            return {
                                x: likelihoods.indexOf(item.x),
                                y: impacts.indexOf(item.y),
                                r: Math.max(5, Math.sqrt(item.v) * 3)
                            };
                        }),
                        backgroundColor: 'rgba(220, 53, 69, 0.6)',
                        borderColor: 'rgba(220, 53, 69, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Impact vs Likelihood Matrix'
                        },
                        tooltip: {
                            callbacks: {
                                label: function (context) {
                                    var item = matrix_data[context.dataIndex];
                                    return item.v + ' risks (' + item.y + ' Impact, ' + item.x + ' Likelihood)';
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            type: 'linear',
                            position: 'bottom',
                            min: -0.5,
                            max: 2.5,
                            ticks: {
                                stepSize: 1,
                                callback: function (value) {
                                    return likelihoods[value] || '';
                                }
                            },
                            title: {
                                display: true,
                                text: 'Likelihood'
                            }
                        },
                        y: {
                            min: -0.5,
                            max: 2.5,
                            ticks: {
                                stepSize: 1,
                                callback: function (value) {
                                    return impacts[value] || '';
                                }
                            },
                            title: {
                                display: true,
                                text: 'Impact'
                            }
                        }
                    }
                }
            });
        },

        _renderRiskDistributionChart: function () {
            var data = this.risk_data.risk_distribution || {};
            var ctx = document.getElementById('risk_distribution_chart');
            if (!ctx) return;

            if (this.charts.risk_distribution) {
                this.charts.risk_distribution.destroy();
            }

            this.charts.risk_distribution = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: Object.keys(data),
                    datasets: [{
                        data: Object.values(data),
                        backgroundColor: [
                            '#17a2b8', // Info
                            '#6f42c1', // Purple
                            '#fd7e14', // Orange
                            '#20c997', // Teal
                            '#e83e8c'  // Pink
                        ],
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Risk Distribution by Category'
                        },
                        legend: {
                            display: true,
                            position: 'right'
                        }
                    }
                }
            });
        },

        _updateOverdueAnalysis: function () {
            var data = this.risk_data.overdue_analysis || {};
            $('#avg_days_overdue').text(data.avg_days_overdue || 0);
            $('#max_days_overdue').text(data.max_days_overdue || 0);
        },

        _renderTopHighRisks: function () {
            var data = this.risk_data.top_high_risks || [];
            var container = $('#high_risks_list');
            container.empty();

            if (data.length === 0) {
                container.append('<div class="list-group-item text-muted">No high-risk items found</div>');
                return;
            }

            data.forEach(function (risk) {
                var risk_item = $('<div class="list-group-item">').html(
                    '<div class="d-flex justify-content-between align-items-center">' +
                    '<div>' +
                    '<h6 class="mb-1">' + risk.name + '</h6>' +
                    '<small class="text-muted">' + (risk.department || 'No Department') + '</small>' +
                    '</div>' +
                    '<span class="badge bg-danger rounded-pill">' + risk.risk_score + '</span>' +
                    '</div>'
                );
                container.append(risk_item);
            });
        },

        _renderRecentActivities: function () {
            var data = this.risk_data.recent_activities || [];
            var container = $('#activities_list');
            container.empty();

            if (data.length === 0) {
                container.append('<div class="list-group-item text-muted">No recent activities</div>');
                return;
            }

            data.forEach(function (activity) {
                var activity_item = $('<div class="list-group-item">').html(
                    '<div class="d-flex w-100 justify-content-between">' +
                    '<h6 class="mb-1">' + activity.description + '</h6>' +
                    '<small>' + activity.date + '</small>' +
                    '</div>' +
                    '<p class="mb-1">' + activity.user + ' - ' + activity.risk_name + '</p>' +
                    '<small class="text-muted">' + activity.details + '</small>'
                );
                container.append(activity_item);
            });
        },

        destroy: function () {
            // Clear auto-refresh interval
            if (this.auto_refresh_interval) {
                clearInterval(this.auto_refresh_interval);
            }
            
            // Destroy charts
            if (this.charts.risk_level) {
                this.charts.risk_level.destroy();
            }
            if (this.charts.department) {
                this.charts.department.destroy();
            }
            if (this.charts.status) {
                this.charts.status.destroy();
            }
            if (this.charts.timeline) {
                this.charts.timeline.destroy();
            }
            if (this.charts.department_status) {
                this.charts.department_status.destroy();
            }
            if (this.charts.impact_likelihood) {
                this.charts.impact_likelihood.destroy();
            }
            if (this.charts.risk_distribution) {
                this.charts.risk_distribution.destroy();
            }
            
            // Unsubscribe from bus events
            if (this.env && this.env.bus) {
                this.env.bus.off('risk_register_updated', this);
            }
            
            this._super.apply(this, arguments);
        }
    });

    // Note: This dashboard implementation is superseded by risk_dashboard_action.js
    // The action registration is handled in risk_dashboard_action.js to avoid conflicts
    
    return {
        RiskDashboard: RiskDashboard,
    };
});

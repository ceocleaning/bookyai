// Analytics Dashboard JavaScript

// Chart.js Configuration for Dark Theme
Chart.defaults.color = '#cecece';
Chart.defaults.borderColor = '#2c2c2c';
Chart.defaults.font.family = "'Outfit', sans-serif";

// Initialize charts when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeRevenueChart();
    initializeLeadSourceChart();
});

/**
 * Initialize Revenue Trend Chart (Line Chart)
 */
function initializeRevenueChart() {
    const ctx = document.getElementById('revenueChart');
    if (!ctx) return;
    
    // Fetch data from API
    fetch('/analytics/api/revenue-chart/')
        .then(response => response.json())
        .then(data => {
            const canvas = ctx.getContext('2d');
            
            // Create gradient for area fill
            const gradient = canvas.createLinearGradient(0, 0, 0, 350);
            gradient.addColorStop(0, 'rgba(17, 72, 191, 0.3)');
            gradient.addColorStop(1, 'rgba(17, 72, 191, 0)');
            
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Revenue ($)',
                        data: data.data,
                        borderColor: 'rgb(17, 72, 191)',
                        backgroundColor: gradient,
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        pointBackgroundColor: 'rgb(17, 72, 191)',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {
                        intersect: false,
                        mode: 'index',
                    },
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            padding: 12,
                            titleFont: {
                                size: 14,
                                weight: '600'
                            },
                            bodyFont: {
                                size: 13
                            },
                            callbacks: {
                                label: function(context) {
                                    let label = context.dataset.label || '';
                                    if (label) {
                                        label += ': ';
                                    }
                                    label += '$' + context.parsed.y.toFixed(2);
                                    return label;
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: 'rgba(255, 255, 255, 0.05)',
                                drawBorder: false
                            },
                            ticks: {
                                callback: function(value) {
                                    return '$' + value.toLocaleString();
                                }
                            }
                        },
                        x: {
                            grid: {
                                display: false,
                                drawBorder: false
                            }
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error('Error loading revenue chart:', error);
            showChartError(ctx, 'Failed to load revenue data');
        });
}

/**
 * Initialize Lead Source Chart (Doughnut Chart)
 */
function initializeLeadSourceChart() {
    const ctx = document.getElementById('leadSourceChart');
    if (!ctx) return;
    
    // Fetch data from API
    fetch('/analytics/api/lead-source-chart/')
        .then(response => response.json())
        .then(data => {
            // Define color palette for lead sources
            const colors = [
                'rgb(17, 72, 191)',    // Primary blue
                '#10B981',              // Success green
                '#F59E0B',              // Warning orange
                '#EF4444',              // Error red
                '#3B82F6',              // Info blue
                '#8B5CF6',              // Purple
                '#14B8A6',              // Teal
            ];
            
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: data.labels,
                    datasets: [{
                        data: data.data,
                        backgroundColor: colors.slice(0, data.labels.length),
                        borderColor: '#2c2c2c',
                        borderWidth: 2,
                        hoverOffset: 10
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                padding: 15,
                                font: {
                                    size: 12
                                },
                                usePointStyle: true,
                                pointStyle: 'circle'
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            padding: 12,
                            titleFont: {
                                size: 14,
                                weight: '600'
                            },
                            bodyFont: {
                                size: 13
                            },
                            callbacks: {
                                label: function(context) {
                                    const label = context.label || '';
                                    const value = context.parsed;
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = ((value / total) * 100).toFixed(1);
                                    return label + ': ' + value + ' (' + percentage + '%)';
                                }
                            }
                        }
                    },
                    cutout: '60%'
                }
            });
        })
        .catch(error => {
            console.error('Error loading lead source chart:', error);
            showChartError(ctx, 'Failed to load lead source data');
        });
}

/**
 * Show error message in chart container
 */
function showChartError(canvas, message) {
    const container = canvas.parentElement;
    container.innerHTML = `
        <div class="chart-loading">
            <div class="text-center">
                <i class="fas fa-exclamation-triangle text-warning mb-3"></i>
                <p class="text-muted mb-0">${message}</p>
            </div>
        </div>
    `;
}

/**
 * Format number as currency
 */
function formatCurrency(value) {
    return '$' + parseFloat(value).toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,');
}

/**
 * Format number with commas
 */
function formatNumber(value) {
    return value.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

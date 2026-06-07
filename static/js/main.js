// StockVision AI Frontend Scripts

// FAQ Accordion functionality
document.addEventListener('DOMContentLoaded', () => {
    const faqItems = document.querySelectorAll('.accordion-custom-item');
    faqItems.forEach(item => {
        item.addEventListener('click', () => {
            const answer = item.querySelector('.accordion-custom-answer');
            const isVisible = answer.style.display === 'block';
            
            // Close all answers
            document.querySelectorAll('.accordion-custom-answer').forEach(ans => {
                ans.style.display = 'none';
            });
            
            // Toggle active
            if (!isVisible && answer) {
                answer.style.display = 'block';
            }
        });
    });
});

// Cache for stock historical chart instance
let historicalChartInstance = null;

// Renders the main historical stock chart
function initHistoricalChart(ticker, defaultPeriod = '1m') {
    const ctx = document.getElementById('historicalStockChart');
    if (!ctx) return;
    
    updateHistoricalChart(ticker, defaultPeriod);
    
    // Bind click events to period filter buttons
    const buttons = document.querySelectorAll('.period-btn');
    buttons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            // Remove active class
            buttons.forEach(b => b.classList.remove('active', 'btn-primary-custom'));
            buttons.forEach(b => b.classList.add('btn-outline-custom'));
            
            // Set active class
            e.target.classList.remove('btn-outline-custom');
            e.target.classList.add('active', 'btn-primary-custom');
            
            const period = e.target.dataset.period;
            updateHistoricalChart(ticker, period);
        });
    });
}

function updateHistoricalChart(ticker, period) {
    const ctx = document.getElementById('historicalStockChart').getContext('2d');
    const spinner = document.getElementById('chartSpinner');
    
    if (spinner) spinner.style.display = 'block';
    
    fetch(`/api/historical/${ticker}?period=${period}`)
        .then(response => {
            if (!response.ok) throw new Error('Data fetch failed');
            return response.json();
        })
        .then(data => {
            if (spinner) spinner.style.display = 'none';
            
            const dates = data.dates;
            const prices = data.prices;
            
            if (historicalChartInstance) {
                historicalChartInstance.destroy();
            }
            
            // Create gradient fill
            const gradient = ctx.createLinearGradient(0, 0, 0, 400);
            gradient.addColorStop(0, 'rgba(99, 102, 241, 0.4)');
            gradient.addColorStop(1, 'rgba(99, 102, 241, 0.0)');
            
            historicalChartInstance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: dates,
                    datasets: [{
                        label: `${ticker} Price`,
                        data: prices,
                        borderColor: '#6366f1',
                        borderWidth: 2,
                        backgroundColor: gradient,
                        fill: true,
                        tension: 0.1,
                        pointRadius: prices.length > 100 ? 0 : 2,
                        pointHoverRadius: 5
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            mode: 'index',
                            intersect: false,
                            backgroundColor: '#111827',
                            borderColor: '#374151',
                            borderWidth: 1,
                            titleColor: '#94a3b8',
                            bodyColor: '#f8fafc',
                            callbacks: {
                                label: function(context) {
                                    return ` $${context.raw.toFixed(2)}`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: {
                                color: 'rgba(255, 255, 255, 0.03)'
                            },
                            ticks: {
                                color: '#64748b',
                                maxTicksLimit: 8
                            }
                        },
                        y: {
                            grid: {
                                color: 'rgba(255, 255, 255, 0.03)'
                            },
                            ticks: {
                                color: '#64748b',
                                callback: function(value) {
                                    return '$' + value.toFixed(2);
                                }
                            }
                        }
                    }
                }
            });
        })
        .catch(err => {
            console.error('Error fetching chart data:', err);
            if (spinner) spinner.style.display = 'none';
            const errorContainer = document.getElementById('chartError');
            if (errorContainer) {
                errorContainer.innerText = 'Failed to load chart data. Please try again.';
                errorContainer.style.display = 'block';
            }
        });
}

// Renders the Actual vs Predicted (Model Validation) Chart
function initModelPerformanceChart(evalData) {
    const ctx = document.getElementById('modelPerformanceChart');
    if (!ctx || !evalData) return;
    
    const context = ctx.getContext('2d');
    const dates = evalData.dates;
    const actual = evalData.actual;
    const predicted_rf = evalData.predicted_rf;
    const predicted_lr = evalData.predicted_lr;
    
    new Chart(context, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [
                {
                    label: 'Actual Closing Price',
                    data: actual,
                    borderColor: '#10b981',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.1,
                    pointRadius: 2
                },
                {
                    label: 'Random Forest Prediction',
                    data: predicted_rf,
                    borderColor: '#6366f1',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    fill: false,
                    tension: 0.1,
                    pointRadius: 2
                },
                {
                    label: 'Linear Regression Baseline',
                    data: predicted_lr,
                    borderColor: '#94a3b8',
                    borderWidth: 1.5,
                    borderDash: [2, 2],
                    fill: false,
                    tension: 0.1,
                    pointRadius: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: '#f8fafc',
                        font: {
                            family: 'Plus Jakarta Sans'
                        }
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: '#111827',
                    borderColor: '#374151',
                    borderWidth: 1,
                    titleColor: '#94a3b8',
                    bodyColor: '#f8fafc',
                    callbacks: {
                        label: function(context) {
                            return ` ${context.dataset.label}: $${context.raw.toFixed(2)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.03)'
                    },
                    ticks: {
                        color: '#64748b',
                        maxTicksLimit: 6
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.03)'
                    },
                    ticks: {
                        color: '#64748b',
                        callback: function(value) {
                            return '$' + value.toFixed(2);
                        }
                    }
                }
            }
        }
    });
}

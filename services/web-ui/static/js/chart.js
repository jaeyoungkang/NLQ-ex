const ChartManager = {
    currentChart: null,

    createChart(data, config) {
        const canvas = document.getElementById('analysisChart');
        if (!canvas || !data?.length) return null;

        // 기존 차트 제거
        if (this.currentChart) {
            this.currentChart.destroy();
        }

        const ctx = canvas.getContext('2d');
        const chartData = this.prepareChartData(data, config);

        this.currentChart = new Chart(ctx, {
            type: config.type,
            data: chartData,
            options: this.getChartOptions(config)
        });

        return this.currentChart;
    },

    prepareChartData(data, config) {
        const colors = ['#4285f4', '#34a853', '#fbbc05', '#ea4335', '#9c27b0'];
        
        if (config.type === 'bar' && config.label_column && config.value_column) {
            return {
                labels: data.slice(0, 10).map(row => String(row[config.label_column])),
                datasets: [{
                    label: config.value_column,
                    data: data.slice(0, 10).map(row => Number(row[config.value_column]) || 0),
                    backgroundColor: colors.map(color => color + '80'),
                    borderColor: colors,
                    borderWidth: 2
                }]
            };
        }
        
        return {};
    },

    getChartOptions(config) {
        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: config.title,
                    font: { size: 16, weight: 'bold' }
                },
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value.toLocaleString();
                        }
                    }
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeOutQuart'
            }
        };
    },

    destroyChart() {
        if (this.currentChart) {
            this.currentChart.destroy();
            this.currentChart = null;
        }
    }
};
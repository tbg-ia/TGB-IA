// Trading related JavaScript functions

function updateTradingChart(data) {
    const ctx = document.getElementById('tradingChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Portfolio Value',
                data: data.values,
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
}

function toggleBot(botId) {
    fetch(`/bot/${botId}/toggle`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update UI accordingly
            updateBotStatus(botId, data.active);
        }
    })
    .catch(error => console.error('Error:', error));
}

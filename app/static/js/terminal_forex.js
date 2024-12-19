
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar TradingView
    let widget = new TradingView.widget({
        "width": "100%",
        "height": 500,
        "symbol": "FX:EURUSD",
        "interval": "15",
        "timezone": "Etc/UTC",
        "theme": "dark",
        "style": "1",
        "locale": "es",
        "toolbar_bg": "#f1f3f6",
        "enable_publishing": false,
        "withdateranges": true,
        "hide_side_toolbar": false,
        "allow_symbol_change": true,
        "details": true,
        "studies": [
            "RSI@tv-basicstudies",
            "MASimple@tv-basicstudies",
            "MACD@tv-basicstudies"
        ],
        "container_id": "tradingview_chart"
    });

    const tradeForm = document.getElementById('tradeForm');
    const instrument = document.getElementById('instrument');

    instrument.addEventListener('change', function() {
        let pair = this.value.replace('_', '');
        widget.chart().setSymbol(`FX:${pair}`);
    });

    tradeForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const webhookUrl = document.getElementById('webhook_url').value;
        const data = {
            symbol: document.getElementById('instrument').value,
            units: parseInt(document.getElementById('units').value),
            side: document.getElementById('side').value,
            take_profit: document.getElementById('take_profit').value || null,
            stop_loss: document.getElementById('stop_loss').value || null
        };

        try {
            // Send to webhook
            const webhookResponse = await fetch(webhookUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            if (webhookResponse.ok) {
                alert('Order sent to webhook successfully');
                updateTrades();
            } else {
                alert('Error sending order to webhook');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error executing order');
        }
    });

    function updateTrades() {
        fetch('/api/forex/trades')
            .then(response => response.json())
            .then(data => {
                const tbody = document.getElementById('tradesList');
                tbody.innerHTML = '';
                data.trades?.forEach(trade => {
                    tbody.innerHTML += `
                        <tr>
                            <td>${trade.instrument}</td>
                            <td>${trade.side}</td>
                            <td>${trade.units}</td>
                            <td>${trade.price}</td>
                            <td>${trade.pnl || 'Calculating...'}</td>
                            <td>
                                ${trade.status === 'OPEN' ? 
                                    `<button class="btn btn-danger btn-sm" onclick="closeTrade(${trade.id})">Close</button>` :
                                    'Closed'}
                            </td>
                        </tr>
                    `;
                });
            })
            .catch(console.error);
    }

    setInterval(updateTrades, 5000);
    updateTrades();
});

function closeTrade(tradeId) {
    if (!confirm('¿Estás seguro de que deseas cerrar esta operación?')) return;
    
    fetch(`/api/forex/trades/${tradeId}/close`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Trade closed successfully');
            updateTrades();
        } else {
            alert(`Error: ${data.error}`);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error closing trade');
    });
}

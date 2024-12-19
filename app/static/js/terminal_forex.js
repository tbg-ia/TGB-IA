
document.addEventListener('DOMContentLoaded', function() {
    // Initialize TradingView widget
    new TradingView.widget({
        "width": "100%",
        "height": 400,
        "symbol": "FX:EURUSD",
        "interval": "15",
        "timezone": "Etc/UTC",
        "theme": "dark",
        "style": "1",
        "locale": "en",
        "toolbar_bg": "#f1f3f6",
        "enable_publishing": false,
        "hide_side_toolbar": false,
        "allow_symbol_change": true,
        "container_id": "tradingview_chart"
    });

    const tradeForm = document.getElementById('tradeForm');
    const instrument = document.getElementById('instrument');

    instrument.addEventListener('change', function() {
        let pair = this.value.replace('_', '');
        widget.chart().setSymbol(`FX:${pair}`);
    });

    // Handle form submission
    tradeForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const data = {
            symbol: document.getElementById('instrument').value,
            side: document.getElementById('side').value,
            units: parseInt(document.getElementById('units').value),
            take_profit: document.getElementById('take_profit').value || null,
            stop_loss: document.getElementById('stop_loss').value || null
        };

        try {
            const response = await fetch('/api/forex/order', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();
            
            if (result.success) {
                alert('Order placed successfully');
                updateTrades();
            } else {
                alert(`Error: ${result.error}`);
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error placing order');
        }
    });

    // Update active trades list
    function updateTrades() {
        fetch('/api/forex/positions')
            .then(response => response.json())
            .then(data => {
                const tbody = document.getElementById('tradesList');
                tbody.innerHTML = '';
                
                data.positions?.forEach(trade => {
                    tbody.innerHTML += `
                        <tr>
                            <td>${trade.instrument}</td>
                            <td>${trade.side}</td>
                            <td>${trade.units}</td>
                            <td>${trade.openPrice}</td>
                            <td>${trade.currentPnl || 'Calculating...'}</td>
                            <td>
                                <button class="btn btn-danger btn-sm" onclick="closeTrade('${trade.id}')">Close</button>
                            </td>
                        </tr>
                    `;
                });
            })
            .catch(console.error);
    }

    // Initialize trades list
    updateTrades();
    // Update every 5 seconds
    setInterval(updateTrades, 5000);
});

async function closeTrade(tradeId) {
    if (!confirm('Are you sure you want to close this trade?')) return;
    
    try {
        const response = await fetch(`/api/forex/position/${tradeId}/close`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        if (result.success) {
            alert('Trade closed successfully');
            updateTrades();
        } else {
            alert(`Error: ${result.error}`);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error closing trade');
    }
}

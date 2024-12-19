
document.addEventListener('DOMContentLoaded', function() {
    // Initialize TradingView widget with dark theme
    new TradingView.widget({
        "width": "100%",
        "height": 500,
        "symbol": "FX:EURUSD",
        "interval": "15",
        "timezone": "Etc/UTC",
        "theme": "dark",
        "style": "1",
        "locale": "en",
        "toolbar_bg": "#1e222d",
        "enable_publishing": false,
        "hide_side_toolbar": false,
        "allow_symbol_change": true,
        "container_id": "tradingview_chart",
        "hide_top_toolbar": false,
        "hide_legend": false,
        "save_image": false,
        "backgroundColor": "#1e222d",
        "gridColor": "#2a2e39",
        "hide_volume": true
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
            instrument: document.getElementById('instrument').value,
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
                updateTrades();
            } else {
                alert(`Error: ${result.error}`);
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error placing order');
        }
    });

    async function updateTrades() {
        try {
            const response = await fetch('/api/forex/positions');
            const data = await response.json();
            
            const tbody = document.getElementById('tradesList');
            tbody.innerHTML = '';
            
            data.positions?.forEach(trade => {
                const pl = parseFloat(trade.currentPnl || 0);
                const plClass = pl >= 0 ? 'text-success' : 'text-danger';
                
                tbody.innerHTML += `
                    <tr>
                        <td>${trade.instrument}</td>
                        <td>${trade.side}</td>
                        <td>${trade.units}</td>
                        <td>${parseFloat(trade.openPrice).toFixed(5)}</td>
                        <td class="${plClass}">${pl.toFixed(2)}</td>
                        <td>
                            <button class="btn btn-danger btn-sm" onclick="closeTrade('${trade.id}')">Close</button>
                        </td>
                    </tr>
                `;
            });
        } catch (error) {
            console.error('Error updating trades:', error);
        }
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
            location.reload();
        } else {
            alert(`Error: ${result.error}`);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error closing trade');
    }
}

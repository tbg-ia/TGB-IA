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
        "hotlist": true,
        "calendar": true,
        "studies": [
            "RSI@tv-basicstudies",
            "MASimple@tv-basicstudies",
            "MACD@tv-basicstudies"
        ],
        "container_id": "tradingview_chart",
        "show_popup_button": true,
        "popup_width": "1000",
        "popup_height": "650",
        "hide_volume": false,
    });

    // Referencias a elementos del DOM
    const tradeForm = document.getElementById('tradeForm');
    const instrument = document.getElementById('instrument');

    // Manejar cambio de instrumento
    instrument.addEventListener('change', function() {
        let pair = this.value.replace('_', '');
        widget.chart().setSymbol(`FX:${pair}`, {
            interval: '15'
        });
    });

    // Manejar envío del formulario
    tradeForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const data = {
            symbol: document.getElementById('instrument').value,
            units: parseInt(document.getElementById('units').value),
            side: document.getElementById('side').value,
            take_profit: document.getElementById('take_profit').value || null,
            stop_loss: document.getElementById('stop_loss').value || null
        };

        fetch('/api/forex/order', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Orden ejecutada exitosamente');
                updateTrades();
            } else {
                alert(`Error: ${data.error}`);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al ejecutar la orden');
        });
    });

    // Función para actualizar la tabla de trades
    function updateTrades() {
        fetch('/api/forex/trades')
            .then(response => response.json())
            .then(data => {
                const tbody = document.querySelector('table tbody');
                tbody.innerHTML = '';
                data.trades.forEach(trade => {
                    const row = document.createElement('tr');
                    row.className = 'trade-row';
                    row.dataset.tradeId = trade.id;
                    row.innerHTML = `
                        <td>${trade.instrument}</td>
                        <td>${trade.side}</td>
                        <td>${trade.units}</td>
                        <td>${trade.price}</td>
                        <td class="pnl" id="pnl-${trade.id}">Calculating...</td>
                        <td>
                            ${trade.status === 'OPEN' ? 
                                `<button class="btn btn-danger btn-sm" onclick="closeTrade(${trade.id})">Close</button>` :
                                'Closed'}
                        </td>
                    `;
                    tbody.appendChild(row);
                });
            })
            .catch(error => console.error('Error:', error));
    }

    // Actualizar trades cada 5 segundos
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
            alert('Operación cerrada exitosamente');
            updateTrades();
        } else {
            alert(`Error: ${data.error}`);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error al cerrar la operación');
    });
}

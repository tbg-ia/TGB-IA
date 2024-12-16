// Terminal Forex Trading JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Referencias a elementos del DOM
    const tradingPair = document.getElementById('tradingPair');
    const tradeUnits = document.getElementById('tradeUnits');
    const takeProfit = document.getElementById('takeProfit');
    const stopLoss = document.getElementById('stopLoss');
    const buyButton = document.getElementById('buyButton');
    const sellButton = document.getElementById('sellButton');
    const balanceDisplay = document.getElementById('balanceDisplay');

    // Función para actualizar el balance
    function updateBalance() {
        fetch('/api/forex/balance')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    balanceDisplay.textContent = `${data.balance.toFixed(2)} ${data.currency}`;
                }
            })
            .catch(error => console.error('Error:', error));
    }

    // Función para actualizar posiciones activas
    function updateActiveTrades() {
        fetch('/api/forex/positions')
            .then(response => response.json())
            .then(data => {
                const tbody = document.getElementById('activeTrades');
                tbody.innerHTML = '';
                data.positions.forEach(position => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${position.instrument}</td>
                        <td>${position.side}</td>
                        <td>${position.units}</td>
                        <td class="${position.pl >= 0 ? 'text-success' : 'text-danger'}">
                            ${position.pl.toFixed(2)}
                        </td>
                        <td>
                            <button class="btn btn-sm btn-danger" 
                                    onclick="closePosition('${position.id}')">
                                Cerrar
                            </button>
                        </td>
                    `;
                    tbody.appendChild(row);
                });
            })
            .catch(error => console.error('Error:', error));
    }

    // Función para ejecutar una orden
    function placeOrder(side) {
        const data = {
            instrument: tradingPair.value,
            units: parseInt(tradeUnits.value),
            side: side,
            type: 'MARKET'
        };

        if (takeProfit.value) {
            data.takeProfit = parseFloat(takeProfit.value);
        }
        if (stopLoss.value) {
            data.stopLoss = parseFloat(stopLoss.value);
        }

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
                alert(`Orden ${side} ejecutada exitosamente`);
                updateBalance();
                updateActiveTrades();
            } else {
                alert(`Error: ${data.error}`);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al ejecutar la orden');
        });
    }

    // Event listeners
    if (buyButton) {
        buyButton.addEventListener('click', () => placeOrder('BUY'));
    }
    if (sellButton) {
        sellButton.addEventListener('click', () => placeOrder('SELL'));
    }

    // Actualizar datos cada 5 segundos
    setInterval(() => {
        updateBalance();
        updateActiveTrades();
    }, 5000);

    // Inicializar datos
    updateBalance();
    updateActiveTrades();
});

// Función para cerrar una posición
function closePosition(positionId) {
    if (confirm('¿Estás seguro de que deseas cerrar esta posición?')) {
        fetch(`/api/forex/position/${positionId}/close`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Posición cerrada exitosamente');
                updateBalance();
                updateActiveTrades();
            } else {
                alert(`Error: ${data.error}`);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al cerrar la posición');
        });
    }
}

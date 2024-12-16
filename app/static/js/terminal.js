// Terminal Trading JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Referencias a elementos del DOM
    const exchangeSelect = document.getElementById('exchangeSelect');
    const tradingPair = document.getElementById('tradingPair');
    const tradeAmount = document.getElementById('tradeAmount');
    const tradePrice = document.getElementById('tradePrice');
    const balanceDisplay = document.getElementById('balanceDisplay');

    // Función para actualizar el balance
    function updateBalance() {
        fetch('/api/trading/balance')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('balanceDisplay').textContent = 
                        `Balance: ${data.balance.toFixed(2)} ${data.currency}`;
                }
            })
            .catch(error => console.error('Error:', error));
    }

    // Función para ejecutar una orden
    function placeOrder(side) {
        const data = {
            exchange_id: exchangeSelect.value,
            symbol: symbolSelect.value,
            side: side,
            amount: parseFloat(amountInput.value),
            price: priceInput.value ? parseFloat(priceInput.value) : null,
            type: priceInput.value ? 'LIMIT' : 'MARKET'
        };

        fetch('/api/trading/place-order', {
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

    // Actualizar balance al cargar
    updateBalance();
    
    // Actualizar balance cada 30 segundos
    setInterval(updateBalance, 30000);
});

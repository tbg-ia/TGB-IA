// Trading related JavaScript functions

document.addEventListener('DOMContentLoaded', function() {
    const exchangeSelect = document.getElementById('exchangeSelect');
    const tradingPair = document.getElementById('tradingPair');
    const tradeAmount = document.getElementById('tradeAmount');
    const tradePrice = document.getElementById('tradePrice');
    
    // Mostrar/ocultar pares según el tipo de exchange
    exchangeSelect.addEventListener('change', function() {
        const selectedOption = this.options[this.selectedIndex];
        const exchangeType = selectedOption.getAttribute('data-type');
        
        const cryptoPairs = tradingPair.querySelector('.crypto-pairs');
        const forexPairs = tradingPair.querySelector('.forex-pairs');
        
        if (exchangeType === 'oanda') {
            cryptoPairs.style.display = 'none';
            forexPairs.style.display = '';
        } else {
            cryptoPairs.style.display = '';
            forexPairs.style.display = 'none';
        }
        
        // Actualizar balance disponible
        const balance = parseFloat(selectedOption.getAttribute('data-balance'));
        document.getElementById('availableBalance').textContent = balance.toFixed(2);
    });
});

function placeOrder(side) {
    const exchange = document.getElementById('exchangeSelect').value;
    const symbol = document.getElementById('tradingPair').value;
    const amount = document.getElementById('tradeAmount').value;
    const price = document.getElementById('tradePrice').value;
    
    if (!exchange || !symbol || !amount) {
        alert('Por favor complete todos los campos requeridos');
        return;
    }
    
    const orderData = {
        exchange_id: exchange,
        symbol: symbol,
        side: side,
        amount: parseFloat(amount),
        price: price ? parseFloat(price) : null,
        type: price ? 'LIMIT' : 'MARKET'
    };
    
    fetch('/api/trading/place-order', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(orderData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(`Orden de ${side} ejecutada exitosamente`);
            updateOrderBook();
            updateOpenOrders();
        } else {
            alert(`Error: ${data.error}`);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error al ejecutar la orden');
    });
}

function updateOrderBook() {
    const exchange = document.getElementById('exchangeSelect').value;
    const symbol = document.getElementById('tradingPair').value;
    
    if (!exchange || !symbol) return;
    
    fetch(`/api/trading/orderbook?exchange_id=${exchange}&symbol=${symbol}`)
        .then(response => response.json())
        .then(data => {
            const orderBookBody = document.getElementById('orderBook');
            orderBookBody.innerHTML = '';
            
            // Agregar asks (ventas)
            data.asks.slice(0, 5).forEach(ask => {
                const row = document.createElement('tr');
                row.className = 'text-danger';
                row.innerHTML = `
                    <td>${parseFloat(ask[0]).toFixed(2)}</td>
                    <td>${parseFloat(ask[1]).toFixed(4)}</td>
                    <td>${(ask[0] * ask[1]).toFixed(2)}</td>
                `;
                orderBookBody.appendChild(row);
            });
            
            // Agregar bids (compras)
            data.bids.slice(0, 5).forEach(bid => {
                const row = document.createElement('tr');
                row.className = 'text-success';
                row.innerHTML = `
                    <td>${parseFloat(bid[0]).toFixed(2)}</td>
                    <td>${parseFloat(bid[1]).toFixed(4)}</td>
                    <td>${(bid[0] * bid[1]).toFixed(2)}</td>
                `;
                orderBookBody.appendChild(row);
            });
        })
        .catch(error => console.error('Error:', error));
}

function updateOpenOrders() {
    const exchange = document.getElementById('exchangeSelect').value;
    
    if (!exchange) return;
    
    fetch(`/api/trading/open-orders?exchange_id=${exchange}`)
        .then(response => response.json())
        .then(data => {
            const openOrdersBody = document.getElementById('openOrders');
            openOrdersBody.innerHTML = '';
            
            data.orders.forEach(order => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${order.symbol}</td>
                    <td>${order.side}</td>
                    <td>${parseFloat(order.price).toFixed(2)}</td>
                    <td>${parseFloat(order.amount).toFixed(4)}</td>
                `;
                openOrdersBody.appendChild(row);
            });
        })
        .catch(error => console.error('Error:', error));
}

// Actualizar datos cada 5 segundos
setInterval(() => {
    updateOrderBook();
    updateOpenOrders();
}, 5000);

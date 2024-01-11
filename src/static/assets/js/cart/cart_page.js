const total_price_span = document.getElementById('total_price')

async function get_total_price(auth) {
    await fetch('http://127.0.0.1:8000/cart/api/cart/')
        .then((response) => {
            return response.json()
        })
        .then((data) => {
            let total_price = 0
            for (elem of data) {
                if (auth === 'True') {
                    total_price += elem.product_seller.price * elem.count
                } else {
                    total_price += elem.price * elem.cart_count
                }
            }
            total_price_span.innerHTML = parseFloat(total_price).toFixed(2) + '$'
        })
}

async function remove_product(pk, auth) {
    await fetch('http://127.0.0.1:8000/cart/api/cart/'+ pk +'/', {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': csrftoken,
        }
    })
        .then(() => {
            cart_amt()
        })
    document.getElementById('product_cart_'+ pk).style.display = 'none'
    get_total_price(auth)
}

async function changing_product_amt(pk, term, auth) {
    let value = Number(document.getElementById('input_'+pk).value) + term
    if (value === 0) {
        remove_product(pk, auth)
        return
    }
    await fetch('http://127.0.0.1:8000/cart/api/cart/'+ pk +'/', {
        method: 'PATCH',
        body: JSON.stringify({'count': value}),
        headers: {
            "Content-Type": "application/json",
            'X-CSRFToken': csrftoken,
        }
    })
        .then((response) => {
            return response.json()
        })
        .then((data) => {
            if (auth === 'True') {
                var product_price = data.count * data.product_seller.price
            } else {
                var product_price = data.count * data.price
            }
            document.getElementById('product_price_'+ pk).innerHTML = parseFloat(product_price).toFixed(2) + '$'
            get_total_price(auth)
        })
}

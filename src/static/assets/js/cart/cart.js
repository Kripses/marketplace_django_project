const cart_header = document.getElementById('cart_amt_header')

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
const csrftoken = getCookie('csrftoken');

async function cart_amt() {
    await fetch(`/cart/api/cart/`)
        .then((response) => {
            return response.json();
        })
        .then((data) => {
            cart_header.innerHTML = data.length;
        });
}

async function add_to_cart(product_pk, seller='') {
    await fetch(`/cart/api/product-seller/?product=${product_pk}&seller=${seller}`)
        .then((response) => {
            return response.json();
        })
        .then((data) => {
            fetch(`/cart/api/cart/`, {
                method: 'POST',
                body: JSON.stringify({
                    'product_seller': data[0].pk,
                    'count': 1,
                }),
                headers: {
                    "Content-Type": "application/json",
                    'X-CSRFToken': csrftoken,
                },
            })
                .then(() => {
                    cart_amt();
                });
        });
}

cart_amt();

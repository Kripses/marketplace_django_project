//Маска ввода номера телефона при оформлении заказа

mask_phone = new Inputmask("+7 (999) 999-99-99").mask(document.querySelector('.mask_phone'));

// Функция для заполнения последней страницы заказа
const total_price = parseFloat(document.getElementById('total-price').value)
const normal_delivery_price = parseFloat(document.getElementById('delivery_type_1').dataset['price']);
const express_delivery_price = parseFloat(document.getElementById('delivery_type_2').dataset['price']);

function makeDataOrderCreate() {
    let delivery_type = '';
    let payment_type = '';

    let user_name = document.getElementById('fio').value;
    let user_phone = document.getElementById('phone').value;
    let user_email = document.getElementById('email').value;

    let delivery_type_1 = document.getElementById('delivery_type_1');
    let delivery_type_2 = document.getElementById('delivery_type_2');
    if (delivery_type_1.checked) {
        delivery_type = delivery_type_1.value;
    } else {
        delivery_type = delivery_type_2.value;
    }

    let city = document.getElementById('city').value;
    let delivery_address = document.getElementById('address').value;

    let payment_type_1 = document.getElementById('type_1');
    let payment_type_2 = document.getElementById('type_2');
    if (payment_type_1.checked) {
        payment_type = payment_type_1.value;
    } else {
        payment_type = payment_type_2.value;
    }

    document.getElementById('user_fio').innerText = user_name;
    document.getElementById('user_phone').innerText = user_phone;
    document.getElementById('user_email').innerText = user_email;
    document.getElementById('user_delivery_type').innerText = delivery_type;
    document.getElementById('user_city').innerText = city;
    document.getElementById('user_delivery_address').innerText = delivery_address;
    document.getElementById('user_payment_type').innerText = payment_type;

    if (delivery_type === "Экспресс доставка") {
        document.getElementById('total-price').value =
            total_price + express_delivery_price;
        document.getElementById('Cart-price').innerText =
            "$" + document.getElementById('total-price').value;
        document.getElementById('Delivery-price').innerText = '$' + (normal_delivery_price + express_delivery_price)

    } else {
        document.getElementById('total-price').value = total_price
        document.getElementById('Cart-price').innerText = "$" + total_price;
        document.getElementById('Delivery-price').innerText = '$' + normal_delivery_price
    }
}

// Перемещение по страницам создания заказа

const create_order = document.querySelector('.Order');
const next = create_order.querySelectorAll('.Order-next'); // кнопка "Далее"
const menu_item = create_order.querySelectorAll('.menu-item'); // элементы меню в разделе создания заказа
const order_page = create_order.querySelectorAll('.Order-block'); // страницы в разделе создания заказа


menu_item.forEach(function(element) {
    element.addEventListener('click', function(elem) {
        const path = elem.currentTarget.querySelector('.menu-link').dataset.path;

        menu_item.forEach(function (btn) {btn.classList.remove('menu-item_ACTIVE')});
        elem.currentTarget.classList.add('menu-item_ACTIVE');

        order_page.forEach(function (page) {page.classList.remove('Order-block_OPEN')})
        create_order.querySelectorAll(`[data-target="${path}"]`).forEach(function(page) {
            page.classList.add('Order-block_OPEN');
        });

        element.classList.add('menu-item_ACTIVE');

        if (path === "four") makeDataOrderCreate();
    });
});


// Обработчик кнопок "Далее" на страницах создания заказа

const order_next = create_order.querySelectorAll('.Order-next');


order_next.forEach(function (btn_next) {
    btn_next.addEventListener('click', function(elem) {
        const path = elem.currentTarget.dataset.path;

        menu_item.forEach(function (btn) {btn.classList.remove('menu-item_ACTIVE')});
        create_order.querySelector('.Section-column').querySelector(`[data-path="${path}"]`)
            .parentNode.classList.add('menu-item_ACTIVE')

        order_page.forEach(function (page) {page.classList.remove('Order-block_OPEN')})
        create_order.querySelector(`[data-target="${path}"]`).classList.add('Order-block_OPEN');

        if (path === "four") makeDataOrderCreate();
    });
});


// form validate

let validator = new window.JustValidate('#form-validate');

validator
    .addField('#fio', [
        {
            rule: 'required',
            errorMessage: 'Введите имя',
        },
        {
            rule: 'minLength',
            value: 2,
            errorMessage: 'Минимум 2 символа',
        }
    ])
    .addField('#phone', [
        {
            rule: 'required',
            errorMessage: 'Введите номер телефона!'
        },
        {
            validator: (value) => {
                const phone = mask_phone.unmaskedvalue();
                return Boolean(Number(phone) && phone.length === 10)
            },
            errorMessage: 'Телефон введен не верно!'
        },
    ])
    .addField('#email', [
        {
            rule: 'required',
            errorMessage: 'Введите почту!'
        },
        {
            rule: 'email',
            errorMessage: 'Почта введена неверно!'
        }
    ])
    .addField('#city', [
        {
            rule: 'required',
            errorMessage: 'Введите город!'
        }
    ])
    .addField('#address', [
        {
            rule: 'required',
            errorMessage: 'Введите адрес!'
        }
    ])
    .onSuccess((event) => {
        event.currentTarget.submit();
    })
    .onFail(() => {
        alert('Заполнены не все поля заказа')
    })


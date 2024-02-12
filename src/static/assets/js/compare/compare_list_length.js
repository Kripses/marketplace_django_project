const compare_amt = document.getElementById('compare_amt')

function compare_length() {
    fetch(`/catalog/compare/amt/`).
    then((response) => {
        return response.json()
    }).then((data) => {
        if (data === 0) {
            compare_main.style = "color: red"
            compare_main.innerHTML = 'недостаточно товаров для сравнения'
            compare_amt.style.display = 'none'
    } else if (data === 1) {
            compare_amt.style.display = 'flex'
            compare_amt.innerHTML = data
            compare_main_label.style = "color: red"
            compare_main_label.innerHTML = 'недостаточно товаров для сравнения'
        } else {
        compare_amt.style.display = 'flex'
        compare_amt.innerHTML = data
    }
    return data
    })
}

compare_length()
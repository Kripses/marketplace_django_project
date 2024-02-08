const type_properties = document.getElementById('type_properties')
const compare_main = document.getElementById('compare-main')
const compare_main_label = document.getElementById('compare-main-error')
const compare_dif_category = document.getElementById('compare_dif_category')

async function delete_all() {
    await fetch('delete_all/', {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': csrftoken,
        }
    })
    document.getElementById('all_products').style.display = 'none'
    // compare_main.style = "color: red"
    // compare_main.innerHTML = 'Недостаточно товаров для сравнения'
    compare_length()
}

async function delete_product(slug) {
    document.getElementById(slug).style.display = 'none'
    await fetch('delete/' + slug + '/', {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': csrftoken,
        }
    })
    compare_length()
}

function change_properties() {
    console.log(type_properties.checked)
    if (type_properties.checked) {
        $('.table-diff').css('display', 'flex')
        $('.table-no-diff').css('display', 'none')
    } else {
        console.log(2)
        $('.table-diff').css('display', 'none')
        $('.table-no-diff').css('display', 'flex')
    }
}

setTimeout(function(){
    compare_dif_category.style.display = 'none'
}, 5000)
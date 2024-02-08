function add_to_compare(slug) {
    fetch('http://127.0.0.1:8000/catalog/compare/add/' + slug + '/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
        }
    })
    .then((res) => {
        compare_length()
    })
}
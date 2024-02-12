function add_to_compare(slug) {
    fetch(`/catalog/compare/add/` + slug + '/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
        }
    })
    .then((res) => {
        compare_length()
    })
}
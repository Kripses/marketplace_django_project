function add_to_compare(slug) {
    const currentLanguage = localStorage.getItem('preferredLanguage') || 'en';
    const url = `/${currentLanguage}/catalog/compare/add/${slug}/`;

    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
        }
    })
    .then((res) => {
        compare_length();
    });
}
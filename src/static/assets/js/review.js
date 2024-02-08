let visible = 3

const btnMore = document.getElementById("btn-more");
const commentItems = document.querySelectorAll('.Comment');
const btnMoreBox = document.querySelector('.Comment-more')

btnMore.addEventListener('click', function() {
    for (let i = visible; i < Math.min(visible + 3, commentItems.length); i++) {
        commentItems.item(i).classList.add('visible')
    }
    visible += 3
    if (visible >= commentItems.length) {
        btnMoreBox.classList.add('non-visible');
    }
})

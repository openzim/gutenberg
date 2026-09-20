(function() {
    var scrollBtn = document.getElementById('scroll-to-top');
    if (!scrollBtn) return;
    
    function toggleScrollButton() {
        scrollBtn.classList.toggle('hidden', window.pageYOffset <= 300);
    }
    
    function scrollToTop(e) {
        e.preventDefault();
        window.scrollTo({top: 0, behavior: 'smooth'});
    }
    
    scrollBtn.addEventListener('click', scrollToTop);
    window.addEventListener('scroll', toggleScrollButton);
    toggleScrollButton();
})();

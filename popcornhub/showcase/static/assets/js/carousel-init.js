$(document).ready(function() {
    // Инициализация карусели
    const featuredCarousel = $("#featuredCarousel").owlCarousel({
        items: 1,
        loop: true,
        nav: true,
        dots: true,
        autoplay: true,
        autoplayTimeout: 5000,
        smartSpeed: 1000,
        navText: [
            '<i class="fa fa-angle-left"></i>',
            '<i class="fa fa-angle-right"></i>'
        ],
        responsive: {
            0: {
                items: 1
            },
            768: {
                items: 1
            },
            992: {
                items: 1
            }
        }
    });

    // Функция обновления баннера
    function updateBanner() {
        // Получаем активный слайд
        const activeSlide = document.querySelector('.owl-item.active');
        if (!activeSlide) return;
        
        const movieElement = activeSlide.querySelector('.item');
        if (!movieElement) return;
        
        // Получаем данные фильма
        const title = movieElement.querySelector('.content h4')?.textContent;
        const description = movieElement.querySelector('.content ul')?.innerHTML;
        const rating = movieElement.querySelector('.content .rating')?.innerHTML;

        // Обновляем информацию в баннере
        const headerText = document.querySelector('.main-banner .header-text h2');
        const movieInfo = document.querySelector('.main-banner .movie-info');
        const ratingDisplay = document.querySelector('.main-banner .rating-display');

        if (headerText && title) headerText.textContent = title;
        if (movieInfo && description) movieInfo.innerHTML = description;
        if (ratingDisplay && rating) ratingDisplay.innerHTML = rating;
    }

    // Обновляем баннер при изменении слайда
    featuredCarousel.on('translated.owl.carousel', updateBanner);
    
    // Обновляем баннер при инициализации
    featuredCarousel.on('initialized.owl.carousel', updateBanner);
}); 
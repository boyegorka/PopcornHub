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
    function updateBanner(movieElement) {
        if (!movieElement) return;
        
        // Получаем данные фильма
        const posterImg = movieElement.querySelector('.thumb img');
        const title = movieElement.querySelector('.content h4')?.textContent;
        const description = movieElement.querySelector('.content ul')?.innerHTML;
        const rating = movieElement.querySelector('.content .rating')?.innerHTML;

        // Обновляем баннер
        const mainBanner = document.querySelector('.main-banner');
        if (posterImg && posterImg.src) {
            mainBanner.style.backgroundImage = `url('${posterImg.src}')`;
            mainBanner.style.backgroundSize = 'cover';
            mainBanner.style.backgroundPosition = 'center';
            mainBanner.style.height = '600px';
        }

        // Обновляем информацию
        const headerText = document.querySelector('.main-banner .header-text h2');
        const movieInfo = document.querySelector('.main-banner .movie-info');
        const ratingDisplay = document.querySelector('.main-banner .rating-display');

        if (headerText && title) headerText.textContent = title;
        if (movieInfo && description) movieInfo.innerHTML = description;
        if (ratingDisplay && rating) ratingDisplay.innerHTML = rating;
    }

    // Обработчик изменения слайда
    featuredCarousel.on('changed.owl.carousel', function(event) {
        setTimeout(() => {
            const activeSlide = document.querySelector('#featuredCarousel .owl-item.active .item');
            if (activeSlide) {
                updateBanner(activeSlide);
            }
        }, 100);
    });

    // Обновляем баннер при загрузке страницы
    const initialSlide = document.querySelector('#featuredCarousel .owl-item.active .item');
    if (initialSlide) {
        updateBanner(initialSlide);
    }
}); 
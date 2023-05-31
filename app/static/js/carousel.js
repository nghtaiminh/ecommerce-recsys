
$(document).ready(function () {
    $('.popular-carousel .owl-carousel').owlCarousel(
        {
            loop: true,
            margin: 15,
            autoHeight: true,
            nav: true,
            navText: ['<i class="fa fa-angle-left" aria-hidden="true"></i>', '<i class="fa fa-angle-right" aria-hidden="true"></i>'],
            navContainer: '.popular-carousel .owl-nav',
            dots: false,
            responsive:
            {
                0: { items: 2 },
                575: { items: 3 },
                768: { items: 4 },
                991: { items: 5 },
                1199: { items: 6 }
            }
        }
    );

    $('.recommendation-carousel .owl-carousel').owlCarousel(
        {
            loop: false,
            margin: 15,
            autoHeight: true,
            nav: true,
            dots: false,
            navText: ['<i class="fa fa-angle-left" aria-hidden="true"></i>', '<i class="fa fa-angle-right" aria-hidden="true"></i>'],
            navContainer: '.recommendation-carousel .owl-nav',
            responsive:
            {
                0: { items: 2 },
                575: { items: 3 },
                768: { items: 4 },
                991: { items: 5 },
                1199: { items: 6 }
            }
        }
    );

    $('.recently-viewed-carousel .owl-carousel').owlCarousel(
        {
            loop: false,
            autoplay: false,
            autoplayTimeout: 5000,
            autoHeight: true,
            dots: false,
            nav: true,
            navText: ['<i class="fa fa-angle-left" aria-hidden="true"></i>', '<i class="fa fa-angle-right" aria-hidden="true"></i>'],
            navContainer: '.recently-viewed-carousel .owl-nav',
            responsive:
            {
                0: { items: 2 },
                575: { items: 3 },
                768: { items: 4 },
                991: { items: 5 },
                1199: { items: 6 }
            }
        }
    );
});

$(document).ready(function () {
    $(document).on('click', '.btn-search', function (e) {
        e.preventDefault();
        window.location.href = "/search/" + encodeURIComponent($('input[name="search-key"]').val());
    })

    // Add basket api
    $(document).on("click", ".add-basket", function (e) {
        e.preventDefault();
        var id = $(e.target).data('id')

        $.ajax({
            type: "PUT",
            url: '/basket/add/' + id,
            contentType: "application/json",
            dataType: 'json',
            success: function (response) {
                if (!response.status) {
                    return;
                }
                if (window.location.href.includes('/basket')) {
                    location.reload();
                }
                
                $("#basket_count").html(response.basket_count);
            },
            error: function (e, t) {
                console.log(e, t);
            },
        });
    });

    // remove item basket
    $(document).on("click", ".remove-basket", function (e) {
        e.preventDefault();
        var id = $(e.target).data('id')

        $.ajax({
            type: "DELETE",
            url: '/basket/remove/' + id,
            contentType: "application/json",
            dataType: 'json',
            success: function (response) {
                if (response.status) {
                    location.reload();
                }
                return;
            },
            error: function (e, t) {
                console.log(e, t);
            },
        });
    });

    // Total price
    $(document).on('change', ".item-basket-quantity", function (e) {
        if ($(e.target).val() < 1) {
            $(e.target).val(1);
        }
        price = $(e.target).data('price') * $(e.target).val();
        $(e.target.parentElement.parentElement).find('.item-basket-price').html(price.toFixed(2));

        total = 0
        $(".item-basket-price").each(function (index, item) {
            total += parseFloat(item.innerHTML)
        });
        $("#total-price").html("$ " + total.toFixed(2))

        $.ajax({
            type: "PUT",
            url: '/basket/update/' + $(e.target).data('id'),
            data: JSON.stringify({ "quantity": $(e.target).val() }),
            contentType: "application/json",
            dataType: 'json',
            success: function (response) {
                return;
            },
            error: function (e, t) {
                console.log(e, t);
            },
        });
    });

});



document.addEventListener("DOMContentLoaded", function() {
    const formOpenBtn = document.querySelector("#form_open"),
          home = document.querySelector(".home"),
          formContainer = document.querySelector(".form_container"),
          formCloseBtn = document.querySelector(".form_close"),
          signupBtn = document.querySelector("#SignUp"),
          loginBtn = document.querySelector("#SignIn");

    formOpenBtn.addEventListener("click", () => {
        home.classList.add("show");
    });

    formCloseBtn.addEventListener("click", () => {
        home.classList.remove("show");
        formContainer.classList.remove("active");
    });

    signupBtn.addEventListener("click", (e) => {
        e.preventDefault();
        formContainer.classList.add("active");
    });

    loginBtn.addEventListener("click", (e) => {
        e.preventDefault();
        formContainer.classList.remove("active");
    });
});






$(document).ready(function () {
    $('#search').keyup(function () {
      var search_term = $(this).val();
      if (search_term.length >= 1) {
        $.ajax({
          type: 'POST',
          url: '',
          data: {
            'search_term': search_term,
            csrfmiddlewaretoken: '{{ csrf_token }}'
          },
          success: function (response) {
            var suggestionsHtml = '';
            response.forEach(function (product) {
              // Modify the suggestionsHtml to include both title and ID
              suggestionsHtml += '<div class="suggestion border-bottom border-1 cursor-pointer suggestion-hover" data-id="' + product.id + '">' + product.title + '</div>';
            });
            $('#search-suggestions').html(suggestionsHtml).show();
          }
        });
      } else {
        $('#search-suggestions').hide();
      }
    });

    // Handle click on suggestion
    $(document).on('click', '.suggestion', function () {
      // Get the ID of the clicked suggestion
      var productId = $(this).data('id');
      // Construct the URL using Django template syntax
      var productUrl = ''.replace('0', productId);
      // Redirect the user to the product details page
      window.location.href = productUrl;
    });

    // Hide suggestions when clicking outside
    $(document).click(function (event) {
      if (!$(event.target).closest('#search-suggestions').length && !$(event.target).is('#search')) {
        $('#search-suggestions').hide();
      }
    });
  });




  document.addEventListener('DOMContentLoaded', function () {
    const searchIcon = document.getElementById('search-icon');
    const searchForm = document.getElementById('search-form');
    
    searchIcon.addEventListener('click', function () {
      if (searchForm.style.display === 'block') {
        searchForm.style.display = 'none';
      } else {
        searchForm.style.display = 'block';
      }
    });

    searchForm.addEventListener('submit', function (event) {
      event.preventDefault(); // Prevent actual form submission for demonstration
      // Add your form submission logic here, e.g., AJAX request
      searchForm.style.display = 'none';
    });
  });
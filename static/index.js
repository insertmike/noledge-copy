
const spinner = document.getElementById("spinner");

$("#contact-us").submit(function(e) {

    e.preventDefault();
    spinner.removeAttribute('hidden');
    var form = $(this);
    var url = form.attr('action');
    $.ajax({
        type: "POST",
        url: ENDPOINT + '/submitForm',
        data: form.serialize(),
        success: function(data)
        {
            spinner.setAttribute('hidden', '');
            alert('Message Sent');
        },
        error: function(data)
        {

          alert('Failed to send :(')
          spinner.setAttribute('hidden', '');
        }
        });

});

function login() {
  console.log('login')
  window.localStorage.setItem("currTest", undefined);
}

function register() {
  window.localStorage.setItem("currTest", undefined);
}


$('.toggle-register').click(function(){
    $(this).addClass('active');
    $('.toggle-login').removeClass('active');
    $('.login-body').slideUp("slow");
    $('.register-body').delay(625).slideDown("slow");
  });

  $('.toggle-login').click(function(){
    $(this).addClass('active');
    $('.toggle-register').removeClass('active');
    $('.register-body').slideUp("slow");
    $('.login-body').delay(625).slideDown("slow");
  });

  $('#registered').click(function(){
    $('.toggle-login').click();
  });

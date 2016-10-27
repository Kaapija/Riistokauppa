$(document).ready(function() {

  $("#extra_search_options").hide();

  $("#search_form").on("submit", function(event) {
    event.preventDefault();
    postSearch();
  });

  function postSearch() {
    var csrftoken = $('input[name="csrfmiddlewaretoken"]').attr("value");
    var categories = $.map( $("input[name='categories']:checked"), function (a, i) {
      return a.value;
    });

    $.ajax({
      url: "search",
      type: "POST",
      traditional: true,
      data: {"gameName": $("#id_gameName").val(),
             "developerName": $("#id_developerName").val(),
             "minPrice": $("#id_minPrice").val(),
             "maxPrice": $("#id_maxPrice").val(),
             "categories": categories,
             csrfmiddlewaretoken: csrftoken },
      success: function(data) {
        $("#search_results").html(data.html);
      }

    });
  }

  $('input[name="toggle_search_options"]').click(function(event) {
    event.preventDefault();
    if ($("#extra_search_options").is(":visible")) {
      $("#extra_search_options").hide();
      this.value = "Lisää hakuehtoja";
    }
    else {
      $("#extra_search_options").show();
      this.value = "Vähemmän hakuehtoja";
    }
  });
});

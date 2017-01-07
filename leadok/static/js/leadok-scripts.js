$(document).ready(function() {

$('#leadok-giga-notify-button').click(function() {
    $('#leadok-giga-notify-status-text').text('Уведомление отправляется...');
    $('#leadok-giga-notify-status-text').css('color', 'blue');
    $('#leadok-giga-notify-button').hide();
    $('#leadok-giga-notify-textarea').attr("disabled", true);

    var lead_id = parseInt($('#leadok-lead-id').text(), 10);
    var note = $('#leadok-giga-notify-textarea').val();

    var var_data = {lead_id : lead_id, notification: note};
    $.ajax({
        method:"POST",
        url: "/ajax/notify_giga_about_brack_via_email",
        data: var_data,
        data: JSON.stringify(var_data),
       contentType: 'application/json; charset=utf-8',
         success: function(data) {
            var result = data['result']
            if (result) {
                $('#leadok-giga-notify-status-text').text('Уведомление отправлено.');
                $('#leadok-giga-notify-status-text').css('color', 'green');
            } else {
                $('#leadok-giga-notify-status-text').text('Уведомление не отправлено.');
                $('#leadok-giga-notify-status-text').css('color', 'red');
                $('#leadok-giga-notify-button').show();
                 $('#leadok-giga-notify-textarea').attr("disabled", false);
            }
            },
        error: function(jqXHR, textStatus, errorThrown) {
                $('#leadok-giga-notify-status-text').text('Уведомление не отправлено.');
                $('#leadok-giga-notify-status-text').css('color', 'red');
                $('#leadok-giga-notify-button').show();
                 $('#leadok-giga-notify-textarea').attr("disabled", false);
            },
       dataType: "json"
      });


});


});
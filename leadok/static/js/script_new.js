// $(window).load(function(){
$(document).ready(function() {

	$( "#lead-alert" ).hide();

	// function ajax_magic(sound) {
	// 	if(typeof(sound)==='undefined') sound = true;
	// 	$.getJSON( "http://leadok.ru/ajax/newleadscount", function(data){
	// 		n_new = parseInt(data.result);
	// 		n_old = parseInt($( "#hidden-counter" ).text());
	// 		// alert(String(n_old) + "    " + String(n_new));
	// 		if (n_new > n_old && n_new > 0) {
	// 			$( "#lead-alert" ).text(n_new);
	// 			$( "#hidden-counter" ).text(n_new);
	// 			$( "#lead-alert" ).show();
	// 			if (sound) {
	// 				$('embed').remove();
	//      		$('body').append('<embed src="http://leadok.ru/static/alert2.mp3" autostart="true" hidden="true" loop="false">');
	// 			}

	// 		}

	// 	});
	// }

	// ajax_magic(false);
	// setInterval(ajax_magic, 5*60000);



    function colHeight(){
		var cheight = $("#wrapper").height();
		$(".col").each(function(){
			$(this).height(cheight);
		});
	}
	colHeight();
	$(window).resize(function(){
		colHeight();
		pmargin();
	});

/*
	var od = 1;
	$(".order-row").each(function(){
        if(od % 2 == 0) $(this).addClass("odd");
		od++;
    });
*/

	$( "#submit-payment-button" ).click(function() {
		$( "#submit-payment-form" ).submit();
	});

	$( "#choose-period-submit-button" ).click(function() {
		$( "#choose-period-form" ).submit();
	});

	$(".input-date" ).datepicker();

    $(".paycalendar" ).datepicker();



	$(".f-today").on("click", function(){
		$(".date-from").val(buildDateTuday());
		$(".date-to").val(buildDateTuday());
	});
	$(".f-yesterday").on("click", function(){
		$(".date-from").val(buildDateYesterday());
		$(".date-to").val(buildDateYesterday());
	});
	$(".f-7days").on("click", function(){
		$(".date-from").val(buildDate7days());
		$(".date-to").val(buildDateTuday());
	});
	$(".f-30days").on("click", function(){
		$(".date-from").val(buildDate30days());
		$(".date-to").val(buildDateTuday());
	});

	function dataFormat(date){
		var d = date.getDate();
		var m = date.getMonth() + 1;
		var y = date.getFullYear();
		if(d < 10) d = "0" + d;
		if(m < 10) m = "0" + m;
		var result = d + "." + m + "." + y;
		return result;
	}

	function buildDateTuday(){
		var date = new Date();
		var tuday = dataFormat(date);
		return tuday;
	}

	function buildDateYesterday(){
		var date = new Date();
		day = date.getDate();
		date.setDate(day - 1);
		var yesterday = dataFormat(date);
		return yesterday;
	}

	function buildDate7days(){
		var date = new Date();
		day = date.getDate();
		date.setDate(day - 7);
		var yesterday = dataFormat(date);
		return yesterday;
	}

	function buildDate30days(){
		var date = new Date();
		day = date.getDate();
		date.setDate(day - 30);
		var yesterday = dataFormat(date);
		return yesterday;
	}

	function pmargin(){
		var wheight = $(window).height();
		var pheight = $("#popup-container").height();
		if(wheight > pheight){
			var pmargin = (wheight - pheight)/2;
			$("#popup-container").css("margin-top", pmargin + "px");
		}
	}
	pmargin();

	$(".lead-brak").on("click", function(){
		$("#popup-wrapper").fadeIn(500);
		return false;
	});
	$(".popup-close").on("click", function(){
		$("#popup-wrapper").fadeOut(500);
	});

	$(".search-number").on("input", function(){
		var val = $(this).val();
		var newval = val.replace(/[^\d-()\+]+/g, "");
		$(this).val(newval);
	});

});
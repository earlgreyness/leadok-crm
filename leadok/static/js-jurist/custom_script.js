$(window).load(function(){
	$(".to-form").on("click", function(){
		var pos = $("#order").offset().top;
		$("body,html").animate({
			scrollTop: pos
		}, 1000);
	});


	$(".button").hover(function(){
		$(this).css("background-color","#fb715e");
	}, function(){
		$(this).css("background-color","#FF5E47");
	});
	$(".button-top").hover(function(){
		$(this).css("background-color","#fb715e");
	}, function(){
		$(this).css("background-color","#FF5E47");
	});

	$(".button").on("mousedown", function(){
		$(this).css("background-color","#cc4633");
	});
	$(".button-top").on("mousedown", function(){
		$(this).css("background-color","#cc4633");
	});

	$(".button").on("mouseleave", function(){
		$(this).css("background-color","#FF5E47");
	});
	$(".button-top").on("mouseleave", function(){
		$(this).css("background-color","#FF5E47");
	});
});
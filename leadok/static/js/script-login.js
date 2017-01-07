$(window).load(function(){
	$(".inputbox-submit").on("mousedown", function(){
		$(this).css("background-position","center bottom");
	});
	$(".inputbox-submit").on("mouseleave", function(){
		$(this).css("background-position","center top");
	});
});
$(document).ready(function(){
//popup открытие нового окна
    $(".btn-popup, .btn-1, .btn-2, .btn-4").click(function(){
        $(".popup-order, #hover").fadeIn();
        return false;
    });

    $(".btn_konf").click(function(){

		$("#modal-confidence").addClass('modal');
		// $("#modal-confidence").attr('style', 'display:block;');
		$("body").attr('style', 'padding-right: 17px;');
		$("body").addClass('modal-open');


        $("#modal-confidence, #hover2").fadeIn();
        return false;
    });



    $("#hover, #hover2, .close, .close-sps").click(function(){

		$("body").attr('style', 'padding-right: 0px;');
		$("body").removeClass('modal-open');
		$("#modal-confidence").removeClass('modal');
		// $("#modal-confidence").attr('style', 'display:none;');

        $(".popup-order, #hover, #hover2, .popup-spasibo, #modal-confidence").fadeOut();
        return false;
    });




    $(".phone_inp, .phone-pop").mask("+7 (999) 999-9999");

    $(".name_inp, .name-pop").DimPlaceHolder("Введите Ваше имя");
    $(".phone_inp, .phone-pop").DimPlaceHolder("Введите Ваш телефон");
    $(".email_inp, .email-pop").DimPlaceHolder("Введите Ваш e-mail");


    $(".btn-3").DimEmptyInputSend(".name_inp_3", ".phone_inp_3", ".email_inp_3", "Введите Ваше имя", "Введите Ваш телефон", "Введите Ваш e-mail");
    $(".btn-5").DimEmptyInputSend(".name_inp_5", ".phone_inp_5", ".email_inp_5", "Введите Ваше имя", "Введите Ваш телефон", "Введите Ваш e-mail");
    $(".btn-pop").DimEmptyInputSend(".name-pop", ".phone-pop", ".email-pop", "Введите Ваше имя", "Введите Ваш телефон", "Введите Ваш e-mail");





	$('#slider').flexslider({
		animation: "slide",
		animationLoop: false,
		slideshow: false,
		prevText: "",
		nextText: ""
	});




//Открывающийся список начало
     $(".section6 .block .desc").hide();



     $('.section6 .block').hover(function(){
		 $(this).children('.name').addClass('name_hover');
     },
     function(){
          $(this).children('.name').removeClass('name_hover');
     });



     $(".section6 .block .name,  .section6 .block .btn").click(function(){

		 $(this).parent().children('.desc').slideToggle(500);

		 if ($(this).parent().children('.btn').children('span').hasClass('open')){
			 $(this).parent().children('.btn').children('span').removeClass('open');
			 $(this).parent().children('.name').removeClass('name_open');
		 } else{
		 	 $(this).parent().children('.btn').children('span').addClass('open');
			 $(this).parent().children('.name').addClass('name_open');
		 }

     });
//Открывающийся список конец




});


$.urlParam = function(name){
    var results = new RegExp('[\?&]' + name + '=([^&#]*)').exec(window.location.href);
    if (results==null){
       return null;
    }
    else{
       return results[1] || 0;
    }
}


$.fn.DimEmptyInputSend = function(name, phone, mail, nameIF, phoneIF, mailIF) {
    $(this).click(function() {
            from = $.urlParam('from');
            if (from==null) {
                params = "";
            }
            else {
                params = "?from=" + from;
            }
            if ($(name).val() == "" || $(name).val() == nameIF)
                { $(name).attr('style', "color: #f00;");  }
            if ($(phone).val() == "" || $(phone).val() == phoneIF)
                { $(phone).attr('style', "color: #f00;");  }
		/*	if ($(mail).val() != ""  && $(mail).val() != mailIF && $(mail).val().indexOf("@") <= 0)
                { $(mail).attr('style', "color: #f00;");  var mailUS = false;}  */
            if (($(name).val() != "" && $(name).val() != nameIF) && ($(phone).val() != "" && $(phone).val() != phoneIF)/* && (mailUS != false) */)
                {   var nameVal = $(name).val(); var phoneVal = $(phone).val(); var mailVal = $(mail).val(); if ($(mail).val() == mailIF) {mailVal = ''}
                    // $.post("send-message.php" + params,
                    //     {
                    //         name: nameVal,
                    //         phone: phoneVal,
                    //         mail: mailVal
                    //     },
                    //     function(data){
                    //         $(name).DimPlaceHolder(nameIF);
                    //         $(phone).DimPlaceHolder(phoneIF);
                    //         $(mail).DimPlaceHolder(mailIF);
                    //         $(".popup-order").fadeOut();
                    //         $(".popup-spasibo, #hover").fadeIn();
                    //     });

                    yaCounter31828131.reachGoal('FORM_SUBMIT');


                }
         return false;
    });
};




$.fn.DimPlaceHolder=function(x) {
    this.val(x);
    this.attr('style', "color: #949494;");
        $(this).focus(function(){
            if ($(this).val() == x) { $(this).val("");  }
            $(this).attr('style', "color: #363636;");
        });
        $(this).blur(function(){  if ( $(this).val() == "" || !/\S/.test($(this).val()) )
            { $(this).val(x).attr('style', "color: #949494;");}  });
};



$(document).ready(function(){
        
    var images = ["img/slides/1.jpg","img/slides/2.jpg","img/slides/3.jpg","img/slides/4.jpg",
                  "img/slides/5.jpg","img/slides/6.jpg","img/slides/7.jpg","img/slides/8.jpg"];
        
    $(images).preloadImage();   
    
    
    var currentImage = 0;
    
    $(".slider-img").attr('style', "background-image: url("+images[currentImage]+");");
    $(".back-slider").click(function(){
        if(currentImage != 0){ 
            currentImage--; 
            $(".slider-img").fadeToggle(300);
            $(".slider-img").fadeToggle(300);
            setTimeout(function() {$(".slider-img").attr('style', "background-image: url("+images[currentImage]+");")}, 300);
        }
        return false;
    });
    $(".forward-slider").click(function(){
        if(currentImage != (images.length - 1)){ 
            currentImage++; 
            $(".slider-img").fadeToggle(300);
            $(".slider-img").fadeToggle(300);
            //setTimeout(function() {$(".slider-img").attr("src", images[currentImage])}, 300);
            setTimeout(function() {$(".slider-img").attr('style', "background-image: url("+images[currentImage]+");")}, 300);
        }
        return false;
    });

});



$.fn.preloadImage = function() {
    this.each(function(){
        $('<img/>')[0].src = this;
    });
};

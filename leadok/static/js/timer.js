function get_timer_403(string_403) {	
    var date_new_403 = string_403; 
    var date_t_403 = new Date(date_new_403);	
    var date_403 = new Date();	
    var timer_403 = date_t_403 - date_403;		
    if(date_t_403 > date_403) {		
        var day_403 = parseInt(timer_403/(60*60*1000*24));		
        if(day_403 < 10) { day_403 = "0" + day_403;	}		
        day_403 = day_403.toString();		
        var hour_403 = parseInt(timer_403/(60*60*1000))%24;		
        if(hour_403 < 10) {	hour_403 = "0" + hour_403; }		
        hour_403 = hour_403.toString();		
        var min_403 = parseInt(timer_403/(1000*60))%60;		
        if(min_403 < 10) { min_403 = "0" + min_403;	}		
        min_403 = min_403.toString();		
        var sec_403 = parseInt(timer_403/1000)%60;		
        if(sec_403 < 10) { sec_403 = "0" + sec_403;	}		
        sec_403 = sec_403.toString(); 		
        timethis_403 = day_403 + " : " + hour_403 + " : " + min_403 + " : " + sec_403;		
        $(".dTimer p.result .result-day").text(day_403);		
        $(".dTimer p.result .result-hour").text(hour_403);		
        $(".dTimer p.result .result-minute").text(min_403);		
        $(".dTimer p.result .result-second").text(sec_403);	}	
        else {		
              $(".dTimer p.result .result-day").text("00");		
              $(".dTimer p.result .result-hour").text("00");		
              $(".dTimer p.result .result-minute").text("00");		
              $(".dTimer p.result .result-second").text("00");	
        }}

function getfrominputs_403(){	
      day = new Date().getDate()+1;
      month = new Date().getMonth()+1;
      year = new Date().getFullYear();
      string_403 = month+"/"+day+"/"+year+" 00:00";        
    get_timer_403(string_403);	
    setInterval(function(){		get_timer_403(string_403);	},1000);}

$(document).ready(function(){ getfrominputs_403(); });		

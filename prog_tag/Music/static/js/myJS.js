


/*
 * Triggers the jump of the page to the lables section, on Enter click
 */
$("#song-input").keypress(function (event) {
      if (event.keyCode == 13) {
      	var song = $("#song-input").val();
      	if (song.length != 0){
      		song = song.split(" - ");
      		var title = song[0], artist = song[1];
	      	//call server to get labeles 
	      	$.ajax({
				type:"GET",
				url:"get_labels",
				data: {
					'title': title,
					'artist':artist
				},
				success:function(response){
					response = JSON.parse(response);
					$("#show_generes_results").empty();
					var html_lables_string = '<h2 style="font-weight:bold;">'+response.title+' by '+response.artist+'</h2>'+
												'<hr style="border-top:1px solid #838282;">';
					$.map(response.labels, function(label){
						html_lables_string+='  <span class="label label-default" style="background-color:#313888">'+label+'</span>';
					});
					$("#show_generes_results").append(html_lables_string);
					$('html,body').animate({
                        scrollTop:  $('#show_geners').offset().top - 150
                    }, 1000);
				}
			});        
        	event.preventDefault();
        	}
      }
    });
    
     
   /*
    * Trigger the modal of additional exploration options
    */           	 
    

$("#graph").click(function(){
	
	$('#myModal').modal('show');
});










function minimizeUI() {
    $( "#top-menu" ).slideUp( 300 );
    $( "#home-about" ).slideUp( 300 );
    $( "#logo2" ).show( 500, function() {
	$( "#logo2" ).show();
    });
}

function showBooks() {
    var url = "static/full_by_popularity.js";
    
    if ( $( "#language_filter" ).val() ) {
	url = "static/lang_" + $( "#language_filter" ).val() + "_by_popularity.js";
    }
    
    if ( $( "#author_filter" ).val() ) {
	var count = authors_json_data.length;
	var author_filter_value = $( "#author_filter" ).val();
	for ( i = 0 ; i < count ; i++ ) {
	    if (authors_json_data[i][0] === author_filter_value) {
		url = "static/auth_" + authors_json_data[i][1] + "_by_popularity.js";
		break;
	    };
	};
    }

    $.getScript( url, function( data, textStatus, jqxhr ) {

	if ( $('#books_table').attr("filled") ) {
	    $('#books_table').dataTable().fnDestroy();
	}
	
	$('#books_table').dataTable( {
	    "searching": false,
	    "ordering":  false,
	    "deferRender": true,
	    "bDeferRender": true,
	    "ordering": false,
	    "lengthChange": false, 
	    "info": false, 
	    "data": json_data,
	    "columns": [
		{ "title": "Title" },
		{ "title": "Author" }
	    ]
	} );
	
	$('#books_table').attr("filled", true);
	
    });
}

function init() {

    /* Language filter */
    var language_count = languages_json_data.length;
    if ( language_count > 1 ) {
	$( "#language_filter" ).autocomplete({
	    source: languages_json_data,
	    select: function (event, ui) {
		minimizeUI();
		showBooks();
	    }
	});
	$( "#language_filter" ).keypress( function( event ) {
	    if( event.which == 13 ) {
		if ( !this.value ) {
		    showBooks();
		}
	    }
	});
    } else {
	$( "#language_filter" ).val( languages_json_data[0] );
	$( "#language_filter" ).hide();
    }

    /* Author filter */
    $( "#author_filter" ).autocomplete({
	source: function ( request, response ) {
            var results = [];
	    var pattern = new RegExp(request.term, "i");
	    var count = authors_json_data.length;
	    var i = 0;
	    while (i < count && results.length < 100) {
		if ( authors_json_data[i][0].match(pattern) ) {
		    results.push( authors_json_data[i][0] );
		}
		i++;
	    };
	    response( results );
        },
	select: function ( event, ui ) {
	    minimizeUI();
	    showBooks();
        }
    });
    $( "#author_filter" ).keypress( function( event ) {
	if( event.which == 13 ) {
	    if ( !this.value ) {
		showBooks();
	    }
	}
    });
    
    /* Show books */
    showBooks();
}
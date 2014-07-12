function minimizeUI() {
    $( "#top-menu" ).slideUp( 300 );
    $( "#home-about" ).slideUp( 300 );
    $( "#logo2" ).show( 500, function() {
	$( "#logo2" ).show();
    });
}

function createBooksTable() {
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
}

function loadBooksData( url ) {
    $.getScript( url, function( data, textStatus, jqxhr ) {
	createBooksTable();
    });
}

function init() {

    /* Language filter */
    $(function() {
	$( "#language_filter" ).autocomplete({
	    source: languages_json_data,
	    select: function (event, ui) {
		minimizeUI();
		loadBooksData( "static/full_by_popularity.js" );
	    },
	    change: function( event ) {
		alert( "Handler for .submit() called." );
	    }
	});
    });

    /* Author filter */
    $(function() {
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
		response(results);
            },
	    select: function ( event, ui ) {
		minimizeUI();
		var count = authors_json_data.length;
		for ( i = 0 ; i < count ; i++ ) {
		    if (authors_json_data[i][0] === this.value) {
			loadBooksData( "static/auth_" + authors_json_data[i][1] + "_by_popularity.js" );
			break;
		    };
		};
            }
	});
	$( "#author_filter" ).keypress( function( event ) {
	    if( event.which == 13 ) {
		if ( !this.value ) {
		    alert( 42 );
		}
	    }
	});
    });

    /* Books */
    loadBooksData( "static/full_by_popularity.js" );
}
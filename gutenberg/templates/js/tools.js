var sortMethod = "popularity";

function minimizeUI() {
    $( "#top-menu" ).slideUp( 300 );
    $( "#home-about" ).slideUp( 300 );
    $( "#logo2" ).show( 500, function() {
	$( "#logo2" ).show();
    });
}

function showBooks() {
    var url = "full_by_" + sortMethod + ".js";

    if ( $( "#language_filter" ).val() ) {
	url = "lang_" + $( "#language_filter" ).val() + "_by_" + sortMethod + ".js";
    }

    if ( $( "#author_filter" ).val() ) {
	var count = authors_json_data.length;
	var author_filter_value = $( "#author_filter" ).val();
	for ( i = 0 ; i < count ; i++ ) {
	    if (authors_json_data[i][0] === author_filter_value) {
		url = "auth_" + authors_json_data[i][1] + "_by_" + sortMethod + ".js";
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
		{ "title": "Author" },
		{ "title": "Format" }
	    ],
	    "bAutoWidth": true,
	    "columnDefs": [
		{
		    "targets": 0,
		    "render": function ( data, type, full, meta ) {
			return "<span style=\"display: none\">" + full[3] + "</span><span>" + full[0] + "</span>";
		    }
		}, 
		{
		    "targets": 2,
		    "render": function ( data, type, full, meta ) {
			return "<a href='42'>" + data + "</a>";
		    }
		}
	    ]
	} );

	$('#books_table').on('click', 'tr', function () {
            var id = $('td', this).children()[0].innerHTML;
            var titre = $('td', this).children()[1].innerHTML;
	    var url = titre + "." + id + ".html";
	    $(location).attr("href", url);
	} );

	$('#books_table').attr("filled", true);

    });
}

function init() {

    /* Sort buttons */
    $( "#popularity_sort" ).button({
	icons: { primary: 'sort_popularity_icon' },
	text: false,
	label: 'Sort books by popularity'
    })
    $( "#popularity_sort" ).click(function() {
	sortMethod = "popularity";
	showBooks();
    });


    $( "#alpha_sort" ).button({
	icons: { primary: 'sort_alpha_icon' },
	text: false,
	label: 'Sort books by title'
    })
    $( "#alpha_sort" ).click(function() {
	sortMethod = "title";
	showBooks();
    });

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
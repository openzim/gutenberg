
var sortMethod = "popularity";
var booksUrl = "full_by_popularity.js";
var inBooksLooadingLoop = false;

function minimizeUI() {
    console.log("minimizeUI");
    $( "#hide-precontent" ).val( "true" );
    $( "#hide-precontent" ).change();
    $( ".precontent" ).slideUp( 300 );
}

function maximizeUI() {
    console.log("maximizeUI");
    $( '#hide-precontent' ).val( '' );
    $( '#hide-precontent' ).change();
    $( ".precontent" ).slideDown( 300 );
}

function loadScript(url, nodeId, callback) {
    console.log("requesting script for #"+nodeId+" from "+ url);
    if (document.getElementById(nodeId)) {
	if (document.getElementById(nodeId).src == url) {
	    return;
	}
	document.getElementById(nodeId).parentElement.
	    removeChild(document.getElementById(nodeId));
    }

    var script = document.createElement("script");
    script.setAttribute('type', "text/javascript");
    script.setAttribute('id', nodeId);
//    script.setAttribute('src', url);
    script.setAttribute('src', '../-/' + url);

    document.getElementsByTagName("head")[0].appendChild(script);
    if (script.readyState) { //IE
	script.onreadystatechange = function () {
	    if (script.readyState == "loaded" || script.readyState == "complete") {
		script.onreadystatechange = null;
		callback();
	    }
	};
    } else { //Others
	script.onload = function () {
            console.log("calling script callback");
	    callback();
	};
    }

    console.log("attaching script");
    document.getElementsByTagName("head")[0].appendChild(script);
}

function populateFilters( callback ) {
    console.log("populateFilters");

    booksUrl = "full_by_" + sortMethod + ".js";

    var language_filter_value = $( "#language_filter" ).val();
    if ( language_filter_value ) {
        var count = languages_json_data.length;
        var ok = false;
        for ( var i = 0 ; i < count ; i++ ) {
            if (languages_json_data[i][1] === language_filter_value) {
		booksUrl = "lang_" + languages_json_data[i][1] + "_by_" + sortMethod + ".js";
                ok = true;
                break;
            }
        }
        if ( !ok ) {
            $( "#language_filter" ).val("");
        }
    }

    console.log("languages populated");

    var authors_url = language_filter_value ? "authors_lang_" + language_filter_value + ".js" : "authors.js";
    loadScript( authors_url, "authors_script", function () {
        console.log("-- authors 1");
        console.log(authors_json_data);
        if ( $( "#author_filter" ).val() ) {
            console.log("-- authors 2");
            var count = authors_json_data.length;
            console.log("count: " + count);
            var author_filter_value = $( "#author_filter" ).val();
            var ok = false;
            for ( i = 0 ; i < count ; i++ ) {
                if (authors_json_data[i][0] === author_filter_value) {
                    booksUrl = "auth_" + authors_json_data[i][1] + "_by_" + sortMethod + ".js";
                    ok = true;
                    break;
                }
            }
            console.log("-- authors 3");
            if ( !ok ) {
                $( "#author_filter" ).val("");
            }
            console.log("-- authors 4");
        }

        console.log("authors populated");

        if ( callback ) {
            console.log("calling callback");
            callback();
        } else {
            console.log("no callback");
        }
    });
}

function is_cover_page() {
    return $("body").hasClass("cover");
}

function showBooks() {

    console.log("showBooks");
    /* Show spinner if loading takes more than 1 second */
    inBooksLoadingLoop = true;
    setTimeout(function() {
        if ( inBooksLoadingLoop ) {
            $("#spinner").show();
        }
    }, 1000);

    populateFilters( function() {

        console.log("populateFilters callback");

        // redirect to home page
        if (is_cover_page()) {
            console.log("Cover page, redirecting");
            $(location).attr("href", "Home.html");
        } else {
            console.log("NOT COVER PAGE");
        }

        console.log("before loadScript");

        loadScript( booksUrl, "books_script", function () {

            if ( $('#books_table').attr("filled") ) {
		$('#books_table').dataTable().fnDestroy();
            }

	    $(document).ready(function() {
		$('#books_table').dataTable( {
		    "searching": false,
		    "ordering":  false,
		    "deferRender": true,
		    "bDeferRender": true,
		    "lengthChange": false,
		    "info": false,
		    "data": json_data,
		    "columns": [
			{ "title": "" },
			{ "title": "" },
			{ "title": "" }
		    ],
		    "bAutoWidth": false,
		    "columnDefs": [
			{ "bVisible": false, "aTargets": [1] },
			{ "sClass": "table-icons", "aTargets": [2] },
			{
			    "targets": 0,
			    "render": function ( data, type, full, meta ) {
				div = "<div class=\"list-stripe\"></div>";
				title = "<span style=\"display: none\">" + full[3] + "</span>";
				title += " <span class = \"table-title\">" + full[0] + "</span>";
				author = ((full[1]=='Anonymous')?
					  "<span class=\"table-author\" data-l10n-id=\"author-anonymous\">" + document.webL10n.get('author-anonymous') + "</span>"
					  :((full[1]=='Various')?
					    "<span class=\"table-author\" data-l10n-id=\"author-various\">" + document.webL10n.get('author-various') + "</span>"
					    :
					    "<span class=\"table-author\">" + full[1] + "</span>"));
				
                    return div + "<div>" + title + "<br>" + author + "</div";
			    }
			},
			{
			    "targets": 1,
			    "render": function ( data, type, full, meta ) {
				return "";
			    }
			},

			{
			    "targets": 2,
			    "render": function ( data, type, full, meta ) {
				var html = "";
				var urlBase = encodeURIComponent( full[0].replace( "/", "-" ).substring(0, 230) );

				if (data[0] == 1) {
				    html += "<a title=\"" + full[0]+ ": HTML\" href=\"../A/" + urlBase + "." + full[3] + ".html\"><i class=\"fa fa-html5 fa-3x\"></i></a>";
				}
				if (data[1] == 1) {
				    html += "<a title=\"" + full[0]+ ": EPUB\" href=\"../I/" + urlBase + "." + full[3] + ".epub\"><i class=\"fa fa-book fa-3x\"></i></a>";
				}
				if (data[2] == 1) {
				    html += "<a title=\"" + full[0]+ ": PDF\" href=\"../I/" + urlBase + "." + full[3] + ".pdf\"><i class=\"fa fa-file-pdf-o fa-3x\"></i></a>";
				}

				return html;
			    }
			}
		    ]
		} );
	    } );

	    /* Book list click handlers */
	    $('#books_table').on('mouseup', 'tr td:first-child', function ( event ) {
                var id = $('span', this)[0].innerHTML;
                var titre = $('span.table-title', this)[0].innerHTML;

		if ( event.which == 1 ) { /* Left click */
                    $(location).attr("href", encodeURIComponent( titre.replace( "/", "-" ).substring(0, 230) ) + "_cover." + id + ".html" );
		} else if ( event.which == 2 ) { /* Middle click */
		    var href = $(this).attr('data-href');
		    var link = $('<a href="' + encodeURIComponent( titre.replace( "/", "-" ).substring(0, 230) ) + "_cover." + id + ".html" + '" />');
		    link.attr('target', '_blank');
		    window.open(link.attr('href'));
		}
            });

            $("#books_table_paginate").click( function() { minimizeUI(); });
            $('#books_table').attr("filled", true);

            $('.sort').show();

            /* Hide Spinner */
            inBooksLoadingLoop = false;
            $("#spinner").hide();

	    /* Translate books table back/next buttons */
	    $( "#books_table_previous" ).attr( "data-l10n-id", "table-previous" );
	    $( "#books_table_previous" ).html( document.webL10n.get( "table-previous" ) );
	    $( "#books_table_next" ).attr( "data-l10n-id", "table-next" );
	    $( "#books_table_next" ).html( document.webL10n.get( "table-next" ) );
        });
        console.log("after loadScript");
    });
    console.log("after populateFilters");

}

function onLocalized() {
    var l10n = document.webL10n;
    var l10nselect = $("#l10nselect");
    l10nselect.val(l10n.getLanguage());
    l10nselect.on('change', function(e) {
        l10n.setLanguage($(this).val());
    });
}

function init() {

    /* Persistence of form values */
    jQuery('input,select,textarea').persist({
	context: 'gutenberg', // a context or namespace for each field
	cookie: 'gutenberg', // cookies basename
	expires: 1 // cookie expiry (eg 365)
    });

    /* Hide home about */
    if ( $( "#hide-precontent" ).val() == "true" ) {
        $( ".precontent" ).hide();
    }

    // search button
    $('.search').on('click', function (e) {
        e.preventDefault();
        showBooks();
    });

    /* Language filter, fill language selector with langs from JS file */
    var language_filter = $("#language_filter");

    function create_options(parent, langlist) {
        $(langlist).each(function (index, lang) {
            var opt = $('<option />');
            opt.val(lang[1]);
            var txt = lang[0] + ' (' + lang[2] + ')';
            opt.text(txt);
            opt.attr('label', txt);
            parent.append(opt);
        });
    }

    if (other_languages_json_data.length) {
        var main_group = $('<optgroup>');
        main_group.attr('label', document.webL10n.get('main-languages'));
        create_options(main_group, main_languages_json_data);
        language_filter.append(main_group);

        var other_group = $('<optgroup>');
        other_group.attr('label', document.webL10n.get('other-languages'));
        create_options(other_group, other_languages_json_data);
        language_filter.append(other_group);
    } else {
        create_options(language_filter, languages_json_data);
    }

    language_filter.on('change', function (e) {
        minimizeUI();
        showBooks();
    });
    if ( languages_json_data.length == 1 ) {
        language_filter.val( languages_json_data[0][1] );
        language_filter.hide();
    }

    /* Sort buttons */
    $( ".sort" ).hide();
    $( "#popularity_sort" ).click(function() {
        sortMethod = "popularity";
        $( "#default-sort" ).val( sortMethod );
        $( "#default-sort" ).change();
        $( "#popularity_sort" ).addClass( "fa-selected" );
        $( "#alpha_sort" ).removeClass( "fa-selected" );
        minimizeUI();
        showBooks();
    });

    $( "#alpha_sort" ).click(function() {
        sortMethod = "title";
        $( "#default-sort" ).val( sortMethod );
        $( "#default-sort" ).change();
        $( "#alpha_sort" ).addClass( "fa-selected" );
        $( "#popularity_sort" ).removeClass( "fa-selected" );
        minimizeUI();
        showBooks();
    });

    if ( $( "#default-sort" ).val() == "popularity" ) {
        $( "#popularity_sort" ).addClass( "fa-selected" );
        sortMethod = "popularity";
    } else {
        $( "#alpha_sort" ).addClass( "fa-selected" );
        sortMethod = "title";
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
        }
        response( results );
        },
    select: function ( event, ui ) {
        minimizeUI();
        showBooks();
        }
    });
    $( "#author_filter" ).keypress( function( event ) {
    if( event.which == 13 ) {
        showBooks();
    }
    });

}

document.webL10n.ready(onLocalized);

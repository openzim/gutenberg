var sortMethod = "popularity";

function minimizeUI() {
    $( "#top-menu" ).slideUp( 300 );
    $( "#home-about" ).slideUp( 300 );
    $( "#logo2" ).show( 500, function() {
	$( "#logo2" ).show();
    });
}

function displayError(message) {

    // create unique id for div
    var dialog_id = "error_dialog_" + new Date().getTime();

    // append html to body
    $("body").append("<div id=\"" + dialog_id + "\">" + message + "</div>");

    // display the error dialog
    $("#" + dialog_id).dialog({
    modal: true,
    resizable: false,
    height: 130,
    width: 250,
    title: "Error",
    buttons: {
        Ok: function() {
        $(this).dialog("close");
        }
    },
    beforeClose: function(event, ui) {
        // remove dialog div from document
        $("#" + dialog_id).remove();
    }
    });
}

function loadScript(url, nodeId, callback) {
    document.getElementById( nodeId ).parentElement.
    removeChild( document.getElementById( nodeId ) );

    var script = document.createElement("script")
    script.type = "text/javascript";
    script.id = nodeId;

    if (script.readyState) { //IE
        script.onreadystatechange = function () {
            if (script.readyState == "loaded" || script.readyState == "complete") {
                script.onreadystatechange = null;
                callback();
            }
        };
    } else { //Others
        script.onload = function () {
            callback();
        };
    }

    script.src = url;
    document.getElementsByTagName("head")[0].appendChild(script);
}

function showBooks() {
    var url = "full_by_" + sortMethod + ".js";

    var language_filter_value = $( "#language_filter" ).val();
    if ( language_filter_value ) {
        var count = languages_json_data.length;
        var ok = false;
        for ( i = 0 ; i < count ; i++ ) {
            if (languages_json_data[i][1] === language_filter_value) {
                url = "lang_" + languages_json_data[i][1] + "_by_" + sortMethod + ".js";
                ok = true;
                break;
            };
        };
        if ( !ok ) {
            return false;
        }
    }

    var authors_url = language_filter_value ? "authors_lang_" + language_filter_value + ".js" : "authors.js";
    loadScript( authors_url, "authors_script", function () {
	if ( $( "#author_filter" ).val() ) {
	    var count = authors_json_data.length;
	    var author_filter_value = $( "#author_filter" ).val();
	    var ok = false;
	    for ( i = 0 ; i < count ; i++ ) {
		if (authors_json_data[i][0] === author_filter_value) {
		    url = "auth_" + authors_json_data[i][1] + "_by_" + sortMethod + ".js";
		    ok = true;
		    break;
		};
	    };
	    if ( !ok ) {
		$( "#author_filter" ).val("")
		return false;
	    }
	}
	
	if ( $( "#cover" ).length > 0 ) {
	    $(location).attr("href", "Home.html");
	}
	
	loadScript( url, "books_script", function () {
	    
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
			    div = "<div class=\"list-stripe\"></div>"
			    title = "<span style=\"display: none\">" + full[3] + "</span>";
			    title += " <span class = \"table-title\">" + full[0] + "</span>"
			    author = "<span class=\"table-author\">" + full[1] + "</span>";
			    
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
			    var urlBase = full[0].replace( "/", "-" );
			    
			    if (data[0] == 1) {
				html += "<a href=\"" + urlBase + "." + full[3] + ".html\"><i class=\"fa fa-html5 fa-2x\"></i></a>";
			    }
			    if (data[1] == 1) {
				html += "<a href=\"" + urlBase + "." + full[3] + ".epub\"><i class=\"fa fa-book fa-2x\"></i></a>";
			    }
			    if (data[2] == 1) {
				html += "<a href=\"" + urlBase + "." + full[3] + ".pdf\"><i class=\"fa fa-file-pdf-o fa-2x\"></i></a>";
			    }
			    return html;
			}
		    }
		]
	    } );
	    
	    $('#books_table').on('click', 'tr td:first-child', function () {
		var id = $('span', this)[0].innerHTML;
		var titre = $('span.table-title', this)[0].innerHTML;
		var url = titre.replace( "/", "-" ) + "_cover." + id + ".html";
		$(location).attr("href", url);
	    } );
	    $("#books_table_paginate").click( function() { minimizeUI() }); 
	    $('#books_table').attr("filled", true);
	    
	    $('#sort').show();
	});
    });

    return true;
}

function onLocalized() {
    var l10n = document.webL10n,
        l10nselect = document.getElementById('l10nselect');
    l10nselect.value = l10n.getLanguage(); // not working with IE<9
    l10nselect.onchange = function() {
        l10n.setLanguage(this.value || this.options[this.selectedIndex].text);
    };
};
document.webL10n.ready(onLocalized);

function init() {

    /* Sort buttons */
    $( "#sort" ).hide();
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
    $( "#popularity_sort" ).removeClass('ui-state-focus');
    $( "#alpha_sort" ).addClass('ui-state-focus');
    });

    /* Language filter */
    var language_filter = $("#language_filter");
    // fill language selector with langs from JS file

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
        main_group.attr('label', "Main languages");
        create_options(main_group, main_languages_json_data);
        language_filter.append(main_group);

        var other_group = $('<optgroup>');
        other_group.attr('label', "Other languages");
        create_options(other_group, other_languages_json_data);
        language_filter.append(other_group);
    } else {
        create_options(language_filter, languages_json_data);
    }

    language_filter.on('change', function (e) {
        minimizeUI();
        if (!showBooks()) {
            displayError( "No books matching these criterias." );
            $(this).val("");
        }
    });
    if ( languages_json_data.length == 1 ) {
        language_filter.val( languages_json_data[0][1] );
        language_filter.hide();
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
        if (!showBooks()) {
        displayError( "No books matching these criterias." );
        this.value = "";
        }
    }
    });

    /* Persistence of form values */
    jQuery('input,select,textarea').persist(
    {
            context : 'gutenberg',  // a context or namespace for each field
            replace : true,         // replace existing field contents if any
            cookie  : 'gutenberg',  // cookies basename
            path    : '/',          // cookie path
            domain  : null,         // cookie domain
            expires : null          // cookie expiry (eg 365)
    }
    );

    var l10nselect = document.getElementById('l10nselect');
    document.webL10n.setLanguage(l10nselect.value || l10nselect.options[this.selectedIndex].text);
}

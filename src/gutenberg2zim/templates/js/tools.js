var sortMethod = "popularity";
var booksUrl = "full_by_popularity.js";
var bookshelves = "bookshelves.js";
var booksTable = null;
var title_dict = null;
var globalShelvesTable = null;
var persist_options = {
  context: "gutenberg", // a context or namespace for each field
  cookie: "{{ project_id }}", // cookies basename
  expires: 1, // cookie expiry (eg 365)
  replace: true,
  debug: true,
};

function getPersistedPage() {
  var pp = $("#page_record").val();
  try {
    return parseInt(pp);
  } catch (e) {
    if (pp) {
      console.log(e);
      console.warn("Unable to work with persisted page `" + pp + "`");
    }
    return 0;
  }
}

function onTablePageChange(e, settings, table) {
  // record global ref to table
  if (table)
    booksTable = table;
  $("#page_record").val(booksTable.api().page());
  // console.debug(info);
}

function goToAuthor(name) {
  $("#author_filter").val(name);
  $("#author_filter").change();
  showBooks();
}

function minimizeUI() {
  console.log("minimizeUI");
  $("#hide-precontent").val("true");
  $("#hide-precontent").change();
  $(".precontent").slideUp(300);
}

function loadScript(url, nodeId, callback) {
  console.log("requesting script for #" + nodeId + " from " + url);
  if (document.getElementById(nodeId)) {
    if (document.getElementById(nodeId).src == url) {
      return;
    }
    document.getElementById(nodeId).parentElement.
    removeChild(document.getElementById(nodeId));
  }

  var script = document.createElement("script");
  script.setAttribute("type", "text/javascript");
  script.setAttribute("id", nodeId);
  script.setAttribute("src", url);

  document.getElementsByTagName("head")[0].appendChild(script);
  if (script.readyState) { //IE
    script.onreadystatechange = function() {
      if (script.readyState == "loaded" || script.readyState == "complete") {
        script.onreadystatechange = null;
        callback();
      }
    };
  } else { //Others
    script.onload = function() {
      console.log("calling script callback");
      callback();
    };
  }

  console.log("attaching script");
  document.getElementsByTagName("head")[0].appendChild(script);
}

function populateFilters(callback) {
  console.log("populateFilters");

  var language_filter_value = $("#language_filter").val();
  var lang_id = null;
  if (language_filter_value) {
    var count = languages_json_data.length;
    for (var i = 0; i < count; i++) {
      if (languages_json_data[i][1] === language_filter_value) {
        lang_id = languages_json_data[i][1];
        break;
      }
    }
  } else
    language_filter_value = null;
  $("#language_filter").val(lang_id);

  // console.log("languages populated");

  var authors_url = language_filter_value ? "authors_lang_" + language_filter_value + ".js" : "authors.js";
  loadScript(authors_url, "authors_script", function() {
    var author_filter_value = $("#author_filter").val();
    var author_id = null;
    if (author_filter_value) {
      var count = authors_json_data.length;
      for (i = 0; i < count; i++) {
        if (authors_json_data[i][0] === author_filter_value) {
          author_id = authors_json_data[i][1];
          break;
        }
      }
      if (author_id === null && author_filter_value) {
        // lang and author not matching but content in field: clear
        $("#author_filter").val("");
        $(".clearable").trigger("input");
      }
    } else
      author_filter_value = null;

    // console.log("authors populated");

    // figure out what to request now (lang_id, author_id, sortMethod)
    if (lang_id && author_id) {
      // we want a reduce of both
      booksUrl = "auth_" + author_id + "_lang_" + lang_id + "_by_" + sortMethod;
      bookshelves = "bookshelves_lang_" + lang_id;
    } else if (author_id) {
      // only books by this author
      booksUrl = "auth_" + author_id + "_by_" + sortMethod;
    } else if (lang_id) {
      // all books in this language
      booksUrl = "lang_" + lang_id + "_by_" + sortMethod;
      bookshelves = "bookshelves_lang_" + lang_id;
    } else {
      // all books, no reduce
      booksUrl = "full_by_" + sortMethod;
      bookshelves = "bookshelves";
    }
    booksUrl += ".js";
    bookshelves += ".js";
    // console.debug("FILTER: " + "lang: " + lang_id + " auth: " + author_id + " sort: " + sortMethod);
    // console.debug(booksUrl);
    console.log(bookshelves);
    if (callback) {
      // console.debug("calling callback");
      callback();
    } else {
      // console.debug("no callback");
    }
  });
}

function is_cover_page() {
  return $("body").hasClass("cover");
}

function is_bookshelves_page() {
  return $('#bookshelvesDisplay').length != 0;
}

function showBooks() {
  console.log("showBooks");
  /* Show spinner if loading takes more than 1 second */
  inBooksLoadingLoop = true;
  setTimeout(function() {
    if (inBooksLoadingLoop) {
      $("#spinner").show();
    }
  }, 1000);

  populateFilters(function() {
    console.log("populateFilters callback");

    // redirect to home page
    if (is_cover_page()) {
      console.log("Cover page, redirecting");
      $(location).attr("href", "Home.html");
    } else {
      console.log("NOT COVER PAGE");
    }

    console.log("before loadScript");
    loadScript(booksUrl, "books_script", function() {
      if ($("#books_table").attr("filled")) {
        booksTable.fnDestroy();
      }

      $(document).ready(function() {
        booksTable = $("#books_table").dataTable({
          initComplete: function() {
            var requestedPage = getPersistedPage();
            if (requestedPage) {
              this.api()
                .page(requestedPage)
                .draw(false);
              // fire event as not registered/ready yet
              onTablePageChange(null, null, this);
            }
          },
          searching: false,
          ordering: false,
          deferRender: true,
          bDeferRender: true,
          lengthChange: false,
          info: false,
          data: json_data,
          columns: [{
            title: ""
          }, {
            title: ""
          }, {
            title: ""
          }],
          bAutoWidth: false,
          columnDefs: [{
              bVisible: false,
              aTargets: [1]
            },
            {
              sClass: "table-icons",
              aTargets: [2]
            },
            {
              targets: 0,
              render: function(data, type, full) {
                img = '<img class="pure-u-1-8 book-cover-pre" src= "' + full[3] + '_cover_image.jpg"' +
                  'onerror="this.onerror=null;this.style.height=\'50px\';this.src=\'' + 'favicon.png\'" >';
                stripe = '<div class="list-stripe"></div>';
                title = '<span style="display: none">' + full[3] + '</span>';
                title += ' <span class = "table-title">' + full[0] + '</span>';
                author =
                  full[1] == 'Anonymous' ?
                  '<span class="table-author" data-l10n-id="author-anonymous">' +
                  document.webL10n.get('author-anonymous') +
                  '</span>' :
                  full[1] == 'Various' ?
                  '<span class="table-author" data-l10n-id="author-various">' +
                  document.webL10n.get('author-various') +
                  '</span>' :
                  '<span class="table-author">' + full[1] + '</span>';
                infoContainer = '<div class="pure-u-7-8">' + title + '<br>' + author + '</div>';
                innerGrid = '<div class="pure-g">' + img + infoContainer + '</div>';
                return '<div class="book-item">' + stripe + innerGrid + '</div>';
              }
            },
            {
              targets: 1,
              render: function() {
                return "";
              }
            },
            {
              targets: 2,
              render: function(data, type, full) {
                var html = "";
                var urlBase =
                  full[0].replace("/", "-").substring(0, 230) + "." + full[3];
                urlBase = encodeURIComponent(urlBase);

                if (data[0] == 1) {
                  html +=
                    '<a class="home-icon" title="' +
                    full[0] +
                    ': HTML" href="' +
                    urlBase +
                    '.html"><i class="fa fa-html5 fa-3x"></i></a>';
                }
                if (data[1] == 1) {
                  html +=
                    '<a class="home-icon" title="' +
                    full[0] +
                    ': EPUB" href="' +
                    urlBase +
                    '.epub"><i class="fa fa-download fa-3x"></i></a>';
                }
                if (data[2] == 1) {
                  html +=
                    '<a class="home-icon" title="' +
                    full[0] +
                    ': PDF" href="' +
                    urlBase +
                    '.pdf"><i class="fa fa-file-pdf-o fa-3x"></i></a>';
                }

                return html;
              }
            }
          ]
        });
        $("#books_table").on("page.dt", onTablePageChange);
      });

      /* Book list click handlers */
      $("#books_table").on("mouseup", "tr td:first-child", function(event) {
        var id = $("span", this)[0].innerHTML;
        var titre = $("span.table-title", this)[0].innerHTML;

        if (event.which == 1) {
          /* Left click */
          $(location).attr(
            "href",
            encodeURIComponent(titre.replace("/", "-").substring(0, 230)) +
            "_cover." +
            id +
            ".html"
          );
        } else if (event.which == 2) {
          /* Middle click */
          var link = $(
            "<a href='" +
            encodeURIComponent(titre.replace("/", "-").substring(0, 230)) +
            "_cover." +
            id +
            ".html" +
            "' />"
          );
          link.attr("target", "_blank");
          window.open(link.attr("href"));
        }
      });

      $("#books_table_paginate").click(function() {
        minimizeUI();
      });
      $("#books_table").attr("filled", true);

      $(".sort").show();

      /* Hide Spinner */
      inBooksLoadingLoop = false;
      $("#spinner").hide();

      /* Translate books table back/next buttons */
      $("#books_table_previous").attr("data-l10n-id", "table-previous");
      $("#books_table_previous").html(document.webL10n.get("table-previous"));
      $("#books_table_next").attr("data-l10n-id", "table-next");
      $("#books_table_next").html(document.webL10n.get("table-next"));
    });
    console.log("after loadScript");
  });
  console.log("after populateFilters");
}

function showBookshelf(bookshelfURL) {
  console.log("showBookshelf");
  /* Show spinner if loading takes more than 1 second */
  inBooksLoadingLoop = true;
  setTimeout(function() {
    if (inBooksLoadingLoop) {
      $("#spinner").show();
    }
  }, 1000);

  populateFilters(function() {
    console.log("populateFilters callback");

    // redirect to home page
    // if (is_cover_page()) {
    //   console.log("Cover page, redirecting");
    //   $(location).attr("href", "Home.html");
    // } else {
    //   console.log("NOT COVER PAGE");
    // }

    console.log("before loadScript");
    bookshelfURL = jQuery.trim(bookshelfURL);
    let scriptURL = `bookshelf_${bookshelfURL}_by_title.js`;
    const lang_id = $("#language_filter").val();
    $("#language_filter").hide();
    console.log(`lang_id === ${lang_id}`);
    if (lang_id !== '') {
      scriptURL = `bookshelf_${bookshelfURL}_lang_${lang_id}_by_title.js`;
    }
    // const scriptURL = "bookshelf_Adventure_lang_en_by_popularity.js"
    console.log("loading bookshelf:", scriptURL);
    loadScript(scriptURL, "books_script", function() {
      if ($("#books_table").attr("filled")) {
        booksTable.fnDestroy();
      }

      $(document).ready(function() {
        booksTable = $("#books_table").dataTable({
          initComplete: function() {
            var requestedPage = getPersistedPage();
            if (requestedPage) {
              this.api()
                .page(requestedPage)
                .draw(false);
              // fire event as not registered/ready yet
              onTablePageChange(null, null, this);
            }
          },
          searching: false,
          ordering: false,
          deferRender: true,
          bDeferRender: true,
          lengthChange: false,
          info: false,
          data: json_data,
          columns: [{
            title: ""
          }, {
            title: ""
          }, {
            title: ""
          }],
          bAutoWidth: false,
          columnDefs: [{
              bVisible: false,
              aTargets: [1]
            },
            {
              sClass: "table-icons",
              aTargets: [2]
            },
            {
              targets: 0,
              render: function(data, type, full) {
                img = '<img class="pure-u-1-8 book-cover-pre" src= "' + full[3] + '_cover_image.jpg"' +
                  'onerror="this.onerror=null;this.style.height=\'50px\';this.src=\'' + 'favicon.png\'" >';
                div = '<div class="list-stripe"></div>';
                title = '<span style="display: none">' + full[3] + '</span>';
                title += ' <span class = "table-title">' + full[0] + '</span>';
                author =
                  full[1] == 'Anonymous' ?
                  '<span class="table-author" data-l10n-id="author-anonymous">' +
                  document.webL10n.get('author-anonymous') +
                  '</span>' :
                  full[1] == 'Various' ?
                  '<span class="table-author" data-l10n-id="author-various">' +
                  document.webL10n.get('author-various') +
                  '</span>' :
                  '<span class="table-author">' + full[1] + '</span>';
                infoContainer = '<div class="pure-u-7-8">' + title + '<br>' + author + '</div>';
                innerGrid = '<div class="pure-g">' + img + infoContainer + '</div>';
                return '<div class="book-item">' + div + '<div>' + innerGrid + '</div></div>';
              }
            },
            {
              targets: 1,
              render: function() {
                return "";
              }
            },
            {
              targets: 2,
              render: function(data, type, full) {
                var html = "";
                var urlBase =
                  full[0].replace("/", "-").substring(0, 230) + "." + full[3];
                urlBase = encodeURIComponent(urlBase);

                if (data[0] == 1) {
                  html +=
                    '<a class="home-icon" title="' +
                    full[0] +
                    ': HTML" href="' +
                    urlBase +
                    '.html"><i class="fa fa-html5 fa-3x"></i></a>';
                }
                if (data[1] == 1) {
                  html +=
                    '<a class="home-icon" title="' +
                    full[0] +
                    ': EPUB" href="' +
                    urlBase +
                    '.epub"><i class="fa fa-download fa-3x"></i></a>';
                }
                if (data[2] == 1) {
                  html +=
                    '<a class="home-icon" title="' +
                    full[0] +
                    ': PDF" href="' +
                    urlBase +
                    '.pdf"><i class="fa fa-file-pdf-o fa-3x"></i></a>';
                }

                return html;
              }
            }
          ]
        });
        $("#books_table").on("page.dt", onTablePageChange);
      });

      /* Book list click handlers */
      $("#books_table").on("mouseup", "tr td:first-child", function(event) {
        var id = $("span", this)[0].innerHTML;
        var titre = $("span.table-title", this)[0].innerHTML;

        if (event.which == 1) {
          /* Left click */
          $(location).attr(
            "href",
            encodeURIComponent(titre.replace("/", "-").substring(0, 230)) +
            "_cover." +
            id +
            ".html"
          );
        } else if (event.which == 2) {
          /* Middle click */
          var link = $(
            "<a href='" +
            encodeURIComponent(titre.replace("/", "-").substring(0, 230)) +
            "_cover." +
            id +
            ".html" +
            "' />"
          );
          link.attr("target", "_blank");
          window.open(link.attr("href"));
        }
      });

      $("#books_table_paginate").click(function() {
        minimizeUI();
      });
      $("#books_table").attr("filled", true);

      $(".sort").show();

      /* Hide Spinner */
      inBooksLoadingLoop = false;
      $("#spinner").hide();

      /* Translate books table back/next buttons */
      $("#books_table_previous").attr("data-l10n-id", "table-previous");
      $("#books_table_previous").html(document.webL10n.get("table-previous"));
      $("#books_table_next").attr("data-l10n-id", "table-next");
      $("#books_table_next").html(document.webL10n.get("table-next"));
    });
    console.log("after loadScript");
  });
  console.log("after populateFilters");
}

function onLocalized() {
  var l10n = document.webL10n;
  var l10nselect = $("#l10nselect");

  var detectedLang = l10n.getLanguage();
  console.debug("detected language: " + detectedLang);
  var persistedLang = jQuery.persistedValue("l10nselect", persist_options);
  console.debug("persisted language: " + persistedLang);
  if (persistedLang && persistedLang != detectedLang) {
    // we have a different persisted language
    // console.debug("persisted lang " + persistedLang +" != browser lang " + detectedLang);
    l10nselect.val(persistedLang);
    l10n.setLanguage(persistedLang);
  } else {
    // console.debug("no persisted lang or equal to browser, updating select");
    l10nselect.val(detectedLang);
  }

  // Check if it's RTL languages and update on direction
  var isRTL = l10n.getDirection();
  l10n.setDirection(isRTL);

  l10nselect.on("change", function() {
    // console.debug("on change, setting lang " + $(this).val());
    $.persistValue("l10nselect", $(this).val(), persist_options);
    l10n.setLanguage($(this).val());
  });
}

function init() {
  /* Persistence of form values */
  $("input,select,textarea").persist(persist_options);

  /* Hide home about */
  if ($("#hide-precontent").val() == "true") {
    $(".precontent").hide();
  }

  // search button
  $(".search").on("click", function(e) {
    e.preventDefault();
    showBooks();
  });

  /* Language filter, fill language selector with langs from JS file */
  var language_filter = $("#language_filter");

  function create_options(parent, langlist) {
    $(langlist).each(function(index, lang) {
      var opt = $("<option />");
      opt.val(lang[1]);
      var txt = lang[0] + " (" + lang[2] + ")";
      if (is_bookshelves_page()) {
        txt = lang[0];
      }
      opt.text(txt);
      opt.attr("label", txt);
      parent.append(opt);
    });
  }

  if (other_languages_json_data.length) {
    var main_group = $("<optgroup>");
    main_group.attr("label", document.webL10n.get("main-languages"));
    create_options(main_group, main_languages_json_data);
    language_filter.append(main_group);

    var other_group = $("<optgroup>");
    other_group.attr("label", document.webL10n.get("other-languages"));
    create_options(other_group, other_languages_json_data);
    language_filter.append(other_group);
  } else {
    create_options(language_filter, languages_json_data);
  }

  language_filter.on("change", function() {
    minimizeUI();
    if (globalShelvesTable == null) {
      showBooks();
    } else {
      showBookshelfSearchResults("");
    }
  });
  if (languages_json_data.length == 1) {
    // console.debug("ONLY ONE language");
    // console.debug(languages_json_data);
    language_filter.val(languages_json_data[0][1]);
    language_filter.hide();
  } else {
    // is there a persisted value?
    var plang = jQuery.persistedValue("language_filter", persist_options);
    if (plang && !language_filter.val()) {
      language_filter.val(plang);
    }
  }

  /* Sort buttons */
  $(".sort").hide();
  $("#popularity_sort").click(function() {
    sortMethod = "popularity";
    $("#default-sort").val(sortMethod);
    $("#default-sort").change();
    $("#popularity_sort").addClass("fa-selected");
    $("#alpha_sort").removeClass("fa-selected");
    minimizeUI();
    showBooks();
  });

  $("#alpha_sort").click(function() {
    sortMethod = "title";
    $("#default-sort").val(sortMethod);
    $("#default-sort").change();
    $("#alpha_sort").addClass("fa-selected");
    $("#popularity_sort").removeClass("fa-selected");
    minimizeUI();
    showBooks();
  });

  if ($("#default-sort").val() == "popularity") {
    $("#popularity_sort").addClass("fa-selected");
    sortMethod = "popularity";
  } else {
    $("#alpha_sort").addClass("fa-selected");
    sortMethod = "title";
  }

  /* Author filter */
  $("#author_filter").autocomplete({
    source: function(request, response) {
      var results = [];
      var pattern = new RegExp(request.term, "i");
      var count = authors_json_data.length;
      var i = 0;
      while (i < count && results.length < 100) {
        if (authors_json_data[i][0].match(pattern)) {
          results.push(authors_json_data[i][0]);
        }
        i++;
      }
      response(results);
    },
    select: function(event, ui) {
      minimizeUI();
      $.persistValue("author_filter", ui.item.value, persist_options);
      showBooks();
    }
  });
  $("#author_filter").keypress(function(event) {
    if (event.which == 13) {
      $.persistValue("author_filter", $(this).val(), persist_options);
      showBooks();
    }
  });

  /* Title filter */
  $("#title_filter").autocomplete({
    source: function(request, response) {
      loadScript(booksUrl, "find_books", function() {
        var results = [];
        var pattern = new RegExp(request.term, "i");
        var count = json_data.length;
        var i = 0;
        title_dict = {}
        while (i < count && results.length < 100) {
          if (json_data[i][0].match(pattern)) {
            results.push(json_data[i][0]);
            title_dict[json_data[i][0]] = json_data[i][3];
          }
          i++;
        }
        response(results);
      })
    },
    select: function(event, ui) {
      minimizeUI();
      let url = "./" + encodeURIComponent(ui.item.value.replace(/\//g, "-")) + "_cover." + title_dict[ui.item.value] + ".html";
      $(location).attr("href", url);
    }
  });

  $("#title_filter").keypress(function(event) {
    if (event.which == 13) {
      if ($(this).val().length === 0 || title_dict === null || title_dict[$(this).val()] === undefined) {
        $(this).val("");
        return;
      }

      let url = "./" + encodeURIComponent($(this).val().replace(/\//g, "-")) + "_cover." + title_dict[$(this).val()] + ".html";
      $(location).attr("href", url);
    }
  });

  $("#bookshelf_filter").keypress(function(event) {
    if (event.which == 13) {
      $.persistValue("author_filter", $(this).val(), persist_options);
      showBookshelfSearchResults($(this).val());
    }
  });

  // author filter UI (X to remove entry)
  function tog(v) {
    return v ? "addClass" : "removeClass";
  }

  function activate_field(selector) {
    var e = jQuery.Event("keypress");
    e.which = 13; // enter
    e.keyCode = 13;
    $(selector).trigger(e);
  }
  $(document)
    .on("input", ".clearable", function() {
      $(this)[tog(this.value)]("x");
    })
    .on("mousemove", ".x", function(e) {
      $(this)[
        tog(
          this.offsetWidth - 18 < e.clientX - this.getBoundingClientRect().left
        )
      ]("onX");
    })
    .on("touchstart click", ".onX", function(ev) {
      ev.preventDefault();
      $(this)
        .removeClass("x onX")
        .val("")
        .change();
      activate_field($(this));
    });

  // enable clearable if persisted value
  if ($("#author_filter").val()) {
    $("#author_filter").addClass("x onX");
    console.log("author filter filled");
  }
  if ($("#title_filter").val()) {
    $("#title_filter").addClass("x onX");
    console.log("title filter filled")
  }
  if ($("#bookshelf_filter").val()) {
    $("#bookshelf_filter").addClass("x onX");
    console.log("title filter filled")
  } else {
    console.log("not filled")
  }
}

function showBookshelfSearchResults(value) {

  let lang_id = $("#language_filter").val();
  console.log(lang_id + " for bookshelfresults");
  if (lang_id === "") {
    bookshelves = "bookshelves.js";
  } else {
    bookshelves = "bookshelves_lang_" + lang_id + ".js";
  }
  console.log(bookshelves + " file");
  loadScript(bookshelves, "find_bookshelves_" + lang_id, function() {
    let pattern = new RegExp(value, "i");
    if (lang_id !== "") {
      bookshelves_json_data = json_data;
    }
    if (globalShelvesTable != null) {
      globalShelvesTable.destroy();
      $("#bookShelfTable").remove();
    }
    let table = "<table id = \"bookShelfTable\" class=\" display  no-footer\" role = 'grid' filled ='true' ><thead><tr><th>Bookshelves</th></tr></thead><tbody>";
    // console.log(bookshelves_lang_en_json_data);
    // bookshelves_json_data = json_data;
    for (let i = 0; i < bookshelves_json_data.length; ++i) {
      if (bookshelves_json_data[i] == null) {
        continue;
      }

      if (bookshelves_json_data[i].match(pattern)) {
        table += '<tr  ><td><div class="book-item"><div class="list-stripe"></div><div class = "pure-g"><div class = "pure-u-7-8"> <span class="table-title">' +
          bookshelves_json_data[i] +
          '</span></div></div></div></td></tr>';
      }
    }
    table += "</tbody></table>";
    $("#bookshelvesDisplay").append($(table));
    globalShelvesTable = $("#bookShelfTable").DataTable({
      searching: false,
      info: false,
      destroy: true,
      stripeClasses: [],
      columnDefs: [{
        targets: -1,
        className: "dt-body-left"
      }]
    });

    $('#bookShelfTable tbody').on('click', 'tr', function() {
      let data = encodeURI($('span', this)[0].innerHTML);
      console.log(data);
      $(location).attr('href', './' + data + '.html');

    });
    $("#bookShelfTable_previous").attr("data-l10n-id", "table-previous");
    $("#bookShelfTable_previous").html(document.webL10n.get("table-previous"));
    $("#bookShelfTable_next").attr("data-l10n-id", "table-next");
    $("#bookShelfTable_next").html(document.webL10n.get("table-next"));
  });

  // enable clearable if persisted value
  if ($("#author_filter").val()) {
    $("#author_filter").addClass("x onX");
  }
}
$('#bookshelf_filter').keypress(function(event) {
  if (event.which == 13) {
    showBookshelfSearchResults($(this).val());
  }
});




document.webL10n.ready(onLocalized);

function author_clicked() {
  if (this.dataset.authorName) {
    goToAuthor(this.dataset.authorName)
  }
}

$(window).on('load', function () {
  const show_books = (document.querySelector('meta[name="show_books"]').content === "true");
  const bookshelf_home = (document.querySelector('meta[name="bookshelf_home"]').content === "true");
  const bookshelf = document.querySelector('meta[name="bookshelf"]').content

  init();

  if (show_books) {
    showBooks();
  } else {
    populateFilters();
  }

  if (bookshelf_home) {
    showBookshelfSearchResults('');
  }

  if (bookshelf.length>0) {
    showBookshelf(bookshelf);
  }

  const authorBtns = document.getElementsByClassName("author-btn");
  for (var i = 0; i < authorBtns.length; ++i) {
      authorBtns[i].addEventListener("click", author_clicked);
  }

});

import pytest

from gutenberg2zim.rdf import RdfParser

RDF_HEADER = """
<?xml version="1.0" encoding="utf-8"?>
<rdf:RDF xml:base="http://www.gutenberg.org/"
  xmlns:pgterms="http://www.gutenberg.org/2009/pgterms/"
  xmlns:dcterms="http://purl.org/dc/terms/"
  xmlns:cc="http://web.resource.org/cc/"
  xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
  xmlns:dcam="http://purl.org/dc/dcam/"
  xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
>
"""

BOOK_22094 = """
<?xml version="1.0" encoding="utf-8"?>
<rdf:RDF xml:base="http://www.gutenberg.org/"
  xmlns:dcterms="http://purl.org/dc/terms/"
  xmlns:pgterms="http://www.gutenberg.org/2009/pgterms/"
  xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
  xmlns:cc="http://web.resource.org/cc/"
  xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
  xmlns:dcam="http://purl.org/dc/dcam/"
>
  <pgterms:ebook rdf:about="ebooks/22094">
    <dcterms:publisher>Project Gutenberg</dcterms:publisher>
    <dcterms:license rdf:resource="license"/>
    <dcterms:issued rdf:datatype="http://www.w3.org/2001/XMLSchema#date">2007-07-17</dcterms:issued>
    <dcterms:rights>Public domain in the USA.</dcterms:rights>
    <pgterms:downloads rdf:datatype="http://www.w3.org/2001/XMLSchema#integer">548</pgterms:downloads>
    <dcterms:creator>
      <pgterms:agent rdf:about="2009/agents/3485">
        <pgterms:name>Richardson, James</pgterms:name>
        <pgterms:birthdate rdf:datatype="http://www.w3.org/2001/XMLSchema#integer">1806</pgterms:birthdate>
        <pgterms:deathdate rdf:datatype="http://www.w3.org/2001/XMLSchema#integer">1851</pgterms:deathdate>
        <pgterms:webpage rdf:resource="https://en.wikipedia.org/wiki/James_Richardson_(explorer)"/>
      </pgterms:agent>
    </dcterms:creator>
    <pgterms:marc010>05003599</pgterms:marc010>
    <dcterms:title>Travels in the Great Desert of Sahara, in the Years of 1845 and 1846</dcterms:title>
    <pgterms:marc508>Produced by Carlo Traverso and the Online Distributed
Proofreading Team at http://www.pgdp.net

HTML revised by David Widger</pgterms:marc508>
    <pgterms:marc520>"Travels in the Great Desert of Sahara, in the Years of 1845 and 1846" by James Richardson is a historical account written in the mid-19th century. The narrative focuses on the author's adventurous journey over a nine-month period through the Sahara Desert, highlighting personal encounters with various tribes such as the Touaricks, as well as descriptions of significant locations like Ghat, Ghadames, and Mourzuk. The work also reflects Richardson's strong condemnation of the slave trade he observed during his travels.  The opening of the book introduces readers to Richardson's motivations and intentions for his journey, emphasizing his desire to understand the lives and cultures of Saharan tribes while aiming to raise awareness against the slave trade. He reflects on the challenges he faced from both the local populations and the harsh desert environment. The narrative begins with his initial plans, the skepticism expressed by acquaintances about his journey, and his adventurous spirit as he departs for Tripoli, setting the stage for the arduous and enlightening experiences that will unfold in the vast landscapes of the Sahara. (This is an automatically generated summary.)</pgterms:marc520>
    <pgterms:marc908>Reading ease score: 70.0 (7th grade). Fairly easy to read.</pgterms:marc908>
    <dcterms:language>
      <rdf:Description rdf:nodeID="N6f0db053bbae494e9b24a29ca5de8aa5">
        <rdf:value rdf:datatype="http://purl.org/dc/terms/RFC4646">en</rdf:value>
      </rdf:Description>
    </dcterms:language>
    <dcterms:subject>
      <rdf:Description rdf:nodeID="Nc069d5fc997845d58235efbbf7a3e910">
        <dcam:memberOf rdf:resource="http://purl.org/dc/terms/LCSH"/>
        <rdf:value>Sahara -- Description and travel</rdf:value>
      </rdf:Description>
    </dcterms:subject>
    <dcterms:subject>
      <rdf:Description rdf:nodeID="N4beb3236c9ba468ab2d1342ed15b902d">
        <dcam:memberOf rdf:resource="http://purl.org/dc/terms/LCC"/>
        <rdf:value>DT</rdf:value>
      </rdf:Description>
    </dcterms:subject>
    <dcterms:type>
      <rdf:Description rdf:nodeID="N8cc1e070610544348142b9a04fd1eb2c">
        <dcam:memberOf rdf:resource="http://purl.org/dc/terms/DCMIType"/>
        <rdf:value>Text</rdf:value>
      </rdf:Description>
    </dcterms:type>
    <pgterms:bookshelf>
      <rdf:Description rdf:nodeID="Nc51305f66a6e4f96a96145aa109fc8f5">
        <dcam:memberOf rdf:resource="2009/pgterms/Bookshelf"/>
        <rdf:value>Category: Travel Writing</rdf:value>
      </rdf:Description>
    </pgterms:bookshelf>
    <pgterms:bookshelf>
      <rdf:Description rdf:nodeID="Nb22e3f43adb8472c9044980ab874498b">
        <dcam:memberOf rdf:resource="2009/pgterms/Bookshelf"/>
        <rdf:value>Category: History - Other</rdf:value>
      </rdf:Description>
    </pgterms:bookshelf>
    <dcterms:hasFormat>
      <pgterms:file rdf:about="https://www.gutenberg.org/cache/epub/22094/pg22094.cover.medium.jpg">
        <dcterms:isFormatOf rdf:resource="ebooks/22094"/>
        <dcterms:extent rdf:datatype="http://www.w3.org/2001/XMLSchema#integer">24150</dcterms:extent>
        <dcterms:modified rdf:datatype="http://www.w3.org/2001/XMLSchema#dateTime">2025-08-09T08:52:44.806859</dcterms:modified>
        <dcterms:format>
          <rdf:Description rdf:nodeID="N215d928978494bfaa1a644386345a73f">
            <dcam:memberOf rdf:resource="http://purl.org/dc/terms/IMT"/>
            <rdf:value rdf:datatype="http://purl.org/dc/terms/IMT">image/jpeg</rdf:value>
          </rdf:Description>
        </dcterms:format>
      </pgterms:file>
    </dcterms:hasFormat>
  </pgterms:ebook>
  <cc:Work rdf:about="">
    <cc:license rdf:resource="https://creativecommons.org/publicdomain/zero/1.0/"/>
    <rdfs:comment>Archives containing the RDF files for *all* our books can be downloaded at
            https://www.gutenberg.org/wiki/Gutenberg:Feeds#The_Complete_Project_Gutenberg_Catalog</rdfs:comment>
  </cc:Work>
  <rdf:Description rdf:about="https://en.wikipedia.org/wiki/James_Richardson_(explorer)">
    <dcterms:description>en.wikipedia</dcterms:description>
  </rdf:Description>
</rdf:RDF>
"""  # noqa: E501


def test_rdf_parser():
    rdf = RdfParser(BOOK_22094, 22094)
    parsed = rdf.parse()
    assert parsed.gid == 22094
    assert parsed.birth_year == "1806"
    assert parsed.author_id == "3485"
    assert parsed.bookshelf == "Category: Travel Writing"
    assert parsed.cover_image == 1
    assert parsed.death_year == "1851"
    assert parsed.downloads == "548"
    assert parsed.first_name == "James"
    assert parsed.languages == ["en"]
    assert parsed.license == "Public domain in the USA."
    assert parsed.last_name == "Richardson"
    assert parsed.subtitle == ""
    assert (
        parsed.title
        == "Travels in the Great Desert of Sahara, in the Years of 1845 and 1846"
    )


def test_rdf_parser_minimal():
    rdf = RdfParser(
        f"""
  {RDF_HEADER}
  <pgterms:ebook rdf:about="ebooks/22094">
    <dcterms:rights>Public domain in the USA.</dcterms:rights>
    <pgterms:downloads>548</pgterms:downloads>
  </pgterms:ebook>
</rdf:RDF>
""",
        1234,
    )
    parsed = rdf.parse()
    assert parsed.gid == 1234
    assert parsed.author_id is None
    assert parsed.first_name is None
    assert parsed.last_name is None
    assert parsed.bookshelf is None
    assert parsed.cover_image == 0
    assert parsed.birth_year is None
    assert parsed.death_year is None
    assert parsed.bookshelf is None
    assert parsed.languages == []


def test_rdf_parser_multi_languages():
    rdf = RdfParser(
        f"""
  {RDF_HEADER}
  <pgterms:ebook rdf:about="ebooks/22094">
    <dcterms:rights>Public domain in the USA.</dcterms:rights>
    <pgterms:downloads>548</pgterms:downloads>
    <dcterms:language>
      <rdf:Description>
        <rdf:value rdf:datatype="http://purl.org/dc/terms/RFC4646">ko</rdf:value>
      </rdf:Description>
    </dcterms:language>
    <dcterms:language>
      <rdf:Description>
        <rdf:value rdf:datatype="http://purl.org/dc/terms/RFC4646">fr</rdf:value>
      </rdf:Description>
    </dcterms:language>
  </pgterms:ebook>
</rdf:RDF>
""",
        1234,
    )
    parsed = rdf.parse()
    assert parsed.languages == ["ko", "fr"]


@pytest.mark.parametrize(
    "cover_url, expected_cover",
    [
        pytest.param(
            "https://www.gutenberg.org/cache/epub/22094/pg22094.cover.medium.jpg",
            1,
            id="good",
        ),
        pytest.param(
            "https://www.gutenberg.org/cache/epub/22094/pg22094.cover.medium.png",
            0,
            id="bad_extension",
        ),
        pytest.param(
            "https://www.gutenberg.org/cache/epub/22094/pg1234.cover.medium.jpg",
            0,
            id="bad_pg_id",
        ),
        pytest.param(
            "https://www.gutenberg.org/cache/epub/12345/pg22094.cover.medium.jpg",
            0,
            id="bad_folder_id",
        ),
        pytest.param(
            "https://foo.org/cache/epub/22094/pg22094.cover.medium.jpg",
            1,
            id="good_mirror",
        ),
    ],
)
def test_rdf_parser_cover(cover_url: str, expected_cover: int):
    rdf = RdfParser(
        f"""
  {RDF_HEADER}
  <pgterms:ebook rdf:about="ebooks/22094">
    <dcterms:rights>Public domain in the USA.</dcterms:rights>
    <pgterms:downloads>548</pgterms:downloads>
    <dcterms:hasFormat>
      <pgterms:file rdf:about="{cover_url}">
        <dcterms:isFormatOf rdf:resource="ebooks/22094"/>
        <dcterms:extent rdf:datatype="http://www.w3.org/2001/XMLSchema#integer">24150</dcterms:extent>
        <dcterms:modified rdf:datatype="http://www.w3.org/2001/XMLSchema#dateTime">2025-08-09T08:52:44.806859</dcterms:modified>
        <dcterms:format>
          <rdf:Description rdf:nodeID="N215d928978494bfaa1a644386345a73f">
            <dcam:memberOf rdf:resource="http://purl.org/dc/terms/IMT"/>
            <rdf:value rdf:datatype="http://purl.org/dc/terms/IMT">image/jpeg</rdf:value>
          </rdf:Description>
        </dcterms:format>
      </pgterms:file>
    </dcterms:hasFormat>
  </pgterms:ebook>
</rdf:RDF>
""",
        22094,
    )
    parsed = rdf.parse()
    assert parsed.cover_image == expected_cover


def test_rdf_parser_title_subtitle():
    rdf = RdfParser(
        f"""
  {RDF_HEADER}
  <pgterms:ebook rdf:about="ebooks/22094">
    <dcterms:title>Travels in the Great Desert of Sahara, in the Years of 1845 and 1846&#xA;This is a subtitle&#xA;Under two lines</dcterms:title>
    <dcterms:rights>Public domain in the USA.</dcterms:rights>
    <pgterms:downloads>548</pgterms:downloads>
  </pgterms:ebook>
</rdf:RDF>
""",  # noqa: E501
        123,
    )
    parsed = rdf.parse()
    assert parsed.gid == 123
    assert parsed.subtitle == "This is a subtitle Under two lines"
    assert (
        parsed.title
        == "Travels in the Great Desert of Sahara, in the Years of 1845 and 1846"
    )


@pytest.mark.parametrize(
    "name, author_id, expected_first_name, expected_last_name",
    [
        pytest.param(
            "Sullivan, J. W. N. (John William Navin)",
            "58535",
            "J. W. N. (John William Navin)",
            "Sullivan",
            id="john_sullivan",
        ),
        pytest.param(
            "John, Joe, Nash",
            "12345",
            "Nash Joe",
            "John",
            id="nash_joe_john",
        ),
        pytest.param(
            "Bob",
            "4567",
            None,
            "Bob",
            id="bob",
        ),
    ],
)
def test_rdf_parser_author(name, author_id, expected_first_name, expected_last_name):
    rdf = RdfParser(
        f"""
    {RDF_HEADER}
    <dcterms:creator>
      <pgterms:agent rdf:about="2009/agents/{author_id}">
        <pgterms:name>{name}</pgterms:name>
        <pgterms:birthdate rdf:datatype="http://www.w3.org/2001/XMLSchema#integer">1886</pgterms:birthdate>
        <pgterms:deathdate rdf:datatype="http://www.w3.org/2001/XMLSchema#integer">1937</pgterms:deathdate>
        <pgterms:alias>Sullivan, John William Navin</pgterms:alias>
        <pgterms:webpage rdf:resource="https://en.wikipedia.org/wiki/J._W._N._Sullivan"/>
      </pgterms:agent>
    </dcterms:creator>
    <dcterms:rights>Public domain in the USA.</dcterms:rights>
    <pgterms:downloads>548</pgterms:downloads>
  </pgterms:ebook>
</rdf:RDF>
""",
        123,
    )
    parsed = rdf.parse()
    assert parsed.gid == 123
    assert parsed.first_name == expected_first_name
    assert parsed.last_name == expected_last_name
    assert parsed.author_id == author_id


def test_rdf_parser_title_missing_license():
    rdf = RdfParser(
        f"""
  {RDF_HEADER}
  <pgterms:ebook rdf:about="ebooks/22094">
    <dcterms:title>Travels in the Great Desert of Sahara, in the Years of 1845 and 1846</dcterms:title>
    <pgterms:downloads>548</pgterms:downloads>
  </pgterms:ebook>
</rdf:RDF>
""",  # noqa: E501
        123,
    )
    with pytest.raises(
        Exception, match="Impossible to find license tag in book 123 RD"
    ):
        rdf.parse()


def test_rdf_parser_title_missing_downloads():
    rdf = RdfParser(
        f"""
  {RDF_HEADER}
  <pgterms:ebook rdf:about="ebooks/22094">
    <dcterms:title>Travels in the Great Desert of Sahara, in the Years of 1845 and 1846</dcterms:title>
    <dcterms:rights>Public domain in the USA.</dcterms:rights>
  </pgterms:ebook>
</rdf:RDF>
""",  # noqa: E501
        123,
    )
    with pytest.raises(
        Exception, match="Impossible to find download tag in book 123 RD"
    ):
        rdf.parse()

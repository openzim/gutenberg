from bs4 import BeautifulSoup

def read_xml(name):
    data = ''
    with open('pg'+name+'.rdf', 'r') as f:
        data = f.read()
    
    soup = BeautifulSoup(data)
    
    # Basic identification
    book_id = name
    title = soup.find('dcterms:title').text
    subtitle = ' '.join(title.split('\n')[1:])
    title = title.split('\n')[0]
    
    # Author
    first_name = ''
    last_name = ''
    author = author = soup.find('dcterms:creator')
    if author == None:
        author = soup.find('marcrel:com')
    author = author.find('pgterms:name').text
    author_name = author.split(',')
    if author == 'Anonymous':
        print 'Anonymous author' # TODO
    elif author == 'Various':
        print 'Various author' # TODO
    elif len(author_name) == 2:
        first_name = author.split(',')[1]
        last_name = author.split(',')[0]
    birth_date = soup.find('pgterms:birthhdate')
    birth_date = birth_date.text if birth_date else None
    death_date = soup.find('pgterms:deathhdate')
    death_date = death_date.text if death_date else None
    
    # Other basic metadata
    language =  soup.find('dcterms:language').find('rdf:value').text
    downloads = soup.find('pgterms:downloads').text 
    license = soup.find('dcterms:rights').text
    
    print 'book id='+book_id
    print 'title='+title
    print 'subtitle='+subtitle
    print 'author='+author
    


read_xml('45213')


from bs4 import BeautifulSoup

data = ''
with open('pg45213.rdf', 'r') as f:
	data = f.read()

soup = BeautifulSoup(data)

title = soup.find('dcterms:title').text
subtitle = ''.join(title.split('\n')[1:])
author = soup.find('dcterms:creator').find('pgterms:name').text
first_name = author.split(',')[1]
last_name = author.split(',')[0]
license = soup.find('dcterms:rights').text
language =  soup.find('dcterms:language').find('rdf:value').text
downloads = soup.find('pgterms:downloads').text 
brith_date = soup.find('pgterms:birthhdate')
brith_date = brith_date.text if brith_date else None
death_date = soup.find('pgterms:deathhdate')
death_date = death_date.text if death_date else None


# Estudo de Caso Utilizando o OpenStreetMap

### Área do Mapa Selecionada
Moema, São Paulo, Brasil.

- [https://www.openstreetmap.org/relation/1706557#map=14/-23.5947/-46.6622](https://www.openstreetmap.org/relation/1706557#map=14/-23.5947/-46.6622)
- [Dados adiquiridos utilizando o MapZen](https://mapzen.com)

 Esse é o mapa do bairro no qual moro atualmente na cidade de São Paulo. Inicialmente tive a intenção de realizar a análise sobre toda a cidade, mas pela sua magnitude foi restringido ao bairro de Moema.

## Desafios Encontrados

### Estrutura dos dados para o database

Mesmo trabalhando com o MongoDb onde o schemma não é fixo, uma boa estrutura dos dados é importante para facilitar na análise de dados. Para o mapa do OpenStreetMaps grande parte das informações estão como atributos dentro das tags. Os principais atributos são o de `k` e `v` quando os mesmos existem dentro da tag `tag`. Assim foi utilizado o script abaixo para transformar os valores de `k` e `v` em um dicionário dentro da key `tag`. Assim sendo de fácil acesso para as análises posteriores.

```python
def custom_osm_reader(file_name):
    """Read OSM from OpenStreetMap
    Args:
        file_name: absolute path of osm file
    Returns:
        List of dictionaries containing data fom the tags
        'node', 'way' and 'relation'. The <tag> tag is stored as a dictionary
        containing the attributes 'k' as key and 'v' as value
    Raises:
    """
    tree = ET.parse(file_name)
    root = tree.getroot()
    data =[]
    
    for first_level in root:
        if first_level.tag in ['node', 'way', 'relation']:
            item_mask = {}
            item_mask['type'] = first_level.tag
            for attri in first_level.attrib:
                item_mask[attri] = first_level.attrib[attri]
            
            # capture n tags 'tag' attributes inside first tag
            tag_holder = {}
            for second_level in first_level:

                if all (key in second_level.attrib for key in ("k", "v")):
                    # inside tag we just desire the k (key) and v (value) attributes
                    tag_holder[second_level.attrib['k']] = second_level.attrib['v']
                
            item_mask['tag'] = tag_holder
            data.append(item_mask)
        
    return data
```

### Acentuação

Foram encontrados casos na variação da escrita devido a utilização ou não de acentuação. Assim foi utilizado a função `data_cleaning_names` para remover toda a acentuação das palavras utilizando o `unidecode` e criando uma nova característica para os dados contendo apenas a primeira palavra da tag `name`.

```python
def data_cleaning_names(data, minor_tag):
    """Removes diacritics and get first word
    Args:
        data: data from the function custom_osm_reader
        tag_minor: key values within 'tag' key dictionary
    Returns:
        Data with a included key in the 'tag' dictionary, maintaining the original minor_tag
        and a new named as minor_tag + '_clean'
    Raises:
    """
    new_tag = minor_tag + '_clean'
    regex = '^.+?(\s|$)'
    # pre compile regex for performance improvement
    re_compiled = re.compile(regex)
    
    for i, entry in enumerate(data):
        if 'tag' in entry:
            # data has no fixed schemma, verify if tag_minor exists first
            if minor_tag in entry['tag']:
                # unidecode finds the closest character without diacritics
                find_match = re_compiled.match(unidecode.unidecode(data[i]['tag'][minor_tag]))
                if find_match:
                    data[i]['tag'][new_tag] = find_match.group(0)

    return data
```

### Websites

Outro problema que foi encontrado é na forma que são imputados os URL dos websites. 
- Presença ou não do protocolo ("http" ou "https") 
- Presença ou não do "www"
- Capitalização do URL
- Presença de *path* ou não após o *domain name*

Assim foi criada a função `data_cleaning_website` para padronizar a representação das URL removendo o protocolo, a presença do "www" e quaisquer *path* após o *domain name*. Também visando a análise a função retorna apenas o *domain* do site (".com", ".com.br" etc) para avaliar quais são mais utilizados. 

```python
def data_cleaning_website(data):
    """Standardize websites URL, removes http, https, returns only root site up to first /
        and returns domain of site
    Args:
        data: data from the function custom_osm_reader
    Returns:
        Data with new key called "website_clean" and "website_domain"
    Raises:
    """
    regex_clean = r'[a-z0-9\-.]+\.[a-z]{2,3}'
    regex_domain = r'(\.[a-z]{2,3}){1,2}(\.[a-z]{2,3})?$'
    # pre compile regex for performance improvement
    re_clean_compiled = re.compile(regex_clean)
    re_doamin_compiled = re.compile(regex_domain)
    
    for i, entry in enumerate(data):
        if 'tag' in entry:
            if 'website' in entry['tag']:
                # makes all lowercase
                website_clean = data[i]['tag']['website'].lower()
                # removes http:// and https://
                if website_clean[:7] == 'http://':
                    website_clean = website_clean[7:] 
                if website_clean[:8] == 'https://':
                    website_clean = website_clean[8:]
                
                find_match = re_clean_compiled.match(website_clean)
                if find_match:
                    website_clean = find_match.group(0)
                
                # removes www.
                if website_clean[0:4] == 'www.':
                    website_clean = website_clean[4:]
                    
                data[i]['tag']['website_clean'] = website_clean
                
                # gather domain of site
                find_match = re_doamin_compiled.search(website_clean)
                if find_match:
                    data[i]['tag']['website_domain'] = find_match.group(0)
                
    return data
```

Todo o código utilizado no projeto está disponível no [github](https://github.com/ChristianNogueira/udacity_data_wrangling/blob/master/final_project.py).

## Visão Geral dos Dados

### Tamanho dos Arquivos

```
sao-paulo_moema.osm.bz2 7,0MB
sao-paulo_moema.osm     125MB
sao-paulo_moema.json    132MB
sao-paulo_moema (mongo) 145MB
```  
```javascript
> db.sao_paulo_moema.stats()['size']
144915425
```
### Quantidade total de registros

```javascript
> db.sao_paulo_moema.find().count()
644817
```

### Quantidade total de tags

Quantidade total independente da hierarquia
```python
def count_tags(file_name):
    tags = {} #empty dict to hold key, count
    for event, elem in ET.iterparse(file_name):
        if elem.tag in tags:
            tags[elem.tag] += 1
        else:
            tags[elem.tag] = 1
    
    print('tag : count')
    for key in tags:
        print(key, ':', tags[key])

my_file = 'sao-paulo_moema.osm'
count_tags(my_file)
```
```
tag : count
bounds : 1
node : 568270
tag : 228359
nd : 795473
way : 75092
member : 7243
relation : 1455
osm : 1
```

### Quantidade de usuários únicos

Podemos verificar a quantidade de usuários que contribuíram nessa região observando a quantidade de `user`, porém não sabemos se o sistema do OpenStreetMap permite ou não que mais de um usuários utilize o mesmo user name. Por garantia também vamos verificar a quantidade de `uid` que são os users id de cada modificação.
```javascript
> db.sao_paulo_moema.distinct('user').length
277
> db.sao_paulo_moema.distinct('uid').length
277
```
Podemos observar que para o local utilizado não existem usuários compartilhando o mesmo user name. Porém isso não nos garante que os usuários tenham que possuir user names únicos.

### Top 10 usuários com mais contribuições realizadas

Esses usuários foram responsáveis por 99% das contribuições da área.
```javascript
> db.sao_paulo_moema.aggregate([{"$group" : {"_id" : "$user", "count" : {"$sum" : 1}}},{"$sort" : {"count" : -1}}, {"$limit" : 10}])
{ "_id" : "Bonix-Mapper", "count" : 485833 }
{ "_id" : "Bonix-Importer", "count" : 144466 }
{ "_id" : "MCPicoli", "count" : 2124 }
{ "_id" : "111111111111111111111111111", "count" : 2066 }
{ "_id" : "Geogast", "count" : 1327 }
{ "_id" : "Ori952", "count" : 939 }
{ "_id" : "Samuka", "count" : 891 }
{ "_id" : "O Fim", "count" : 869 }
{ "_id" : "AjBelnuovo", "count" : 555 }
{ "_id" : "naoliv", "count" : 441 }
```

### Total de usuários com apenas uma contribuição

Dos 277 usuários com contribuições 34% fizeram apenas uma única contribuição para a área.
```javascript
> db.sao_paulo_moema.aggregate([{"$group" : {"_id" : "$user", "count" : {"$sum" : 1}}},{"$match" : {"count": 1}}, {"$group" : {"_id" : "count", "total" : {"$sum" : 1}}}])
{ "_id" : "count", "total" : 95 }
```

### Quantidade de `node`, `way` e `relation`

```javascript
> db.sao_paulo_moema.aggregate([{"$group" : {"_id" : "$type", "count" : {"$sum" : 1}}}])
{ "_id" : "relation", "count" : 1455 }
{ "_id" : "way", "count" : 75092 }
{ "_id" : "node", "count" : 568270 }
```

### Observação sobre os *Domain* utilizado

Como esperado o *domain* mais utilizado é o ".com.br" com uma representatividade de 78% dos sites cadastrados.
```javascript
> db.sao_paulo_moema.aggregate([{"$match" : {"tag.website_domain" : {"$exists" : 1}}}, {"$group" : {"_id" : "$tag.website_domain", "count" : {"$sum" : 1}}}])
{ "_id" : ".sp.gov.br", "count" : 5 }
{ "_id" : ".com", "count" : 9 }
{ "_id" : ".oep.org.bo", "count" : 1 }
{ "_id" : ".com.br", "count" : 103 }
{ "_id" : ".org.br", "count" : 7 }
{ "_id" : ".gov.br", "count" : 1 }
{ "_id" : ".org", "count" : 3 }
{ "_id" : ".br", "count" : 2 }
```

O interessante é observar o ".oep.org.bo" que é um domain incomum, procurando por esse registro podemos observar que é referente ao consulado Boliviano.

```javascript
> db.sao_paulo_moema.find({"tag.website_domain" : ".oep.org.bo"}, {"_id" : 0, "tag" : 1}).pretty()
{
        "tag" : {
                "name" : "Oficina de empadronamiento electoral de Bolivia en el exterior",
                "website" : "http://yoparticipo.oep.org.bo/",
                "addr:city" : "São Paulo",
                "addr:street" : "Rua Coronel Artur Godoi",
                "addr:housenumber" : "7",
                "website_clean" : "yoparticipo.oep.org.bo",
                "website_domain" : ".oep.org.bo",
                "name_clean" : "Oficina "
        }
}
```

### Tipos de locais com mais ocorrências (`amenity`) 

Algo surpreendente é a quantidade de estacionamentos.
```javascript
> db.sao_paulo_moema.aggregate([{"$match" : {"tag.amenity" : {"$exists" : 1}}}, {"$group" : {"_id" : "$tag.amenity", "count" : {"$sum" : 1}}}, {"$sort" : {"count" : -1}}, {"$limit" : 10}])
{ "_id" : "parking", "count" : 766 }
{ "_id" : "restaurant", "count" : 151 }
{ "_id" : "fuel", "count" : 102 }
{ "_id" : "bank", "count" : 83 }
{ "_id" : "bicycle_rental", "count" : 67 }
{ "_id" : "fast_food", "count" : 49 }
{ "_id" : "pharmacy", "count" : 41 }
{ "_id" : "school", "count" : 39 }
{ "_id" : "cafe", "count" : 37 }
{ "_id" : "hospital", "count" : 23 }
```

### Abertura dos Estacionamentos (*parking*) por tipo de acesso

Abrindo por tipo de acesso podemos verificar que em sua maioria 93% são estacionamentos privados se referenciando aos estacionamentos dos prédios da região.
```javascript
> db.sao_paulo_moema.aggregate([{"$match" : {"tag.amenity" : "parking"}}, {"$group" : {"_id" : "$tag.access", "count" : {"$sum" : 1}}}, {"$sort" : {"count" : -1}}])
{ "_id" : "private", "count" : 714 }
{ "_id" : null, "count" : 34 }
{ "_id" : "customers", "count" : 15 }
{ "_id" : "permissive", "count" : 2 }
{ "_id" : "yes", "count" : 1 }

> db.sao_paulo_moema.find({"tag.amenity" : "parking", "tag.access" : "private", "tag.building" : "yes"}).count()
708
```

### Analise de onde tomar um café

Sempre é bom saber onde é possível tomar um café.
```javascript
> db.sao_paulo_moema.distinct('tag.name', {'tag.amenity' : 'cafe', 'tag.name' : {'$exists' : 1}}, {'_id' : 0, 'tag.name' : 1})
[
    "Kopenhagen",
    "Lanchonete Flor Do Paraíso",
    "Lanchonette Praça du Paz",
    "Fran's Cafe",
    "Fredisimo",
    "Frans Café",
    "Estação do Café",
    "Confeitaria Monte Líbano",
    "Quinto Pecado",
    "Les Café",
    "Starbucks",
    "Borges Café",
    "Gold Stone",
    "Jamie's Italian",
    "Vanilla Café",
    "Casa do Pão de Queijo",
    "Luz da Villa",
    "Confeitaria Christina",
    "Clemente Café",
    "La Guapa",
    "Cheesecakeria",
    "Delta Expresso",
    "Bossa Nova",
    "Dolcissimo",
    "Original American Cofee Cake",
    "Café e restaurante",
    "M Café"
]
```
Apenas 8 dos 32 cafés possuem o horário de atendimento cadastrado.
```javascript
> db.sao_paulo_moema.find({'tag.amenity' : 'cafe', 'tag.name' : {'$exists' : 1}}).count()
32
> db.sao_paulo_moema.find({'tag.amenity' : 'cafe', 'tag.name' : {'$exists' : 1}, 'tag.opening_hours' : {'$exists' : 1}}).count()
8
```
## Ideias Adicionais e Melhorias

Pode se observar a concentração das contribuições em poucos usuários, isso pode estar relacionado ao extenso processo para se contribuir com detalhamento seguindo toda a documentação. Poderia se explorar integrações com API de serviços como o Twitter para aumentar a participação dos usuários. 
Esse serviço por outro lado tem de ser desenvolvido necessitaria de uma grande aplicação de machine learning para não acabar realizando os inputs de forma a piorar a qualidade da informação coletada.

## Conclusão

A região possui uma grande quantidade dados como ruas, localidades e áreas, porém o OpenStreetMaps ainda necessita de um maior detalhamento das informações desses dados, como visto na análise das cafeterias. Esses detalhes são cada vez o que chama a atenção do publico para a utilização das plataformas de mapas, que cada vez estão se integrando com outros serviços para atingir o detalhamento desejado.
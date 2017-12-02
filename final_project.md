# Estudo de Caso Utilizando o OpenStreetMap

### Área do Mapa Selecionada
Moema, São Paulo, Brasil

- [https://www.openstreetmap.org/relation/1706557#map=14/-23.5947/-46.6622](https://www.openstreetmap.org/relation/1706557#map=14/-23.5947/-46.6622)
- [Dados adiquiridos utilizando o MapZen](https://mapzen.com)

 Esse é o mapa do bairro no qual moro atualmente na cidade de São Paulo. Inicialmente tive a intenção de realizar a análise sobre toda a cidade, mas pela sua magnitude foi restringido ao bairro de Moema.

## Desafios Encontrados

### Acentuação

Foram encontrados casos na variação da escrita devido a utilização ou não de acentuação. Assim foi utilizado a função para remover toda a acentuação das palavras utilizando o `unidecode` e criando uma nova característica para os dados contendo apenas a primeira palavra da tag `name`.

```python
def data_cleaning(data, minor_tag):
    
    new_tag = minor_tag + '_clean'
    regex = '^.+?(\s|$)'
    # pre compile regex for performance improvment
    re_compiled = re.compile(regex)
    
    for i, entry in enumerate(data):
        if 'tag' in entry:
            if minor_tag in entry['tag']:
                find_match = re_compiled.match(unidecode.unidecode(data[i]['tag'][minor_tag]))
                if find_match:
                    data[i]['tag'][new_tag] = find_match.group(0)
                    
    return data
    
data_cleaned = data_cleaning(data, 'name')
```

Todo o código utilizado no projeto está disponível no [github](https://github.com/ChristianNogueira/udacity_data_wrangling/blob/master/final_project.py)

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

### Quantidade total de Tags
Quantidade total independente da hierarquia
```python
import xml.etree.ElementTree as ET

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
```javascript
> db.sao_paulo_moema.aggregate([{"$group": {"_id": "$user", "count": {"$sum":1}}},{"$sort": {"count": -1}}, {"$limit":10}])
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
Dos 277 usuários com contribuições 34% fizeram apenas uma única contribuição para a área
```javascript
> db.sao_paulo_moema.aggregate([{"$group": {"_id": "$user", "count": {"$sum":1}}},{"$match": {"count": 1}}, {"$group" : {"_id": "count", "total" : {"$sum":1}}}])
{ "_id" : "count", "total" : 95 }
```

### Quantidade de `node`, `way` e `relation`
```javascript
> db.sao_paulo_moema.aggregate([{"$group": {"_id": "$type", "count": {"$sum":1}}}])
{ "_id" : "relation", "count" : 1455 }
{ "_id" : "way", "count" : 75092 }
{ "_id" : "node", "count" : 568270 }
```

### Tipos de locais com mais ocorrências (`amenity`) 
```javascript
> db.sao_paulo_moema.aggregate([{"$match" : {"tag.amenity" : {"$exists" : 1}}}, {"$group" : {"_id":"$tag.amenity", "count" : {"$sum":1}}}, {"$sort" : {"count" : -1}}, {"$limit":10}])
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

Sempre é bom saber one é possível tomar um café
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

Apenas 8 dos 32 cafés possuem o horário de atendimento cadastrado 
```javascript
> db.sao_paulo_moema.find({'tag.amenity' : 'cafe', 'tag.name' : {'$exists' : 1}}).count()
32
> db.sao_paulo_moema.find({'tag.amenity' : 'cafe', 'tag.name' : {'$exists' : 1}, 'tag.opening_hours' : {'$exists' : 1}}).count()
8
```
## Idéias Adicionais e Melhorias

## Conclusão

A região possui uma grande quantidade de dados, porém o OpenStreetMaps ainda necessita de um maior detalhamento maior da informação dos locais.
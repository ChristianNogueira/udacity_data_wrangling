# Estudo de Caso Utilizando o OpenStreetMap

### Área do Mapa Selecionada
Moema, São Paulo, Brasil

- [https://www.openstreetmap.org/relation/1706557#map=14/-23.5947/-46.6622](https://www.openstreetmap.org/relation/1706557#map=14/-23.5947/-46.6622)
- [Dados adiquiridos utilizando o MapZen](https://mapzen.com)

 Esse é o mapa do bairro que vivo atualmente na cidade de São Paulo. Inicialmente tive a intenção de realizar a análise sobre toda a cidade, mas pela sua magnitude foi restringido ao bairro de Moema.

## Desafios Encontrados

## Visão Geral dos Dados

### Tamanho dos Arquivos
```
sao-paulo_moema.osm.bz2 7,0MB
sao-paulo_moema.osm     125MB
```  

### Quantidade de Tags
```python
def count_tags(file_name):
    tags = {}
    for event, elem in ET.iterparse(file_name):
        if elem.tag in tags:
            tags[elem.tag] += 1
        else:
            tags[elem.tag] = 1
    
    print('tag : count')
    for key in tags:
        print(key, ':', tags[key])
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
### Quantidade de nós (node) e caminhos (ways)
### Quantidade de tipo de nós escolhidos, como cafés, lojas etc.

## Idéias Adicionais e Melhorias

## Análises Adicionais

## Conclusão

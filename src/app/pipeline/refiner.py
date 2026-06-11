
# hilfsfunktion um alle entities und triples in lowercase umzuwandeln
def data_to_lowercase(data):
    # step 1: alle entities  klein schreiben
    entity_list = data["entities"]
    for index, entity in enumerate(entity_list):
        entity_list[index]=entity.lower()
    # step 2: triple klein schreiben
    triple_list = data["triples"]
    for index, triple in enumerate(triple_list):
        triple_list[index]["subject"]=triple["subject"].lower()
        triple_list[index]["predicate"]=triple["predicate"].lower()
        triple_list[index]["object"]=triple["object"].lower()

    return data
#hilfsfunktion um liste von dicts zu liste von triples zu convertieren
def convert_dics_to_tuples(triples_dics):
    triples_list = []
    for elem in triples_dics:
        t_values = (elem["subject"], elem["predicate"], elem["object"])
        triples_list.append(t_values)
    return triples_list

def convert_tuples_to_dicts(triples_tuples):
    triples_dics = []
    for elem in triples_tuples:
        t_dict = {"subject": elem[0], "predicate": elem[1], "object": elem[2]}
        triples_dics.append(t_dict)
    return triples_dics
#hilfsfunktion um exakte duplikate in entities, triples und relationen zu entfernen und addded die relationen in das dict
def rm_exact_duplicates(data, relations):
    entities = data["entities"]
    triples = data["triples"]
    # step 3: exakte Duplikate in entities entfernen
    data["entities"] = list(dict.fromkeys(entities))
    # step 4: exakte Duplikate in triples entfernen
    #hier mit cbv und cbf aufpassen
    triples_tuples = convert_dics_to_tuples(triples)
    triples_tuples = list(dict.fromkeys(triples_tuples))
    data["triples"] = convert_tuples_to_dicts(triples_tuples)
    #i want to remov exact duplicates in relation and fuse triples, entities and relaiton into a new dict
    # step 5: exakte Duplikate in relation entfernen
    relations = list(dict.fromkeys(relations))
    data["relations"] = relations
    return data

#hilfsfunktion um reltionen aus den tirple dicts zu extrahieren
def extract_relations(data):
    triples = data["triples"]
    relations = []
    for triple in triples:
        relations.append(triple["predicate"])
    return relations


# Hauptfunktion um die Daten zu refinen
def refine_data(data):

    if not isinstance(data, dict):
        raise ValueError("Input data must be a dictionary.")
    data_lowercase = data_to_lowercase(data)
    # extrahiere die ralationen in eine Liste von Tupeln
    relations = extract_relations(data_lowercase)

    # remove exact duplicates in entities, triples and relations
    dedup_data = rm_exact_duplicates(data_lowercase, relations)
    # bring data in a vector representation for further processing


    return dedup_data
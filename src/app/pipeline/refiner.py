import copy
from app.pipeline.retrieval import prepare_bm25, get_top_k_elements, vectorise_data,model
from app.pipeline.llm_dedup import send_llm_candidates


##############Preprcessing#######################
# hilfsfunktion um alle entities und triples in lowercase umzuwandeln
def data_to_lowercase(data):
    # alle entities  klein schreiben
    entity_list = data["entities"]
    for entity in entity_list:
        entity["name"]=entity["name"].lower()
    # triple klein schreiben
    triple_list = data["triples"]
    for triple in triple_list:
        triple["subject"]["name"]=triple["subject"]["name"].lower()
        triple["predicate"]=triple["predicate"].lower()
        triple["object"]["name"]=triple["object"]["name"].lower()
    # relation klein schreiben 
    for index, relation in enumerate(data["relations"]):
        data["relations"][index]=relation.lower()

    return data

#hilfsfunktion um exakte duplikate in entities, triples und relationen zu entfernen und addded die relationen in das dict
def rm_exact_duplicates(data):
    entities = data["entities"]
    triples = data["triples"]
    relations = data["relations"]
    # step 3: exakte Duplikate in entities entfernen
    data["entities"] =dedup_entities(entities) 
    # step 4: exakte Duplikate in triples entfernen
    #hier mit cbv und cbf aufpassen
    triples_tuples = convert_dicts_to_tuples(triples)
    triples_tuples =dedup_list(triples_tuples) 
    data["triples"] = convert_tuples_to_dicts(triples_tuples)
    # step 5: exakte Duplikate in relation entfernen
    relations = dedup_list(relations)
    data["relations"] = relations
    return data



################convertion utils#####################
#hilfsfunktion um liste von dicts zu liste von triples zu konvertieren
def convert_dicts_to_tuples(triples_dicts):
    triples_list = []
    for elem in triples_dicts:
        t_values = ((elem["subject"]["name"], elem["subject"]["type"]), elem["predicate"], (elem["object"]["name"], elem["object"]["type"]))
        triples_list.append(t_values)
    return triples_list
#hilfsfunktion um liste von triples zu liste von dicts zu konvertieren
def convert_tuples_to_dicts(triples_tuples):
    triples_dicts = []
    for elem in triples_tuples:
        t_dict = {"subject": {"name": elem[0][0], "type": elem[0][1]}, "predicate": elem[1], "object": {"name": elem[2][0], "type": elem[2][1]}}
        triples_dicts.append(t_dict)
    return triples_dicts

##############orchestration#######################

# Hauptfunktion um die Daten zu refinen
def refine_data(data, input_text):

    if not isinstance(data, dict):
        raise ValueError("Input data must be a dictionary.")
    data_lowercase = data_to_lowercase(data)

    # entfernt exakte Duplikate
    dedup_data = rm_exact_duplicates(data_lowercase)
    
    entity_mapping, relation_mapping = process_retrieval(dedup_data, input_text)
    dedup_data= apply_mapping(dedup_data, entity_mapping, relation_mapping)

    return dedup_data, entity_mapping, relation_mapping

##########retrieval loop#######################
#goal main loop: arbeite durch die work list und rufe die top k elemente ab, die dann and die LLM geschickt werden um die deduplikation mapping zu generieren.
def refine_loop(vectorised_items,bm25_items,work_list_items,item_reference,input_text):
    llm_mappings = {}
   #haupt loop um die arbeitsliste durchzuarbeiten 
    while len(work_list_items) > 0:
        #setup fuer das query item
        query_item = work_list_items.pop(0)
        query_name = query_item
        query_item_embedding = model.encode(query_name)
        #hol die tip k indizes
        top_k_item_indices = get_top_k_elements(vectorised_items, bm25_items, query_name, query_item_embedding, k=17)
        top_k_items = []
        #hol die namen der items
        for item in top_k_item_indices:
            if item_reference[item] == query_item:
                continue
            top_k_items.append(item_reference[item])
        #send die candidaten and die llm
        result=send_llm_candidates(query_item, top_k_items,input_text,True)
        # remove duplicates from work list
        for item in result:
            for i, work_item in enumerate(work_list_items):
                if item == work_item:
                    work_list_items.pop(i)
                    break
        llm_mappings[query_item] = result
    return llm_mappings

def refine_entities_loop(vectorised_entities, bm25_entities, work_list_entities, entities_list, input_text):
    work_list_tuples = []
    for entity in work_list_entities:
        work_list_tuples.append((entity["name"], entity["type"]))

    llm_mappings = {}
    #haupt loop um die arbeitsliste durchzuarbeiten
    while len(work_list_tuples) > 0:
        #setup fuer das query item
        query_entity_tuple = work_list_tuples.pop(0)
        query_entity = {"name": query_entity_tuple[0], "type": query_entity_tuple[1]}
        query_string = f"{query_entity_tuple[0]} ({query_entity_tuple[1]})"
        query_entity_embedding = model.encode(query_string)
        #hol die top k indizes
        top_k_entity_indices = get_top_k_elements(
            vectorised_entities, bm25_entities, query_string,
            query_entity_embedding, k=17
        )
        #hol die namen der indizes
        top_k_entities = []
        for item in top_k_entity_indices:
            if entities_list[item] == query_entity:
                continue
            top_k_entities.append(entities_list[item])
        #send die kandidaten and die llm
        result = send_llm_candidates(query_entity, top_k_entities, input_text, False)

        for item in result:
            for i, work_item in enumerate(work_list_tuples):
                if item == work_item:
                    work_list_tuples.pop(i)
                    break

        llm_mappings[(query_entity["name"], query_entity["type"])] = result
    return llm_mappings

#hauptfunktion retrieval
def process_retrieval(data, input_text):

    entities = data["entities"]

    entity_names = []
    for entity in entities:
        entity_names.append(f"{entity['name']} ({entity['type']})")

    relations = data["relations"]
    #wenn keine entities oder relationen vorhanden sind, raise error,
    if len(entities) == 0 or len(relations) == 0:
        raise ValueError("No entities or relations to refine.")
    #embeddings 
    vectorised_entities, vectorised_relations = vectorise_data(entity_names, relations)
    #bm objects
    bm25_entities = prepare_bm25(entity_names)
    bm25_relations = prepare_bm25(relations)
    #deep copies fuer main loop
    work_list_entities = copy.copy(entities)
    work_list_relations = copy.copy(relations)
    #ruf main loop fuer entities
    entity_mappings = refine_entities_loop(vectorised_entities, bm25_entities, work_list_entities, entities, input_text)
    relation_mappings = refine_loop(vectorised_relations, bm25_relations, work_list_relations, relations, input_text)

    return [entity_mappings, relation_mappings]

###########andere utils#####################
#hilfsfunktion um 2 dicts zu vegleichten
def compare_dicts(dict1, dict2):
    if dict1["name"] == dict2["name"] and dict1["type"] == dict2["type"]:
        return True
    return False
#hilfsfunktion um einer liste von exakten duplikaten zu entfernen.
def dedup_entities(entities):
    new_entities = []
    seen = set()

    for  entity in entities:
                if (entity["name"], entity["type"]) not in seen:
                    seen.add((entity["name"], entity["type"]))
                    new_entities.append(entity)
    return new_entities 



def dedup_list(items):
    return list(dict.fromkeys(items))

#hilfsfunktion um eine mapping dict zu generieren, die die duplikate auf das originale item mapped
def gen_reverse_mapping(mapping):
    reverse_mapping = {}
    for key, value in mapping.items():
        for e in value:
            reverse_mapping[e]= key
    return reverse_mapping
#todo rewrite the funciton so that dicts work
#entity mapping: (name,type) -> (name,type)
#hilfsfunktion um die mappings auf die Graphen anzuwenden
def apply_mapping(data,entity_mapping,relation_mapping):
    
    #ansatz though a reverse mapping
    entity_r_mapping = gen_reverse_mapping(entity_mapping)
    relation_r_mapping = gen_reverse_mapping(relation_mapping)
    #ersetz die duplikates in entities
    for index, data_entity in enumerate(data["entities"]):
        enity_key = (data_entity["name"], data_entity["type"])
        if enity_key in entity_r_mapping:
           res=entity_r_mapping[enity_key] 
           data["entities"][index] = {"name": res[0], "type": res[1]} 
    
    
    #ersetz die duplikates in relationen
    #for index, data_relation in enumerate(data["relations"]):
    #    if data_relation in relation_r_mapping:
    #        data["relations"][index] = relation_r_mapping[data_relation]

    #ersetz die duplikates in triples
    for index, triple in enumerate(data["triples"]):
        subject = (triple["subject"]["name"], triple["subject"]["type"])
        t_object_ = (triple["object"]["name"], triple["object"]["type"])
        if subject in entity_r_mapping:
            data["triples"][index]["subject"] = {"name": entity_r_mapping[subject][0], "type": entity_r_mapping[subject][1]}
        if t_object_ in entity_r_mapping:
            data["triples"][index]["object"] = {"name": entity_r_mapping[t_object_][0], "type": entity_r_mapping[t_object_][1]}
        if triple["predicate"] in relation_r_mapping:
            data["triples"][index]["predicate"] = relation_r_mapping[triple["predicate"]]

    #dedupliziert die neuen triples die durch die ersetzungen entstanden sind
    #tripel
    triples_tuples = convert_dicts_to_tuples(data["triples"])
    triples_tuples = dedup_list(triples_tuples)
    data["triples"] = convert_tuples_to_dicts(triples_tuples)
    #entities
    data["entities"] = dedup_entities(data["entities"])
    #relationen
    data["relations"] = dedup_list(data["relations"])

    return data



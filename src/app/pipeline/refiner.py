import copy
from app.pipeline.retrieval import prepare_bm25, get_top_k_elements, vectorise_data,model
from app.pipeline.llm_dedup import send_llm_candidates


##############Preprcessing#######################
# hilfsfunktion um alle entities und triples in lowercase umzuwandeln
def data_to_lowercase(data):
    # step 1: alle entities  klein schreiben
    entity_list = data["entities"]
    for index, entity in enumerate(entity_list):
        entity_list[index]=entity.lower()
    # step 2: triple klein schreiben
    triple_list = data["triples"]
    for triple in triple_list:
        triple["subject"]=triple["subject"].lower()
        triple["predicate"]=triple["predicate"].lower()
        triple["object"]=triple["object"].lower()

    return data

#hilfsfunktion um exakte duplikate in entities, triples und relationen zu entfernen und addded die relationen in das dict
def rm_exact_duplicates(data):
    entities = data["entities"]
    triples = data["triples"]
    relations = data["relations"]
    # step 3: exakte Duplikate in entities entfernen
    data["entities"] =dedup_list(entities) 
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
        t_values = (elem["subject"], elem["predicate"], elem["object"])
        triples_list.append(t_values)
    return triples_list
#hilfsfunktion um liste von triples zu liste von dicts zu konvertieren
def convert_tuples_to_dicts(triples_tuples):
    triples_dicts = []
    for elem in triples_tuples:
        t_dict = {"subject": elem[0], "predicate": elem[1], "object": elem[2]}
        triples_dicts.append(t_dict)
    return triples_dicts

##############orchestration#######################

# Hauptfunktion um die Daten zu refinen
def refine_data(data):

    if not isinstance(data, dict):
        raise ValueError("Input data must be a dictionary.")
    data_lowercase = data_to_lowercase(data)

    # entfernt exekte Duplikate
    dedup_data = rm_exact_duplicates(data_lowercase)
    
    entity_mapping, relation_mapping = process_retrieval(dedup_data)
    dedup_data= apply_mapping(dedup_data, entity_mapping, relation_mapping)

    return dedup_data, entity_mapping, relation_mapping

##########retrieval loop#######################
#goal main loop: arbeite durch die work list und rufe die top k elemente ab, die dann and die LLM geschickt werden um die deduplikation mapping zu generieren.
def refine_loop(vectorised_items,bm25_items,work_list_items,item_reference):
    llm_mappings = {} 
   #haupt loop um die arbeitsliste durchzuarbeiten 
    while len(work_list_items) > 0:
        #setup fuer das query item
        query_item = work_list_items.pop(0)
        query_item_embedding = model.encode(query_item)
        #hol die tip k indizes
        top_k_item_indices = get_top_k_elements(vectorised_items, bm25_items, query_item, query_item_embedding, k=17)
        top_k_items = [] 
        #hol die namen der items
        for item in top_k_item_indices:
            if item_reference[item] == query_item:
                continue
            top_k_items.append(item_reference[item]) 
        #send die candidaten and die llm
        result=send_llm_candidates(query_item, top_k_items)
        # TODOneed to remove the duplicate form the work list items so that the while loops works
        for duplicate in result:
            if duplicate in work_list_items:
                work_list_items.remove(duplicate)
        llm_mappings[query_item] = result
    return llm_mappings

#hauptfunktion retrieval
def process_retrieval(data):

    entities = data["entities"]
    relations = data["relations"]
    #wenn keine entities oder relationen vorhanden sind, raise error,
    if len(entities) == 0 and len(relations) == 0:
        raise ValueError("No entities or relations to refine.")
    #embeddings 
    vectorised_entities, vectorised_relations = vectorise_data(data)
    #bm objects
    bm25_entities = prepare_bm25(entities)
    bm25_relations = prepare_bm25(relations)
    #deep copies fuer main loop
    work_list_entities = copy.copy(entities)
    work_list_relations = copy.copy(relations)
    #ruf main loop fuer entities
    entity_mappings = refine_loop(vectorised_entities, bm25_entities, work_list_entities,entities)
    relation_mappings = refine_loop(vectorised_relations, bm25_relations, work_list_relations,relations)

    return [entity_mappings, relation_mappings]

###########andere utils#####################

#hilfsfunktion um einer liste von exakten duplikaten zu entfernen.
def dedup_list(items):
    return list(dict.fromkeys(items))

#hilfsfunktion um eine mapping dict zu generieren, die die duplikate auf das originale item mapped
def gen_reverse_mapping(mapping):
    reverse_mapping = {}
    for key, value in mapping.items():
        for e in value:
            reverse_mapping[e]= key
    return reverse_mapping

#hilfsfunktion um die mappings auf die Graphen anzuwenden
def apply_mapping(data,entity_mapping,relation_mapping):
    
    #ansatz though a reverse mapping
    entity_r_mapping = gen_reverse_mapping(entity_mapping)
    relation_r_mapping = gen_reverse_mapping(relation_mapping)
    #ersetz die duplikates in entities
    for index, data_entity in enumerate(data["entities"]):
        if data_entity in entity_r_mapping:
            data["entities"][index] = entity_r_mapping[data_entity]
    #ersetz die duplikates in relationen
    for index, data_relation in enumerate(data["relations"]):
        if data_relation in relation_r_mapping:
            data["relations"][index] = relation_r_mapping[data_relation]
    #ersetz die duplikates in triples
    for index, triple in enumerate(data["triples"]):
        if triple["subject"] in entity_r_mapping:
            data["triples"][index]["subject"] = entity_r_mapping[triple["subject"]]

        if triple["predicate"] in relation_r_mapping:
            data["triples"][index]["predicate"] = relation_r_mapping[triple["predicate"]]

        if triple["object"] in entity_r_mapping:
            data["triples"][index]["object"] = entity_r_mapping[triple["object"]]
    #dedupliziert die neuen triples die durch die ersetzungen entstanden sind
    #tripel
    triples_tuples = convert_dicts_to_tuples(data["triples"])
    triples_tuples = dedup_list(triples_tuples)
    data["triples"] = convert_tuples_to_dicts(triples_tuples)
    #entities
    data["entities"] = dedup_list(data["entities"])
    #relationen
    data["relations"] = dedup_list(data["relations"])

    return data



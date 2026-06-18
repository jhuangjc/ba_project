import copy
from app.pipeline.retrieval import prepare_bm25, get_top_k_elements, vectorise_data,model
from app.pipeline.llm_dedup import send_llm_candidates
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
def convert_dicts_to_tuples(triples_dicts):
    triples_list = []
    for elem in triples_dicts:
        t_values = (elem["subject"], elem["predicate"], elem["object"])
        triples_list.append(t_values)
    return triples_list

def convert_tuples_to_dicts(triples_tuples):
    triples_dicts = []
    for elem in triples_tuples:
        t_dict = {"subject": elem[0], "predicate": elem[1], "object": elem[2]}
        triples_dicts.append(t_dict)
    return triples_dicts
#hilfsfunktion um exakte duplikate in entities, triples und relationen zu entfernen und addded die relationen in das dict
def rm_exact_duplicates(data, relations):
    entities = data["entities"]
    triples = data["triples"]
    # step 3: exakte Duplikate in entities entfernen
    data["entities"] = list(dict.fromkeys(entities))
    # step 4: exakte Duplikate in triples entfernen
    #hier mit cbv und cbf aufpassen
    triples_tuples = convert_dicts_to_tuples(triples)
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

    # entfernt exekte Duplikate
    dedup_data = rm_exact_duplicates(data_lowercase, relations)
    
    entity_mapping, relation_mapping = process_retrieval(dedup_data)
   #todo data= apply_mappings(dedup_data, entity_mapping, relation_mapping)

    return dedup_data

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
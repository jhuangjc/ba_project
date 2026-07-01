from app.pipeline.refiner import data_to_lowercase
######################constants#####################
MATCH_NAME = "is_name"
MATCH_ALIAS = "is_alias"
#####################utility functions fuer metriken#####################
def calculate_precision(predicted, goldstandard):
    pass
def calculate_recall(predicted, goldstandard):
    pass
def calculate_f1(predicted, goldstandard):
    pass

# hilfsfunktion um heraus wie viele mappings eine Entity im goldstandard hat,es wird eine liste von gefundenen matchen zuruckgegeben, mit der id, in welchen eintrag im golstandard.
def match_entities_in_gold(predicted_entity, goldstandard):
    result = []
    for gold_item in goldstandard:
        if predicted_entity == gold_item["name"]:
            result.append([gold_item["name"], gold_item["id"], gold_item["name"],MATCH_NAME])
            continue
        for alias in gold_item["aliases"]:
            if predicted_entity == alias:
                result.append([gold_item["name"], gold_item["id"], alias, MATCH_ALIAS])
    return result

    
#hilfsfunktion um die predicted triples mit den goldstandard triples zu vergleichen, wichtig fuer das endergebnis
def map_to_gold(entities,goldstandard):
    #wandelt die golstandard in eine verschachtelte liste um.
    matched_gold_entities = {} 
    for entity in entities:
        #for each entity, invoke compare_entities to find the corresponding goldstandard entities
        matched_gold_entities[entity] = match_entities_in_gold(entity,goldstandard)
    return matched_gold_entities


#hilfsfunktion um die goldstandard entities in lowercase zu wandeln
def goldstandard_lowercase(goldstandard):
    for item in goldstandard:
        item["name"] = item["name"].lower()
        for i , alias in enumerate(item["aliases"]):
            item["aliases"][i] = alias.lower()
    return goldstandard
#hilfsfuntion um die relations aus dem goldstandard zu extrahieren, wichtig fuer das endergebnis
def extract_relations_from_gold(goldstandard):
    relations = []
    for item in goldstandard:
        relations.append(item["relation_label"].lower())
    return relations

#entities matche= {name: [matches...]}
#hilfsfunktion um die doppelten matches zu resolven
def resolve_duplicate_matches(matches):
    for match in matches:
        if match[3] == MATCH_NAME:
            return match[1]
#placholder loesung, bis passenderes matching implemetiert ist
    return -1


#hilfsfunktion, die ein dict mit den predicted items den matches baut
def resolve_entity_matches(entity_matches, predicted_entities):
    #build the table
    resolved_entities = {}
    for entity in predicted_entities:
        resolved_entities[entity] =-1 
    for entity, matches in entity_matches.items():
            if len(matches) == 1:
                resolved_entities[entity] = matches[0][1]
            elif len(matches) > 1:
                resolved_entities[entity] = resolve_duplicate_matches(matches)


    return resolved_entities
    
#####################orchastration functions fuer metriken#####################
def measure_data(predicted_lowercase,goldstandard_raw, before_refinement):
    if before_refinement:
        predicted_lowercase = data_to_lowercase(predicted_lowercase)
    #hold die entities in lowercase, um die vergleichbarkeit zu erleichtern 
    gold_list_lowercase= goldstandard_lowercase(goldstandard_raw["entities"])

    # map entites to goldstandard
    entity_matches = map_to_gold(predicted_lowercase["entities"], gold_list_lowercase)
    resolved_entities = resolve_entity_matches(entity_matches,predicted_lowercase["entities"])

    

    # map relations to goldstandard
    #generate a list of goldstandard relations
    gold_relations = extract_relations_from_gold(goldstandard_raw["relations"])


    metrics = {}

    
    return metrics
def generate_combined_metrics(metrics_before, metrics_after, goldstandard, refined_result):
    pass

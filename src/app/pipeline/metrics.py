from app.pipeline.refiner import data_to_lowercase
######################constants#####################
MATCH_NAME = "is_name"
MATCH_ALIAS = "is_alias"
#####################utility functions fuer metriken#####################
#hilfsfunktion um die precision zu berechnen
def calculate_precision(true_positives, false_positives):
    if true_positives + false_positives == 0:
        return 0
    return true_positives / (true_positives + false_positives)
#hilfsfunktion um die recall zu berechnen
def calculate_recall(true_positives, false_negatives):
    if true_positives + false_negatives == 0:
        return 0
    return true_positives / (true_positives + false_negatives)
#hilfsfunktion um die f1 zu berechnen
def calculate_f1(precision, recall):
    if precision + recall == 0:
        return 0
    return 2 * (precision * recall) / (precision + recall)
############### matching functions fuer metriken#####################
# hilfsfunktion um heraus wie viele mappings eine Entity im goldstandard hat,es wird eine liste von gefundenen matchen zuruckgegeben, mit der id, in welchen eintrag im golstandard.
def match_entities_in_gold(predicted_entity, goldstandard):
    result = []
    for gold_item in goldstandard:
        if predicted_entity["name"] == gold_item["name"] and predicted_entity["type"] == gold_item["type"]:
            result.append([gold_item["name"], gold_item["id"], gold_item["name"],MATCH_NAME])
            continue
        for alias in gold_item["aliases"]:
            if predicted_entity["name"] == alias and predicted_entity["type"] == gold_item["type"]:
                result.append([gold_item["name"], gold_item["id"], alias, MATCH_ALIAS])
    return result

    
#hilfsfunktion um die predicted triples mit den goldstandard triples zu vergleichen, wichtig fuer das endergebnis
def map_to_gold(entities,goldstandard):
    #wandelt die golstandard in eine verschachtelte liste um.
    matched_gold_entities = {} 
    for entity in entities:
        #for each entity, invoke compare_entities to find the corresponding goldstandard entities
        matched_gold_entities[(entity["name"], entity["type"])] = match_entities_in_gold(entity,goldstandard)
    return matched_gold_entities

####################### utility functions fuer metriken#####################
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
        resolved_entities[(entity["name"], entity["type"])] = -1
    for entity, matches in entity_matches.items():
            if len(matches) == 1:
                resolved_entities[entity] = matches[0][1]
            elif len(matches) > 1:
                resolved_entities[entity] = resolve_duplicate_matches(matches)


    return resolved_entities
 
#################### gen metriken utility #######################
# hilfsfunktion um true positives zu generieren. TP haben genau ein match
def generate_true_positives(resolved_entities):
    true_positives = 0
    for entity, value in resolved_entities.items():
        if value != -1:
            true_positives += 1
    return true_positives  
def generate_false_positives(resolved_entities):
    false_positives = 0
    for entity, value in resolved_entities.items():
        if value == -1:
            false_positives += 1
    return false_positives 
def generate_false_negatives(resolved_entities, goldstandard):
    false_negatives = 0
    #aggegiert alle resolved entity ids
    resolved_entity_ids = set(resolved_entities.values())
    matched_gold_ids = set()
    #aggegiert alle goldstandard ids
    for entity in goldstandard:
        matched_gold_ids.add(entity["id"])
    #berechnet die false negatives, indem die goldstandard ids mit den resolved entity ids verglichen werden 
    false_negatives = len(matched_gold_ids - resolved_entity_ids)
    return false_negatives
#####################orchastration functions fuer metriken#####################
def measure_data(predicted_lowercase,goldstandard_raw, before_refinement):
    if before_refinement:
        predicted_lowercase = data_to_lowercase(predicted_lowercase)
    #hold die entities in lowercase, um die vergleichbarkeit zu erleichtern 
    gs_copy = goldstandard_raw.copy()
    gold_list_lowercase= goldstandard_lowercase(gs_copy["entities"])

    # map entites to goldstandard
    entity_matches = map_to_gold(predicted_lowercase["entities"], gold_list_lowercase)
    resolved_entities = resolve_entity_matches(entity_matches,predicted_lowercase["entities"])

    True_Positives = generate_true_positives(resolved_entities)
    False_Positives = generate_false_positives(resolved_entities)
    False_Negatives = generate_false_negatives(resolved_entities, gold_list_lowercase)

    #berechne precision, recall und f1
    precision = calculate_precision(True_Positives, False_Positives)
    recall = calculate_recall(True_Positives, False_Negatives)
    f1 = calculate_f1(precision, recall)
    # map relations to goldstandard
    #generate a list of goldstandard relations
    gold_relations = extract_relations_from_gold(goldstandard_raw["relations"])


    metrics = {"entity_metrics":
               {
                   "true_positives": True_Positives,
                   "false_positives": False_Positives,
                   "false_negatives": False_Negatives,
                   "precision": precision,
                   "recall": recall,
                   "f1": f1},
                "relation_metrics":
                {},
                "triple_metrics":
                {}
               }

    
    return metrics
def generate_combined_metrics(metrics_before, metrics_after, goldstandard, refined_result):
    pass

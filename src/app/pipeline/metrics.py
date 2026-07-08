from app.pipeline.refiner import data_to_lowercase
from app.utils.gold import extract_gold_relations
from app.utils.gold import goldstandard_lowercase
######################constants#####################
MATCH_NAME = "is_name"
MATCH_ALIAS = "is_alias"
#####################other utility functions#####################
#hilfsfunktion um die ids der entities in die triples zu schreiben, damit sie mit dem goldstandard verglichen werden koennen
def apply_id(triples, resolved_entities):
    for triple in triples:
        subject = (triple["subject"]["name"], triple["subject"]["type"])
        object_ = (triple["object"]["name"], triple["object"]["type"])
        triple["subject"]["id"] = resolved_entities.get(subject, -1)
        triple["object"]["id"] = resolved_entities.get(object_, -1)
    return triples
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
############### matching functions fuer entitties#####################
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
#######################matching functions fuer relations#####################
#hilfsfunktion um die predicted triples mit den goldstandard triples zu vergleichen, wichtig fuer das endergebnis
def map_relations_to_gold(predicted_relations, gold_relations):
    matches=set()
    for relation in predicted_relations:
        if relation in gold_relations:
            matches.add(relation)
    return list(matches)
def triples_in_gold(predicted_triples, goldstandard):
    #probelem, the dicts are named differently, so we need to map them to the same format
    #convert both to a common format
    matches = []
    for relation in goldstandard["relations"]:
        for elem in predicted_triples:
            if relation["head_id"] == elem["subject"]["id"] and relation["relation_label"] == elem["predicate"] and relation["tail_id"] == elem["object"]["id"]:
                matches.append(elem)
    return matches
####################### utility functions fuer metriken#####################
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

    True_Positives_entities = generate_true_positives(resolved_entities)
    False_Positives_entities = generate_false_positives(resolved_entities)
    False_Negatives_entities = generate_false_negatives(resolved_entities, gold_list_lowercase)

    #berechne precision, recall und f1
    precision_entities = calculate_precision(True_Positives_entities, False_Positives_entities)
    recall_entities = calculate_recall(True_Positives_entities, False_Negatives_entities)
    f1_entities = calculate_f1(precision_entities, recall_entities)
    # map relations to goldstandard
    #generate a list of goldstandard relations
    gold_relations = extract_gold_relations(goldstandard_raw) 



    #metrics relations
    relation_matches=map_relations_to_gold(predicted_lowercase["relations"], gold_relations)
    False_Positives_relations = len(predicted_lowercase["relations"]) - len(relation_matches)
    True_Positives_relations = len(relation_matches)
    False_Negatives_relations = len(gold_relations) - len(relation_matches)
    
    
    
    #berechne precision, recall und f1
    precision_relations = calculate_precision(True_Positives_relations, False_Positives_relations)
    recall_relations = calculate_recall(True_Positives_relations, False_Negatives_relations)
    f1_relations = calculate_f1(precision_relations, recall_relations)
    #metrics triples
    triples = predicted_lowercase["triples"]
    triples = apply_id(triples, resolved_entities)
    triples_matches = triples_in_gold(triples, goldstandard_raw)
    tripels_true_positives = len(triples_matches)
    tripels_false_positives = len(triples) - len(triples_matches)
    tripels_false_negatives = len(goldstandard_raw["relations"]) - len(triples_matches)
    precision_triples = calculate_precision(tripels_true_positives, tripels_false_positives)
    recall_triples = calculate_recall(tripels_true_positives, tripels_false_negatives)
    f1_triples = calculate_f1(precision_triples, recall_triples)

    metrics = {"entity_metrics":
               {
                   "true_positives": True_Positives_entities,
                   "false_positives": False_Positives_entities,
                   "false_negatives": False_Negatives_entities,
                   "precision": precision_entities,
                   "recall": recall_entities,
                   "f1": f1_entities},
                "relation_metrics":
                {
                    "true_positives": True_Positives_relations,
                    "false_positives": False_Positives_relations,
                    "false_negatives": False_Negatives_relations,
                    "precision": precision_relations,
                    "recall": recall_relations,
                    "f1": f1_relations
                },
                "triple_metrics":
                {
                    "true_positives": tripels_true_positives,
                    "false_positives": tripels_false_positives,
                    "false_negatives": tripels_false_negatives,
                    "precision": precision_triples,
                    "recall": recall_triples,
                    "f1": f1_triples
                }
               }

    
    return metrics
def generate_combined_metrics(metrics_before, metrics_after, goldstandard, refined_result):
    pass

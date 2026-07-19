from app.pipeline.refiner import data_to_lowercase
from app.utils.gold import extract_gold_relations
from app.utils.gold import goldstandard_lowercase
from scipy.optimize import linear_sum_assignment

import copy


######################constants#####################
MATCH_NAME = "is_name"
MATCH_ALIAS = "is_alias"
##################### utility functions#####################
#hilfsfunktion die das triple key in ein string umwandelt
def resolve_to_string(value):
    result = {}
    for entity, g_id in value.items():
        result[entity[0] + "_" + entity[1]] = g_id
    return result
#hilfsfunktion um die ids der entities in die triples zu schreiben, damit sie mit dem goldstandard verglichen werden koennen
def apply_id(triples, resolved_entities):
    for triple in triples:
        subject = (triple["subject"]["name"], triple["subject"]["type"])
        object_ = (triple["object"]["name"], triple["object"]["type"])
        triple["subject"]["id"] = resolved_entities.get(subject, -1)
        triple["object"]["id"] = resolved_entities.get(object_, -1)
    return triples
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
#loose match funktion
def loose_match(predicted_name, gold_name):
    #beide name normalieren und leerzeichen entfernen
    predicted_name = predicted_name.lower().replace(" ", "")
    gold_name = gold_name.lower().replace(" ", "")
    if gold_name in predicted_name:
        return True
    return False
#metrik-helper für entities
def gen_entity_metrics(resolved_matches, goldstandard_lowercase):
    #generiere counts
    true_positives = generate_true_positives(resolved_matches)
    false_positives = generate_false_positives(resolved_matches)
    false_negatives = generate_false_negatives(resolved_matches, goldstandard_lowercase)
    #metriken berechnen
    precision = calculate_precision(true_positives, false_positives)
    recall = calculate_recall(true_positives, false_negatives)
    f1 = calculate_f1(precision, recall)

    return {
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision": precision,
        "recall": recall,
        "f1": f1
    }
# metrik-helper für relationen
def gen_relation_metrics(predicted_relations, gold_relations):
    #pre processing
    relation_matches, extra_relations = map_relations_to_gold(predicted_relations, gold_relations)
    matched_relations, unmatched_relations = get_details_relations(relation_matches, gold_relations)
    #generiere counts
    tp = len(relation_matches)
    fp = len(predicted_relations) - len(relation_matches)
    fn = len(gold_relations) - len(relation_matches)
    #metriken berechnen
    precision = calculate_precision(tp, fp)
    recall = calculate_recall(tp, fn)
    f1 = calculate_f1(precision, recall)
    metrics = {
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1
    }
    details = {
        "matched": matched_relations,
        "unmatched": unmatched_relations,
        "extra": extra_relations
    }
    return metrics, details
# metrik-helper für triples
def gen_triple_metrics(triples, resolved_entities, goldstandard_raw):
    triples_copy = copy.deepcopy(triples)
    triples_with_ids = apply_id(triples_copy, resolved_entities)
    triples_matches, extra_triples = triples_in_gold(triples_with_ids, goldstandard_raw)
    matched_triples, unmatched_triples = get_details_triples(triples_matches, goldstandard_raw)
    #generiere counts
    tp = len(triples_matches)
    fp = len(triples) - len(triples_matches)
    fn = len(goldstandard_raw["relations"]) - len(triples_matches)
    #metriken berechnen
    precision = calculate_precision(tp, fp)
    recall = calculate_recall(tp, fn)
    f1 = calculate_f1(precision, recall)
    metrics = {
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1
    }
    details = {
        "matched": matched_triples,
        "unmatched": unmatched_triples,
        "extra": extra_triples
    }
    return metrics, details
#delta zwischen strict und loose berechnen
def compute_metrics_delta(strict_metrics, loose_metrics):
    delta = {}
    for metric_type in strict_metrics:
        delta[metric_type] = {}
        for key in strict_metrics[metric_type]:
            delta[metric_type][key] = loose_metrics[metric_type][key] - strict_metrics[metric_type][key]
    return delta
############### matching functions fuer entities#####################
# hilfsfunktion um heraus wie viele mappings eine Entity im goldstandard hat,es wird eine liste von gefundenen matchen zuruckgegeben. 
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
#gleiche funktion mit loose matching
def loose_match_entities(predicted_entity, goldstandard):
    result = []
    for gold_item in goldstandard:
        if predicted_entity["type"] == gold_item["type"]:
            if predicted_entity["name"] == gold_item["name"]:
                result.append([gold_item["name"], gold_item["id"], gold_item["name"],MATCH_NAME])
                continue

            for alias in gold_item["aliases"]:
                if predicted_entity["name"] == alias:
                    result.append([gold_item["name"], gold_item["id"], alias, MATCH_ALIAS])
                    break
    if not result:
        for entity in goldstandard:
            if predicted_entity["type"] == entity["type"]:
                if loose_match(predicted_entity["name"], entity["name"]):
                    result.append([entity["name"], entity["id"], entity["name"],MATCH_NAME])
                    continue
                for alias in entity["aliases"]:
                    if loose_match(predicted_entity["name"], alias):
                        result.append([entity["name"], entity["id"], alias, MATCH_ALIAS])
                        break
    return result

#hilfsfunktion um die predicted triples mit den goldstandard triples zu vergleichen, wichtig fuer das endergebnis
def map_to_gold(entities,goldstandard, loose_matching=False):
    #wandelt die golstandard in eine verschachtelte liste um.
    matched_gold_entities = {} 
    for entity in entities:
        #for each entity, invoke compare_entities to find the corresponding goldstandard entities
        if loose_matching:
            matched_gold_entities[(entity["name"], entity["type"])] = loose_match_entities(entity,goldstandard)
        else:
            matched_gold_entities[(entity["name"], entity["type"])] = match_entities_in_gold(entity,goldstandard)
    return matched_gold_entities
#hilfsfunktion um die predicted triples mit den goldstandard triples zu vergleichen, wichtig fuer das endergebnis
def map_relations_to_gold(predicted_relations, gold_relations):
    matches=set()
    extra=set()
    for relation in predicted_relations:
        if relation in gold_relations:
            matches.add(relation)
        else:
            extra.add(relation)
    return list(matches), list(extra)
def triples_in_gold(predicted_triples, goldstandard):
    #probelem, the dicts are named differently, so we need to map them to the same format

    matches = []
    extra = []

    for elem in predicted_triples:
        found = False
        for relation in goldstandard["relations"]:
            if relation["head_id"] == elem["subject"]["id"] and relation["relation_label"] == elem["predicate"] and relation["tail_id"] == elem["object"]["id"]:
                matches.append(elem)
                found = True
                break
        #um duplikates zu vermeiden, wird die relation nach der for aufgenommen
        if not found:
            extra.append(elem)
    return matches, extra

####################### utility functions fuer matches #####################
#hilfsfunktion um die doppelten matches zu resolven
def resolve_duplicate_matches(matches):
    for match in matches:
        if match[3] == MATCH_NAME:
            return match[1]


    return matches[0][1]
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
############################zaehlfunktionen fuer die metriken#####################
#zaehlfunktion fuer mengen von items
def get_details_entities(resolved_entities, goldstandard):
    matched = []
    unmatched = []
    extra = []
    #wenn die enity in resolved entities nicht -1 ist, dann ist sie matched, sonst extra. 
    #Wenn die entity im goldstandard nicht in resolved entities ist, dann ist sie missed.
    for entity, value in resolved_entities.items():
        if value != -1:
            matched.append({"name": entity[0], "type": entity[1], "id": value})
        else:
            extra.append({"name": entity[0], "type": entity[1]})
    for entity in goldstandard:
        if entity["id"] not in resolved_entities.values():
            unmatched.append({"name": entity["name"], "type": entity["type"], "id": entity["id"]})
    return matched, unmatched, extra
def get_details_relations(relation_matches, gold_relations):
    matched = []
    unmatched = []
    #das gleich wie bei den entities,hier ist das datenformat einfacher
    for relation in relation_matches:
        if relation in gold_relations:
            matched.append(relation)
    for relation in gold_relations:
        if relation not in relation_matches:
            unmatched.append(relation)
    return matched, unmatched
def get_details_triples(triples_matches, goldstandard):
    matched = []
    unmatched = []
    #das gleich wie bei den entities,arbeit mit ids
    for triple in triples_matches:
        matched.append(triple)
    for relation in goldstandard["relations"]:
        found = False
        for triple in triples_matches:
            if relation["head_id"] == triple["subject"]["id"] and relation["relation_label"] == triple["predicate"] and relation["tail_id"] == triple["object"]["id"]:
                found = True
                break
        if not found:
            unmatched.append(relation)
    return matched, unmatched
#hilfsfunktion tp, fp, fn zu generieren    
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
#####################cluster metrics################################

def gen_cluster_metrics(predicted_clusters, goldstandard_clusters):
    #preprocessing
    pc=copy.deepcopy(predicted_clusters)
    #name ist nicht in predicted clusters drinne, wird hier hinzugefuegt
    predicted_clusters_adjusted = []
    for key,value in pc.items():
        c=set(value)
        c.add(key)
        predicted_clusters_adjusted.append(c)
    #goldstand muss auch adjustet werden, damit der algorithmus funktioniert
    gc=copy.deepcopy(goldstandard_clusters)
    goldstandard_clusters_adjusted = []
    for cluster in gc:
        c=set()
        for alias in cluster["aliases"]:
            c.add((alias, cluster["type"]))
        goldstandard_clusters_adjusted.append(c)
    #bau die kostenmatrix
    cost_matrix = []
    for i in range(len(predicted_clusters_adjusted)):
        row = []
        for j in range(len(goldstandard_clusters_adjusted)):
            row.append(-len(predicted_clusters_adjusted[i].intersection(goldstandard_clusters_adjusted[j])))
        cost_matrix.append(row)
    #call den hungarian algorithmus
    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    #berechne die true positives, false positives und false negatives
    true_positives = 0
    false_positives = 0
    false_negatives = 0
    for i,j in zip(row_ind, col_ind):
        intersection = predicted_clusters_adjusted[i].intersection(goldstandard_clusters_adjusted[j])
        true_positives += len(intersection)
        false_positives += len(predicted_clusters_adjusted[i]) - len(intersection)
        false_negatives += len(goldstandard_clusters_adjusted[j]) - len(intersection)
    #ungemachte cluster auswerten
    for i in range(len(predicted_clusters_adjusted)):
        if i not in row_ind:
            false_positives += len(predicted_clusters_adjusted[i])
    for j in range(len(goldstandard_clusters_adjusted)):
        if j not in col_ind:
            false_negatives += len(goldstandard_clusters_adjusted[j])    
    #berechne precision, recall und f1
    precision = calculate_precision(true_positives, false_positives)
    recall = calculate_recall(true_positives, false_negatives)
    f1 = calculate_f1(precision, recall)
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1
    } 
#################################cluster coverage metrics################################
def gen_cluster_hit_table(resolved_entities, gold_entities):
    hit_table = []
    #fuell die tabllelle
    for entity in gold_entities:
        hit_table.append({"gold_id": entity["id"], "name": entity["name"], "type": entity["type"], "hit": 0})
    
    #berechne die hits
    for entity, value in resolved_entities.items():
        if value != -1:
            for row in hit_table:
                if row["gold_id"] == value:
                    row["hit"] += 1
                    break

    return hit_table

def gen_cluster_coverage_metrics(resolved_entities, gold_entities):
    hit_table = gen_cluster_hit_table(resolved_entities, gold_entities)
    #berechne die coverage
    table_length = len(gold_entities)
    count =0
    for row in hit_table:
        if row["hit"] > 0:
            count += 1
    covered_gold = count
    coverage = covered_gold / table_length if table_length > 0 else 0
    #berchne mit avg cluster hit
    total_hits=0
    for row in hit_table:
        total_hits += row["hit"]
    avg_cluster_hit = total_hits / table_length if table_length > 0 else 0

    return {
        "covered_gold": covered_gold,
        "coverage": coverage,
        "avg_cluster_hit": avg_cluster_hit
    }
def tuple_dict(tuple_set):
    result = []
    for item in tuple_set:
        result.append({"name": item[0], "type": item[1]})
    return result

def categorize_error_sources(details_before, details_after):
    """Klassifiziert Fehlerquellen durch Before/After-Vergleich der Entity-Details.

    Returns:
        dict mit:
        - generation_error: Entities, die sowohl vor als auch nach Refinement FP sind
        - refinement_error: Entities, die NACH Refinement neu FP wurden
        - resolved_through_refinement: Entities, die VOR Refinement FP waren, danach nicht mehr
        - lost_matches: Entities, die VOR Refinement gematcht waren, NACH Refinement nicht mehr
    """
    def _entity_set(details, key):
        result = set()
        for item in details["entities"][key]:
            result.add((item["name"], item["type"]))
        return result

    before_extra = _entity_set(details_before, "extra")
    after_extra = _entity_set(details_after, "extra")
    before_matched = _entity_set(details_before, "matched")
    after_matched = _entity_set(details_after, "matched")

    generation_error = before_extra & after_extra
    refinement_error = after_extra - before_extra
    resolved_error = before_extra - after_extra
    lost_matches = before_matched - after_matched

    return {
        "generation_error": tuple_dict(generation_error),
        "refinement_error": tuple_dict(refinement_error),
        "resolved_through_refinement": tuple_dict(resolved_error),
        "lost_matches": tuple_dict(lost_matches)
    }
 

#####################orchestration functions fuer metriken#####################
def measure_data(predicted_lowercase, goldstandard_raw, before_refinement):

    gs_copy = goldstandard_raw.copy()
    p_copy = predicted_lowercase.copy()
    # normalisiere die predicted data, wenn es vor dem refinement ist
    if before_refinement:
        p_copy = data_to_lowercase(p_copy)

    gold_list_lowercase = goldstandard_lowercase(gs_copy["entities"])
    gold_relations = extract_gold_relations(goldstandard_raw)

    # entity matching fuer strict
    entity_matches_strict = map_to_gold(p_copy["entities"], gold_list_lowercase, loose_matching=False)
    resolved_entities_strict = resolve_entity_matches(entity_matches_strict, p_copy["entities"])

    cluster_hit_metrics_strict = gen_cluster_coverage_metrics(resolved_entities_strict, gold_list_lowercase)

    # entity matching fuer loose
    entity_matches_loose = map_to_gold(p_copy["entities"], gold_list_lowercase, loose_matching=True)
    resolved_entities_loose = resolve_entity_matches(entity_matches_loose, p_copy["entities"])

    # metriken
    entity_metrics_strict = gen_entity_metrics(resolved_entities_strict, gold_list_lowercase)
    entity_details_strict = get_details_entities(resolved_entities_strict, gold_list_lowercase)

    cluster_hit_metrics_loose = gen_cluster_coverage_metrics(resolved_entities_loose, gold_list_lowercase)
    entity_metrics_loose = gen_entity_metrics(resolved_entities_loose, gold_list_lowercase)
    entity_details_loose = get_details_entities(resolved_entities_loose, gold_list_lowercase)

    # metriken fuer relationen
    relation_metrics, relation_details = gen_relation_metrics(p_copy["relations"], gold_relations)

    # metriken fuer triples
    triple_metrics_strict, triple_details_strict = gen_triple_metrics(p_copy["triples"], resolved_entities_strict, goldstandard_raw)
    triple_metrics_loose, triple_details_loose = gen_triple_metrics(p_copy["triples"], resolved_entities_loose, goldstandard_raw)

    # output
    metrics_strict = {
        "entity_metrics": entity_metrics_strict,
        "relation_metrics": relation_metrics,
        "triple_metrics": triple_metrics_strict,
        "cluster_hit_metrics": cluster_hit_metrics_strict
    }
    details_strict = {
        "entities": {"matched": entity_details_strict[0], "unmatched": entity_details_strict[1], "extra": entity_details_strict[2]},
        "relations": relation_details,
        "triples": triple_details_strict
    }

    metrics_loose = {
        "entity_metrics": entity_metrics_loose,
        "relation_metrics": relation_metrics,
        "triple_metrics": triple_metrics_loose,
        "cluster_hit_metrics": cluster_hit_metrics_loose
    }
    details_loose = {
        "entities": {"matched": entity_details_loose[0], "unmatched": entity_details_loose[1], "extra": entity_details_loose[2]},
        "relations": relation_details,
        "triples": triple_details_loose
    }

    delta = compute_metrics_delta(metrics_strict, metrics_loose)

    return {
        "strict": {
            "metrics": metrics_strict,
            "details": details_strict
        },
        "loose": {
            "metrics": metrics_loose,
            "details": details_loose
        },
        "delta": delta,
        "debug": {"resolved_entities_strict": resolve_to_string(resolved_entities_strict), "resolved_entities_loose": resolve_to_string(resolved_entities_loose)},
        "resolved_strict_raw": resolved_entities_strict
    }



def generate_combined_metrics(goldstandard, entity_mapping, resolved_before=None, resolved_after=None):
    gs_copy = goldstandard_lowercase(copy.deepcopy(goldstandard["entities"]))
    dedup_metrics = gen_cluster_metrics(entity_mapping, gs_copy)
    combined_metrics = {
        "deduplication_metrics": dedup_metrics
    }
    return combined_metrics

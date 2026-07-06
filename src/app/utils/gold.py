#hilfsfunktion um die relationen aus dem goldstandard zu extrahieren
def extract_gold_relations(goldstandard):
    relations = set()
    for item in goldstandard["relations"]:
        relations.add(item["relation_label"].lower())
    return list(relations)
#hilfsfunktion um die goldstandard entities in lowercase zu wandeln
def goldstandard_lowercase(goldstandard):
    for item in goldstandard:
        item["name"] = item["name"].lower()
        for i , alias in enumerate(item["aliases"]):
            item["aliases"][i] = alias.lower()
    return goldstandard


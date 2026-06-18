from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity as cos_sim
from ranking_bm25 import BM25Okapi

# lade das Modell
model = SentenceTransformer("all-MiniLM-L6-v2")

# input: dict mit den keys "entities", "triples" und "relations"
def vectorise_data(data):
    entities = data["entities"]
    relations = data["relations"]

    entity_embeddings = model.encode(entities)
    relation_embeddings = model.encode(relations)
    return entity_embeddings, relation_embeddings
# auslagerung bm 25 prepwork
def prepare_bm25(item_list):
    tokenized_items = []
    for item in item_list:
        tokenized_items.append(item.split())
    bm25 = BM25Okapi(tokenized_items)
    return bm25

# diese hilfs funktion ist teil des mein flows
# es soll die nach und nach die elemente in der item list druchgehen und
# und anhand von similarity score und bm 25 die top k elemente zurueckgbeen werden.
# kggen wichtet den similiarity score und bm 25 score gleich.
#work in progress
def get_top_k_elements(embedding, bm_object,query_item,query_item_embedding,k=4):
    # bm 25 vorbereiten
    # berechne den sililarity score der query item zu allesn items in der item list
    bm25_scores = bm_object.get_scores(query_item.split())
    if max(bm25_scores) > 0:
        normalized_bm25_scores = bm25_scores / max(bm25_scores)
    else:
        normalized_bm25_scores = bm25_scores
    # berechen den similarity score der query zu items in der embedding liste
    similarity_scores =cos_sim([query_item_embedding], embedding).flatten()
    # rechne beide score zusammen um dann die top k element zu bekommen
    combined_scores = similarity_scores + normalized_bm25_scores
    # holt die indizes der top k elemente
    top_k_items_indices = combined_scores.argsort()[-k:][::-1]
    return top_k_items_indices





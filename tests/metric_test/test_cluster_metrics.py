import pytest
from app.pipeline.metrics import gen_cluster_metrics, generate_combined_metrics, measure_data

def test_gen_cluster_metrics_perfect_match():
    goldstandard = [{
        "name": "Jonas",
        "type": "PER",
        "aliases": ["Jonas", "Jonas Doe"]
        }]
    predicted = {("Jonas", "PER"):[("Jonas Doe", "PER")] }
    metrics = gen_cluster_metrics(predicted, goldstandard)
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["f1"] == 1.0

def test_gen_cluster_metrics_partial_match():
    goldstandard = [{
        "name": "Jonas",
        "type": "PER",
        "aliases": ["Jonas", "Jonas Doe"]
        }]
        #predicted kennt nur einen der aliase      
    predicted = {("Jonas", "PER"):[] }
    metrics = gen_cluster_metrics(predicted, goldstandard)
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 0.5
    assert metrics["f1"] == pytest.approx(0.6667, 0.01)

def test_gen_cluster_metrics_no_match():
    goldstandard = [{
        "name": "Jonas",
        "type": "PER",
        "aliases": ["Jonas", "Jonas Doe"]
        }]
    predicted = {("Jonas", "LOC"):[] }
    metrics = gen_cluster_metrics(predicted, goldstandard)
    assert metrics["precision"] == 0.0
    assert metrics["recall"] == 0.0
    assert metrics["f1"] == 0.0

def test_gen_cluster_metics_extra_predicted():
    goldstandard = [{
        "name": "Jonas",
        "type": "PER",
        "aliases": ["Jonas", "Jonas Doe"]
        }]
    predicted = {("Jonas", "PER"):[], ("Extra", "PER"):[] }
    metrics = gen_cluster_metrics(predicted, goldstandard)
    assert metrics["precision"] == 0.5
    assert metrics["recall"] == 0.5
    assert metrics["f1"] == 0.5 

def test_gen_cluster_metrics_extra_goldstandard():
    goldstandard = [{
        "name": "Jonas",
        "type": "PER",
        "aliases": ["Jonas", "Jonas Doe"]
        }, {
        "name": "Extra",
        "type": "PER",
        "aliases": ["Extra"]
        }]
    predicted = {("Jonas", "PER"):[] }
    metrics = gen_cluster_metrics(predicted, goldstandard)
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == pytest.approx(0.333, 0.01)
    assert metrics["f1"] == pytest.approx(0.5, 0.01)
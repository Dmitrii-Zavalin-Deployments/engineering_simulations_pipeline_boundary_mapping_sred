# /tests/pipeline/test_metadata_enrichment.py

import pytest
import logging
import json
from unittest.mock import patch, mock_open
from src.pipeline import metadata_enrichment as me

# 🧪 Basic utility functions
def test_compute_domain_size():
    assert me.compute_domain_size(10, 20, 30) == 6000
    assert me.compute_domain_size(0, 0, 0) == 0

def test_compute_spacing_hint_valid():
    domain_size = 1000
    nx, ny, nz = 10, 10, 10
    assert me.compute_spacing_hint(domain_size, nx, ny, nz) == 1000 / 30

def test_compute_spacing_hint_zero_dim():
    result = me.compute_spacing_hint(1000, 0, 0, 0)
    assert result is None

def test_compute_resolution_density_valid():
    assert me.compute_resolution_density(1000, 500) == 2.0

def test_compute_resolution_density_invalid_volume(caplog):
    with caplog.at_level(logging.WARNING):
        result = me.compute_resolution_density(1000, 0)
        assert result is None
        assert "Missing or invalid bounding_volume" in caplog.text

def test_is_zero_resolution_true():
    assert me.is_zero_resolution(10, 10, 10, 0) is True

def test_is_zero_resolution_false():
    assert me.is_zero_resolution(10, 10, 10, 1000) is False

# 🧪 enrich_metadata_pipeline() behavior
@patch("src.pipeline.metadata_enrichment.load_pipeline_index", return_value={"mock": True})
def test_enrich_metadata_success(mock_load):
    result = me.enrich_metadata_pipeline(10, 10, 10, 1000)
    assert result["domain_size"] == 1000
    assert result["spacing_hint"] > 0
    assert result["resolution_density"] == 1.0

def test_enrich_metadata_config_disabled(caplog):
    caplog.set_level(logging.INFO)  # ✅ Ensure INFO logs are captured
    result = me.enrich_metadata_pipeline(10, 10, 10, 1000, config_flag=False)
    assert result == {}
    assert "Metadata tagging disabled." in caplog.text

def test_enrich_metadata_zero_resolution(caplog):
    caplog.set_level(logging.INFO)
    result = me.enrich_metadata_pipeline(10, 10, 10, 0)
    assert result == {}
    assert "Zero resolution detected" in caplog.text

# 📂 load_pipeline_index mock
@patch("builtins.open", new_callable=mock_open, read_data='{"foo": "bar"}')
def test_load_pipeline_index(mock_file):
    result = me.load_pipeline_index("dummy_path.json")
    assert result["foo"] == "bar"
    mock_file.assert_called_once_with("dummy_path.json", "r")




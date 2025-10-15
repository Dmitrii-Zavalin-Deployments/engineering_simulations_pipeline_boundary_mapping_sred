# tests/test_geometry.py

import pytest
from src.geometry import classify_face_label

def test_x_axis_positive_classification():
    normal = [1.0, 0.0, 0.0]
    label = classify_face_label(normal, face_id=1, debug=False)
    assert label == "x_max"

def test_x_axis_negative_classification():
    normal = [-1.0, 0.0, 0.0]
    label = classify_face_label(normal, face_id=2, debug=False)
    assert label == "x_min"

def test_y_axis_positive_classification():
    normal = [0.0, 1.0, 0.0]
    label = classify_face_label(normal, face_id=3, debug=False)
    assert label == "y_max"

def test_y_axis_negative_classification():
    normal = [0.0, -1.0, 0.0]
    label = classify_face_label(normal, face_id=4, debug=False)
    assert label == "y_min"

def test_z_axis_positive_classification():
    normal = [0.0, 0.0, 1.0]
    label = classify_face_label(normal, face_id=5, debug=False)
    assert label == "z_max"

def test_z_axis_negative_classification():
    normal = [0.0, 0.0, -1.0]
    label = classify_face_label(normal, face_id=6, debug=False)
    assert label == "z_min"

def test_threshold_failure_returns_wall():
    normal = [0.5, 0.5, 0.5]  # All components below threshold
    label = classify_face_label(normal, face_id=7, debug=False)
    assert label == "wall"

def test_non_dominant_axis_returns_wall():
    normal = [0.6, 0.6, 0.6]  # max component < 0.95
    label = classify_face_label(normal, face_id=8, debug=False)
    assert label == "wall"

def test_debug_output_triggers_print(capsys):
    normal = [0.0, 1.0, 0.0]
    label = classify_face_label(normal, face_id=9, debug=True)
    captured = capsys.readouterr()
    assert "[DEBUG_LABEL]" in captured.out
    assert label == "y_max"




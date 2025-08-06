## 📘 Fallback Resolution Trace — Strategy & Examples

_Last updated: 2025-07-28_

---

### 🎯 What is Fallback Resolution?

When a user or upstream system provides incomplete grid spacing inputs (`dx`, `dy`, `dz`), the pipeline applies a prioritized fallback mechanism to safely derive resolution values.

This ensures that the simulation domain remains valid even under partial configuration or missing data.

---

### 🔁 Resolution Fallback Priority

```text
INPUT_HINT → CONFIG_DEFAULT → HEURISTIC_ESTIMATION
```

| Source              | Description                                                         | Coverage Behavior         |
|---------------------|----------------------------------------------------------------------|---------------------------|
| ✅ Input Hint        | User provides explicit `dx`, `dy`, `dz` in run request               | Used directly if valid     |
| ✅ Config Default     | Fallback to values from `system_config.json` → `"default_resolution"` | Used if hint is missing    |
| ✅ Heuristic Estimate | Compute spacing from domain extent and default grid count (`nx`, etc.) | Final fallback if others fail |

---

### 🧪 Example Scenarios

#### Case A — All Hints Provided

```json
{
  "dx": 1.0,
  "dy": 1.0,
  "dz": 1.0
}
```

→ Resolution uses these values directly.  
→ Config and heuristic are skipped.  
→ `resolution_density`, `spacing_hint`, and `domain_size` derived from these.

---

#### Case B — Partial Config + No Hint

```json
"default_resolution": {
  "dx": 0.5,
  "dz": 0.25
}
```

→ Missing `dy` triggers heuristic estimation.  
→ Final `dy` computed as:  
  `dy = (bounding_box["ymax"] - bounding_box["ymin"]) / default_ny`

---

#### Case C — Missing Everything

```json
"dx": null,
"default_resolution": {}
```

→ All spacing values derived from bounding box extents:  
```python
dx = (xmax - xmin) / nx_default
dy = (ymax - ymin) / ny_default
dz = (zmax - zmin) / nz_default
```

→ Triggered when both hint and config paths are unavailable.

---

### 📦 Trace Logging Reference

From `run_pipeline.py`, example fallback logs:

```
WARNING: Resolution hint 'dy' missing — falling back to config value
INFO: Using config default dy = 0.6
INFO: dz not found in config — estimating from bounding box: dz = 0.25
```

---

### 📐 Metadata Dependency

Metadata enrichment values depend heavily on resolution precision:

| Field               | Derived From                             |
|---------------------|------------------------------------------|
| `spacing_hint`      | Average of `dx`, `dy`, `dz`              |
| `resolution_density`| `domain_size / volume`                   |
| `domain_size`       | `nx * ny * nz`                           |

→ Imprecise or heuristic estimates may degrade simulation fidelity.

---

### ⚙️ Configuration Notes

Ensure your `system_config.json` includes:

```json
"default_resolution": {
  "dx": 0.5,
  "dy": 0.5,
  "dz": 0.5
}
```

You may also specify:

```json
"default_grid_dimensions": {
  "nx": 10,
  "ny": 20,
  "nz": 30
}
```

These values are used for heuristic calculations when resolution spacing is unknown.

---

### 🔗 Integration References

| Module                | Function                              |
|------------------------|----------------------------------------|
| `resolution_calculator.py` | Applies fallback logic for `dx/dy/dz` |
| `test_fallback_paths.py`   | Tests fallback activation patterns   |
| `system_config.json`       | Supplies config default spacing      |
| `run_pipeline.py`          | Orchestrates fallback application and logs |

---



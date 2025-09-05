# /src/pipeline/metadata_enrichment.py

import json
import logging
import yaml

logger = logging.getLogger(__name__)

def load_pipeline_index(config_path="configs/metadata/pipeline_index.json"):
    with open(config_path, 'r') as f:
        return json.load(f)

def load_resolution_profile(profile_path="configs/validation/resolution_profile.yaml"):
    try:
        with open(profile_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"Failed to load resolution profile: {e}")
        return {}

def compute_domain_size(nx, ny, nz):
    return nx * ny * nz

def compute_spacing_hint(domain_size, nx, ny, nz):
    total_dims = nx + ny + nz
    return domain_size / total_dims if total_dims > 0 else None

def compute_resolution_density(domain_size, bounding_volume):
    if bounding_volume and bounding_volume > 0:
        return domain_size / bounding_volume
    logger.warning("Missing or invalid bounding_volume for resolution_density.")
    return None

def is_zero_resolution(nx, ny, nz, bounding_volume):
    domain_size = compute_domain_size(nx, ny, nz)
    resolution_density = compute_resolution_density(domain_size, bounding_volume)
    return resolution_density is None or resolution_density == 0

def enrich_metadata_pipeline(nx, ny, nz, bounding_volume, config_flag=True):
    if not config_flag:
        logger.info("Metadata tagging disabled.")
        return {}

    if is_zero_resolution(nx, ny, nz, bounding_volume):
        logger.warning("Zero resolution detected — skipping metadata enrichment.")
        return {}

    index = load_pipeline_index()
    config = load_resolution_profile()

    domain_size = compute_domain_size(nx, ny, nz)
    spacing_hint = compute_spacing_hint(domain_size, nx, ny, nz)
    resolution_density = compute_resolution_density(domain_size, bounding_volume)

    metadata = {
        "domain_size": domain_size,
        "spacing_hint": spacing_hint,
        "resolution_density": resolution_density
    }

    if metadata["resolution_density"] is None:
        fallback = config.get("default_resolution_density", 0.5)
        metadata["resolution_density"] = fallback
        logger.info(f"Injected default resolution_density from config: {fallback}")

    logger.info("Enriched metadata computed.")
    return metadata




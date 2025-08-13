# src/clustering_engine.py

import numpy as np
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from typing import List, Dict, Tuple

def extract_normals(faces: List[Dict]) -> Tuple[List[int], np.ndarray]:
    """
    Extract face IDs and normal vectors from face vertex data.
    """
    ids = []
    normals = []

    for face in faces:
        vertices = face.get("vertices", [])
        if len(vertices) >= 3:
            v0, v1, v2 = np.array(vertices[:3])
            normal = np.cross(v1 - v0, v2 - v0)
            norm = np.linalg.norm(normal)
            if norm != 0:
                ids.append(face["id"])
                normals.append(normal / norm)

    return ids, np.array(normals)

def cluster_face_normals(normals: np.ndarray, n_clusters: int = 6) -> np.ndarray:
    """
    Apply PCA + KMeans to group face normals into directional clusters.
    Returns cluster labels for each normal.
    """
    # ✅ Reduce dimensionality for stability
    pca = PCA(n_components=3)
    reduced = pca.fit_transform(normals)

    # ✅ Cluster into directional groups
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
    labels = kmeans.fit_predict(reduced)

    return labels

def assign_cluster_labels(face_ids: List[int], labels: np.ndarray) -> Dict[int, int]:
    """
    Map face IDs to their assigned cluster label.
    """
    return {fid: label for fid, label in zip(face_ids, labels)}

def cluster_faces(faces: List[Dict], n_clusters: int = 6) -> Dict[str, List[int]]:
    """
    Cluster ambiguous faces and return grouped face IDs by cluster index.
    """
    face_ids, normals = extract_normals(faces)
    if len(normals) == 0:
        return {}

    labels = cluster_face_normals(normals, n_clusters=n_clusters)
    mapping = assign_cluster_labels(face_ids, labels)

    # ✅ Group face IDs by cluster index
    clustered = {}
    for fid, label in mapping.items():
        key = f"cluster_{label}"
        clustered.setdefault(key, []).append(fid)

    return clustered




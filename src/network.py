import numpy as np
import pandas as pd
import networkx as nx
import leidenalg
import igraph as ig
from sklearn.metrics.pairwise import cosine_similarity
from scipy.spatial.distance import cdist
from typing import Tuple, Dict, List
from .config import KNN_K, WEAK_BOUNDARY_THRESHOLD, RANDOM_SEED

class NetworkAnalyzer:
    
    @staticmethod
    def compute_mahalanobis_similarity(X: np.ndarray) -> np.ndarray:
        try:
            cov = np.cov(X.T)
            inv_cov = np.linalg.pinv(cov)
            dist = cdist(X, X, metric='mahalanobis', VI=inv_cov)
            return 1 / (1 + dist)
        except Exception as e:
            print(f"Warning: Mahalanobis calculation failed ({e}). Defaulting to Cosine.")
            return cosine_similarity(X)

    @staticmethod
    def build_graph(X: np.ndarray, df_indices: pd.Index, metric: str = 'cosine') -> Tuple[nx.Graph, np.ndarray]:
        if metric == 'cosine':
            sim_matrix = cosine_similarity(X)
        elif metric == 'mahalanobis':
            sim_matrix = NetworkAnalyzer.compute_mahalanobis_similarity(X)
        elif metric == 'euclidean':
            dist = cdist(X, X, metric='euclidean')
            sim_matrix = 1 / (1 + dist)
        else:
            raise ValueError(f"Unknown metric: {metric}")
        
        G = nx.Graph()
        for i in range(len(X)):
            G.add_node(i, dataframe_index=df_indices[i])
            
        for i in range(len(X)):
            neighbors = np.argsort(sim_matrix[i])[-KNN_K-1:-1]
            for j in neighbors:
                weight = sim_matrix[i][j]
                if weight > 0:
                    G.add_edge(i, j, weight=weight)
                    
        return G, sim_matrix

    @staticmethod
    def detect_communities(G: nx.Graph) -> Tuple[Dict[int, int], Dict[int, int], float, float]:
        louvain_coms = nx.community.louvain_communities(G, seed=RANDOM_SEED)
        louvain_map = {node: cid for cid, nodes in enumerate(louvain_coms) for node in nodes}
        mod_louvain = nx.community.modularity(G, louvain_coms)
        
        h = ig.Graph.from_networkx(G)
        leiden_part = leidenalg.find_partition(h, leidenalg.ModularityVertexPartition, seed=RANDOM_SEED)
        leiden_map = {node: leiden_part.membership[i] for i, node in enumerate(G.nodes())}
        mod_leiden = leiden_part.modularity
        
        return louvain_map, leiden_map, mod_louvain, mod_leiden

    @staticmethod
    def find_weak_boundaries(G: nx.Graph, community_map: Dict[int, int]) -> List[Tuple[int, int, float]]:
        weak_boundaries = []
        for u, v, data in G.edges(data=True):
            if community_map[u] != community_map[v]:
                if data.get('weight', 0) > WEAK_BOUNDARY_THRESHOLD:
                    weak_boundaries.append((u, v, data['weight']))
        return weak_boundaries

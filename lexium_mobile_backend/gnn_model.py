import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import HeteroConv, GATConv, Linear
from torch_geometric.data import HeteroData
import numpy as np
from sentence_transformers import SentenceTransformer


def pad_to_768(emb):
    """Pad embedding to 768 dimensions if needed."""
    if emb.shape[1] < 768:
        padding = np.zeros((emb.shape[0], 768 - emb.shape[1]), dtype=np.float32)
        return np.concatenate([emb, padding], axis=1)
    return emb[:, :768]


class LegalHeteroGNN(nn.Module):
    """
    Heterogeneous Graph Attention Network with SINGLE output head
    Handles 10 edge types: 3 forward + 3 reverse + 4 self-loops
    Output: Single GNN score (legal pattern match)
    """

    def __init__(self, node_types, edge_types, hidden_dim=128, num_layers=2, num_heads=4, dropout=0.3):
        super().__init__()

        self.node_types = node_types
        self.edge_types = edge_types
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers

        # Node embeddings
        self.node_embeddings = nn.ModuleDict({
            'document': Linear(768, hidden_dim),
            'statute':  Linear(768, hidden_dim),
            'section':  Linear(768, hidden_dim),
            'claim':    Linear(768, hidden_dim),
        })

        # Layer normalization
        self.layer_norms = nn.ModuleList([
            nn.ModuleDict({node_type: nn.LayerNorm(hidden_dim) for node_type in node_types})
            for _ in range(num_layers)
        ])

        # Graph convolution layers
        self.convs = nn.ModuleList()
        for _ in range(num_layers):
            conv_dict = {}
            for edge_type in edge_types:
                src, rel, dst = edge_type
                is_self_loop = rel.startswith('self_')
                conv_dict[edge_type] = GATConv(
                    (hidden_dim, hidden_dim),
                    hidden_dim // num_heads,
                    heads=num_heads,
                    concat=True,
                    dropout=dropout,
                    add_self_loops=is_self_loop
                )
            self.convs.append(HeteroConv(conv_dict, aggr='mean'))

        # Single output head with Sigmoid
        self.output_head = nn.Sequential(
            Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            Linear(hidden_dim, 1),
            nn.Sigmoid()
        )

        self.dropout = nn.Dropout(dropout)

    def forward(self, data):
        # Initial embeddings
        x_dict = {}
        for node_type in self.node_types:
            if node_type in data.x_dict:
                x_dict[node_type] = self.node_embeddings[node_type](data.x_dict[node_type])

        # Add bidirectional edges
        edge_index_dict = self._add_bidirectional_edges(data.edge_index_dict)

        # Graph convolutions
        for i, conv in enumerate(self.convs):
            x_dict_new = conv(x_dict, edge_index_dict)
            for node_type in x_dict_new:
                x_dict_new[node_type] = F.relu(x_dict_new[node_type])
                x_dict_new[node_type] = self.layer_norms[i][node_type](x_dict_new[node_type])
                x_dict_new[node_type] = self.dropout(x_dict_new[node_type])
            x_dict = x_dict_new

        claim_embeddings = x_dict['claim']
        gnn_score = self.output_head(claim_embeddings)

        return {
            'embeddings': claim_embeddings,
            'gnn_score':  gnn_score
        }

    def _add_bidirectional_edges(self, edge_index_dict):
        new_dict = {}

        device = None
        for edge_type, edge_index in edge_index_dict.items():
            if edge_index.size(1) > 0:
                device = edge_index.device
                break
        if device is None:
            device = torch.device('cpu')

        # Copy original edges
        for edge_type, edge_index in edge_index_dict.items():
            new_dict[edge_type] = edge_index

        # Add reverse edges
        for edge_type, edge_index in edge_index_dict.items():
            src_type, rel, dst_type = edge_type
            reverse_edge = (dst_type, f'rev_{rel}', src_type)
            reversed_index = torch.stack([edge_index[1], edge_index[0]], dim=0)
            new_dict[reverse_edge] = reversed_index

        # Add self-loops
        for node_type in self.node_types:
            self_edge = (node_type, f'self_{node_type}', node_type)
            max_idx = 0
            for edge_type, edge_index in edge_index_dict.items():
                src_type, _, dst_type = edge_type
                if edge_index.size(1) > 0:
                    if src_type == node_type:
                        max_idx = max(max_idx, edge_index[0].max().item())
                    if dst_type == node_type:
                        max_idx = max(max_idx, edge_index[1].max().item())
            if max_idx > 0:
                num_nodes = max_idx + 1
                self_loops = torch.arange(num_nodes, dtype=torch.long, device=device)
                new_dict[self_edge] = torch.stack([self_loops, self_loops], dim=0)

        return new_dict


def load_gnn_model(model_path='models/legal_gnn.pt', device='cpu'):
    """Load the trained GNN model."""
    print(f"Loading GNN model from: {model_path}")

    checkpoint = torch.load(model_path, map_location=device, weights_only=False)

    node_types = checkpoint.get('node_types', ['document', 'statute', 'section', 'claim'])
    edge_types = checkpoint.get('edge_types', [])

    print(f"✅ Loaded checkpoint with {len(edge_types)} edge types")

    model = LegalHeteroGNN(
        node_types=node_types,
        edge_types=edge_types,
        hidden_dim=128,
        num_layers=2,
        num_heads=4,
        dropout=0.3
    )

    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()

    print(f"✅ Model loaded successfully!")
    print(f"   Node types: {node_types}")
    print(f"   Edge types: {len(edge_types)} total")
    print(f"   Output: Single GNN score (0-1)")

    return model, checkpoint


import re

PAT_FULL = re.compile(
    r'(?:Section|Article|§)\s*\d+[A-Za-z]?(?:\([^)]+\))?\s+of\s+(?:the\s+)?'
    r'([A-Z][A-Za-z\s]+?(?:Act|Ordinance|Code|Law))', re.IGNORECASE)
PAT_ACT = re.compile(
    r'\b([A-Z][A-Za-z\s]{3,40}?(?:Act|Ordinance|Code|Law)(?:\s+No\.?\s*\d+)?)\b')
STOPWORDS = {'this act','the act','said act','such act','any act',
             'supreme court','high court','court of appeal'}

def find_statute_indices(claim_text, statute_embeddings, embedder, top_k=3):
    device = statute_embeddings.device
    claim_emb = embedder.encode([claim_text], convert_to_numpy=True)
    claim_emb = pad_to_768(claim_emb)  # ← pad 384 → 768
    claim_emb = torch.FloatTensor(claim_emb).to(device)
    claim_norm = F.normalize(claim_emb, dim=1)
    stat_norm  = F.normalize(statute_embeddings, dim=1)
    sims       = (claim_norm @ stat_norm.T).squeeze(0)
    return sims.topk(min(top_k, statute_embeddings.shape[0])).indices.tolist()

def find_section_indices(claim_text, section_embeddings, embedder, top_k=2):
    device = section_embeddings.device
    claim_emb = embedder.encode([claim_text], convert_to_numpy=True)
    claim_emb = pad_to_768(claim_emb)  # ← pad 384 → 768
    claim_emb = torch.FloatTensor(claim_emb).to(device)
    claim_norm = F.normalize(claim_emb, dim=1)
    sect_norm  = F.normalize(section_embeddings, dim=1)
    sims       = (claim_norm @ sect_norm.T).squeeze(0)
    return sims.topk(min(top_k, section_embeddings.shape[0])).indices.tolist()

class GNNPredictor:
    def __init__(self, model_path='models/legal_gnn.pt'):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model, self.checkpoint = load_gnn_model(model_path, self.device)
        self.model = self.model.to(self.device)
        self.embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

        self.statute_embeddings  = torch.FloatTensor(self.checkpoint['statute_embeddings']).to(self.device)
        self.section_embeddings  = torch.FloatTensor(self.checkpoint['section_embeddings']).to(self.device)
        self.document_embeddings = torch.FloatTensor(self.checkpoint['document_embeddings']).to(self.device)

        print(f"✅ Node embeddings loaded from checkpoint:")
        print(f"   Device: {self.device}")
        print(f"   Statutes:  {self.statute_embeddings.shape}")
        print(f"   Sections:  {self.section_embeddings.shape}")
        print(f"   Documents: {self.document_embeddings.shape}")

    def predict(self, claim_text):
        claim_embedding = self.embedder.encode([claim_text], convert_to_numpy=True)
        claim_embedding = pad_to_768(claim_embedding)

        statute_indices = find_statute_indices(
            claim_text, self.statute_embeddings, self.embedder, top_k=5)
        section_indices = find_section_indices(
            claim_text, self.section_embeddings, self.embedder, top_k=3)

        data = HeteroData()
        data['document'].x = self.document_embeddings
        data['statute'].x  = self.statute_embeddings
        data['section'].x  = self.section_embeddings
        data['claim'].x    = torch.FloatTensor(claim_embedding).to(self.device)

        n_stat = len(statute_indices)
        n_sect = len(section_indices)

        data['claim', 'references', 'statute'].edge_index = torch.LongTensor(
            [[0]*n_stat, statute_indices]).to(self.device)
        data['claim', 'references', 'section'].edge_index = torch.LongTensor(
            [[0]*n_sect, section_indices]).to(self.device)
        data['document', 'cites', 'statute'].edge_index = torch.LongTensor(
            [[0,1,2,3,4],[0,2,4,6,8]]).to(self.device)

        with torch.no_grad():
            output = self.model(data)

        gnn_score = output['gnn_score'][0].item()
        return {'gnn_score': gnn_score, 'overall': gnn_score}


# ── Global predictor (lazy init) ─────────────────────────────────────────────
_PREDICTOR = None


def predict_claim(claim_text):
    """
    Simple function to predict claim validity.

    Usage:
        result = predict_claim("The defendant violated Section 2")
        print(f"GNN Score: {result['gnn_score']:.1%}")

    Returns:
        dict with 'gnn_score' (0-1) and 'overall' (same value)
    """
    global _PREDICTOR

    if _PREDICTOR is None:
        _PREDICTOR = GNNPredictor()

    return _PREDICTOR.predict(claim_text)
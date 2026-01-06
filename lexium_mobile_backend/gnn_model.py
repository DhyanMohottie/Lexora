import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import HeteroConv, GATConv, Linear
from torch_geometric.data import HeteroData
import numpy as np
from sentence_transformers import SentenceTransformer


class LegalHeteroGNN(nn.Module):
    """
    Heterogeneous Graph Attention Network - UPDATED for NEW trained model
    Handles 10 edge types: 3 forward + 3 reverse + 4 self-loops
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
            'statute': Linear(768, hidden_dim),
            'section': Linear(768, hidden_dim),
            'claim': Linear(768, hidden_dim),
        })
        
        # Layer normalization
        self.layer_norms = nn.ModuleList([
            nn.ModuleDict({node_type: nn.LayerNorm(hidden_dim) for node_type in node_types})
            for _ in range(num_layers)
        ])
        
        # Graph convolution layers - BUILD ALL EDGE TYPES
        self.convs = nn.ModuleList()
        for _ in range(num_layers):
            conv_dict = {}
            
            # Add ALL edge types that exist in checkpoint
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
        
        # Output heads
        self.output_heads = nn.ModuleDict({
            'citation_validity': nn.Sequential(
                Linear(hidden_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout),
                Linear(hidden_dim, 1)
            ),
            'relevance_score': nn.Sequential(
                Linear(hidden_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout),
                Linear(hidden_dim, 1)
            ),
            'coherence_score': nn.Sequential(
                Linear(hidden_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout),
                Linear(hidden_dim, 1)
            ),
        })
        
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, data):
        """Forward pass"""
        # Initial embeddings
        x_dict = {}
        for node_type in self.node_types:
            if node_type in data.x_dict:
                x_dict[node_type] = self.node_embeddings[node_type](data.x_dict[node_type])
        
        # Add bidirectional edges (model expects them)
        edge_index_dict = self._add_bidirectional_edges(data.edge_index_dict)
        
        # Graph convolutions
        for i, conv in enumerate(self.convs):
            x_dict_new = conv(x_dict, edge_index_dict)
            
            for node_type in x_dict_new:
                x_dict_new[node_type] = F.relu(x_dict_new[node_type])
                x_dict_new[node_type] = self.layer_norms[i][node_type](x_dict_new[node_type])
                x_dict_new[node_type] = self.dropout(x_dict_new[node_type])
            
            x_dict = x_dict_new
        
        # Get claim embeddings
        claim_embeddings = x_dict['claim']
        
        # Predictions
        outputs = {
            'embeddings': claim_embeddings,
            'validity_scores': torch.sigmoid(self.output_heads['citation_validity'](claim_embeddings)),
            'relevance_scores': torch.sigmoid(self.output_heads['relevance_score'](claim_embeddings)),
            'coherence_scores': torch.sigmoid(self.output_heads['coherence_score'](claim_embeddings)),
        }
        
        return outputs
    
    def _add_bidirectional_edges(self, edge_index_dict):
        """Add reverse edges and self-loops"""
        new_dict = {}
        
        # Get device
        device = None
        for edge_type, edge_index in edge_index_dict.items():
            if edge_index.size(1) > 0:
                device = edge_index.device
                break
        if device is None:
            device = torch.device('cpu')
        
        # Copy original
        for edge_type, edge_index in edge_index_dict.items():
            new_dict[edge_type] = edge_index
        
        # Add reverse
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


def load_gnn_model(model_path='legal_gnn_trained_no_cases.pt', device='cpu'):
    """Load the trained GNN model"""
    print(f"Loading GNN model from: {model_path}")
    
    checkpoint = torch.load(model_path, map_location=device, weights_only=False)
    
    node_types = checkpoint.get('node_types', ['document', 'statute', 'section', 'claim'])
    edge_types = checkpoint.get('edge_types', [])
    
    print(f" Loaded checkpoint with {len(edge_types)} edge types")
    
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
    
    print(f" Model loaded successfully!")
    print(f"   Node types: {node_types}")
    print(f"   Edge types: {len(edge_types)} total")
    
    return model, checkpoint


class GNNPredictor:
    """Easy-to-use predictor for GNN model"""
    
    def __init__(self, model_path='legal_gnn_trained_no_cases.pt'):
        self.device = 'cpu'
        self.model, self.checkpoint = load_gnn_model(model_path, self.device)
        self.embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        
    def predict(self, claim_text):
        """Predict validity of a legal claim"""
        # Generate embedding
        claim_embedding = self.embedder.encode([claim_text], convert_to_numpy=True)
        
        # Pad to 768 dimensions
        if claim_embedding.shape[1] < 768:
            padding = np.zeros((1, 768 - claim_embedding.shape[1]))
            claim_embedding = np.concatenate([claim_embedding, padding], axis=1)
        
        # Create graph structure
        data = HeteroData()
        
        # Add nodes
        data['document'].x = torch.randn(5, 768)
        data['statute'].x = torch.randn(10, 768)
        data['section'].x = torch.randn(5, 768)
        data['claim'].x = torch.FloatTensor(claim_embedding)
        
        # Add edges (only the 3 original - model will add reverse + self-loops)
        data['document', 'cites', 'statute'].edge_index = torch.LongTensor([
            [0, 1, 2, 3, 4],
            [0, 2, 4, 6, 8]
        ])
        
        data['document', 'references', 'section'].edge_index = torch.LongTensor([
            [0, 1, 2],
            [0, 2, 4]
        ])
        
        data['claim', 'references', 'statute'].edge_index = torch.LongTensor([
            [0, 0, 0],
            [0, 1, 2]
        ])
        
        # Run inference
        with torch.no_grad():
            output = self.model(data)
        
        # Extract scores
        result = {
            'validity': output['validity_scores'][0].item(),
            'relevance': output['relevance_scores'][0].item(),
            'coherence': output['coherence_scores'][0].item(),
            'overall': (
                output['validity_scores'][0].item() +
                output['relevance_scores'][0].item() +
                output['coherence_scores'][0].item()
            ) / 3
        }
        
        return result


# Global predictor
_PREDICTOR = None

def predict_claim(claim_text):
    """
    Simple function to predict claim validity
    
    Usage:
        result = predict_claim("The defendant violated Section 2")
        print(result['overall'])
    """
    global _PREDICTOR
    
    if _PREDICTOR is None:
        _PREDICTOR = GNNPredictor()
    
    return _PREDICTOR.predict(claim_text)



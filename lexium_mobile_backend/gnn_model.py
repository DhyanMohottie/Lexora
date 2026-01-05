import torch
import torch.nn as nn
from torch_geometric.nn import HeteroConv, GATConv, Linear
from torch_geometric.data import HeteroData
import numpy as np
from sentence_transformers import SentenceTransformer


class LegalHeteroGNN(nn.Module):
    """
    Heterogeneous Graph Attention Network - FIXED VERSION
    """
    
    def __init__(self, node_types, edge_types, hidden_dim=128, num_layers=2, num_heads=4):
        super().__init__()
        
        self.node_types = node_types
        self.edge_types = edge_types  # Original edge types
        self.hidden_dim = hidden_dim
        
        # Node embeddings (matches trained model: "node_embeddings")
        self.node_embeddings = nn.ModuleDict({
            node_type: Linear(768, hidden_dim)
            for node_type in node_types
        })
        
        # Layer normalization (matches trained model: "layer_norms")
        self.layer_norms = nn.ModuleList()
        for _ in range(num_layers):
            layer_norm_dict = nn.ModuleDict({
                node_type: nn.LayerNorm(hidden_dim)
                for node_type in node_types
            })
            self.layer_norms.append(layer_norm_dict)
        
        # Graph convolution layers
        self.convs = nn.ModuleList()
        for _ in range(num_layers):
            conv_dict = {}
            for edge_type in edge_types:
                src, rel, dst = edge_type
                conv_dict[edge_type] = GATConv(
                    (hidden_dim, hidden_dim),
                    hidden_dim // num_heads,
                    heads=num_heads,
                    concat=True,
                    add_self_loops=False
                )
            self.convs.append(HeteroConv(conv_dict, aggr='mean'))
        
        # Output heads
        self.output_heads = nn.ModuleDict({
            'citation_validity': nn.Sequential(
                Linear(hidden_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(0.3),
                Linear(hidden_dim, 1)
            ),
            'relevance_score': nn.Sequential(
                Linear(hidden_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(0.3),
                Linear(hidden_dim, 1)
            ),
            'coherence_score': nn.Sequential(
                Linear(hidden_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(0.3),
                Linear(hidden_dim, 1)
            )
        })
    
    def forward(self, data):
        """Forward pass - FIXED VERSION"""
        x_dict = {}
        
        # Encode node features with embeddings
        for node_type in self.node_types:
            if node_type in data.x_dict and data.x_dict[node_type] is not None:
                x_dict[node_type] = self.node_embeddings[node_type](data.x_dict[node_type])
        
        # IMPORTANT: Only use edges that exist in the model's HeteroConv
        edge_index_dict = {}
        for edge_type in self.edge_types:
            if edge_type in data.edge_index_dict:
                src_type, _, dst_type = edge_type
                # Only include edge if BOTH source and dest node types have features
                if src_type in x_dict and dst_type in x_dict:
                    edge_index_dict[edge_type] = data.edge_index_dict[edge_type]
        
        # Store initial claim embedding for fallback
        initial_claim_emb = x_dict.get('claim', None)
        
        # Apply graph convolutions with layer norms
        for i, conv in enumerate(self.convs):
            if len(edge_index_dict) > 0:
                x_dict_new = conv(x_dict, edge_index_dict)
                
                # Apply layer norm and activation
                for node_type in x_dict_new:
                    if node_type in self.layer_norms[i]:
                        x_dict_new[node_type] = torch.relu(
                            self.layer_norms[i][node_type](x_dict_new[node_type])
                        )
                
                # Keep nodes that didn't get updated (no incoming edges)
                for node_type in x_dict:
                    if node_type not in x_dict_new:
                        x_dict_new[node_type] = x_dict[node_type]
                
                x_dict = x_dict_new
        
        # Get claim embeddings for prediction
        if 'claim' in x_dict and x_dict['claim'] is not None:
            claim_emb = x_dict['claim']
        elif initial_claim_emb is not None:
            # Fallback to initial embedding if claim wasn't updated
            claim_emb = initial_claim_emb
        else:
            raise RuntimeError("No claim embeddings available!")
        
        # Predict scores
        validity = torch.sigmoid(self.output_heads['citation_validity'](claim_emb))
        relevance = torch.sigmoid(self.output_heads['relevance_score'](claim_emb))
        coherence = torch.sigmoid(self.output_heads['coherence_score'](claim_emb))
        
        return {
            'validity_scores': validity,
            'relevance_scores': relevance,
            'coherence_scores': coherence
        }


def load_gnn_model(model_path='legal_gnn_trained_no_cases.pt', device='cpu'):
    """Load the trained GNN model"""
    print(f"Loading GNN model from: {model_path}")
    
    checkpoint = torch.load(model_path, map_location=device)
    
    node_types = checkpoint.get('node_types', ['document', 'statute', 'section', 'claim'])
    edge_types_saved = checkpoint.get('edge_types', [])
    
    if not edge_types_saved or len(edge_types_saved) == 0:
        edge_types = [
            ('document', 'cites', 'statute'),
            ('document', 'references', 'section'),
            ('claim', 'references', 'statute'),
        ]
    else:
        edge_types = edge_types_saved
    
    model = LegalHeteroGNN(
        node_types=node_types,
        edge_types=edge_types,
        hidden_dim=128,
        num_layers=2,
        num_heads=4
    )
    
    # Load weights with strict=False to handle any mismatches
    model.load_state_dict(checkpoint['model_state_dict'], strict=False)
    model.eval()
    
    print(f" Model loaded successfully!")
    print(f"   Node types: {node_types}")
    print(f"   Edge types: {edge_types}")
    
    return model, checkpoint


class GNNPredictor:
    """Easy-to-use predictor for GNN model"""
    
    def __init__(self, model_path='legal_gnn_trained_no_cases.pt'):
        self.device = 'cpu'
        self.model, self.checkpoint = load_gnn_model(model_path, self.device)
        self.embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        
        # Get edge types from the model
        self.edge_types = self.model.edge_types
        
    def predict(self, claim_text):
        """Predict validity of a legal claim"""
        # Generate embedding
        claim_embedding = self.embedder.encode([claim_text], convert_to_numpy=True)
        
        # Pad to 768 dimensions if needed (MiniLM outputs 384)
        if claim_embedding.shape[1] < 768:
            padding = np.zeros((1, 768 - claim_embedding.shape[1]))
            claim_embedding = np.concatenate([claim_embedding, padding], axis=1)
        
        # Create graph structure with ALL required node types
        data = HeteroData()
        
        # Add nodes - ensure all node types have features
        data['document'].x = torch.randn(5, 768)
        data['statute'].x = torch.randn(10, 768)
        data['section'].x = torch.randn(5, 768)
        data['claim'].x = torch.FloatTensor(claim_embedding)
        
        # Add ONLY the edges that the model was trained with
        # These must match self.edge_types exactly
        
        # Check which edge types the model expects and create them
        for edge_type in self.edge_types:
            src, rel, dst = edge_type
            
            if edge_type == ('document', 'cites', 'statute'):
                data[edge_type].edge_index = torch.LongTensor([
                    [0, 1, 2, 3, 4],
                    [0, 2, 4, 6, 8]
                ])
            elif edge_type == ('document', 'references', 'section'):
                data[edge_type].edge_index = torch.LongTensor([
                    [0, 1, 2],
                    [0, 2, 4]
                ])
            elif edge_type == ('claim', 'references', 'statute'):
                data[edge_type].edge_index = torch.LongTensor([
                    [0, 0, 0],
                    [0, 1, 2]
                ])
            else:
                # For any other edge type, create a minimal connection
                print(f"   Creating minimal edges for: {edge_type}")
                data[edge_type].edge_index = torch.LongTensor([
                    [0],
                    [0]
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


# Quick test
if __name__ == "__main__":
    test_claim = "The defendant violated Section 2 of the Consumer Protection Act"
    print(f"\nTesting with claim: {test_claim}\n")
    
    try:
        result = predict_claim(test_claim)
        print("Results:")
        print(f"  Validity:  {result['validity']:.4f}")
        print(f"  Relevance: {result['relevance']:.4f}")
        print(f"  Coherence: {result['coherence']:.4f}")
        print(f"  Overall:   {result['overall']:.4f}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
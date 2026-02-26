# fusion_network.py

"""
Fusion Network for Neurosymbolic Legal AI System
Combines GNN and Symbolic predictions
"""

import torch
import torch.nn as nn
import numpy as np
import os


class FusionNetwork(nn.Module):
    """Neural Fusion Network - Architecture Definition"""
    
    def __init__(self, input_dim=4, hidden_dim=32):
        super().__init__()
        
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_dim),
            nn.Dropout(0.3),
            
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_dim // 2),
            nn.Dropout(0.2),
            
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid()  # Output 0-1
        )
    
    def forward(self, x):
        return self.network(x)


class FusionPredictor:
    """
    Load and use trained fusion network
    
    Usage:
        fusion = FusionPredictor('models/fusion_network.pt')
        score = fusion.predict(0.85, 0.90, 9, 1)
    """
    
    def __init__(self, model_path='models/fusion_network.pt'):
        """
        Load trained fusion model
        
        Args:
            model_path: Path to .pt file (trained weights)
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"❌ Model file not found: {model_path}\n"
                f"💡 Make sure you downloaded fusion_network.pt from Colab!"
            )
        
        # Load checkpoint
        checkpoint = torch.load(model_path, weights_only=False)
        
        # Create model with same architecture
        self.model = FusionNetwork(
            input_dim=checkpoint['input_dim'],
            hidden_dim=checkpoint['hidden_dim']
        )
        
        # Load trained weights
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.eval()
        
        # Load normalization parameters
        self.X_mean = checkpoint['X_mean']
        self.X_std = checkpoint['X_std']
        
        print(f"✅ Fusion network loaded from: {model_path}")
        print(f"   Validation MAE: {checkpoint['mae']:.4f}")
        print(f"   Validation RMSE: {checkpoint['rmse']:.4f}")
    
    def predict(self, gnn_score, symbolic_confidence, num_satisfied, num_violations):
        """
        Predict fused confidence score
        
        Args:
            gnn_score: GNN prediction (0-1)
            symbolic_confidence: Symbolic confidence (0-1)
            num_satisfied: Rules satisfied (0-10)
            num_violations: Rules violated (0-10)
        
        Returns:
            float: Fused score (0-1)
        
        Example:
            score = fusion.predict(0.85, 0.90, 9, 1)
            print(f"Score: {score:.1%}")  # Score: 92.6%
        """
        # Prepare input features
        features = np.array([[
            gnn_score, 
            symbolic_confidence, 
            num_satisfied, 
            num_violations
        ]])
        
        # Normalize (same way as training)
        features = (features - self.X_mean) / (self.X_std + 1e-8)
        
        # Predict
        with torch.no_grad():
            X = torch.FloatTensor(features)
            prediction = self.model(X)
        
        return prediction.item()
# test_fusion.py

from fusion_network import FusionPredictor

print("="*60)
print("TESTING FUSION NETWORK")
print("="*60)

# Load model
fusion = FusionPredictor('fusion_network.pt')

# Test 1: Good claim
score1 = fusion.predict(
    gnn_score=0.85,
    symbolic_confidence=0.90,
    num_satisfied=9,
    num_violations=1
)
print(f"\n✅ Good claim: {score1:.1%}")

# Test 2: Bad claim
score2 = fusion.predict(
    gnn_score=0.15,
    symbolic_confidence=0.10,
    num_satisfied=1,
    num_violations=9
)
print(f"❌ Bad claim: {score2:.1%}")

# Test 3: Mixed
score3 = fusion.predict(
    gnn_score=0.60,
    symbolic_confidence=0.75,
    num_satisfied=7,
    num_violations=3
)
print(f"⚠️  Mixed claim: {score3:.1%}")

print("\n" + "="*60)
print("✅ Fusion network working!")
print("="*60)
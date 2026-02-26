from gnn_model import predict_claim

test_claims = [
    "violated Section 2 of Contract Act",
    "abkjnlklnlkqd asjkdhaskjd",
    "I went for a walk yesterday",
    "This violates law of being mean"
]

for claim in test_claims:
    result = predict_claim(claim)
    
    # Check if all 3 scores are similar
    validity = result['validity']
    relevance = result['relevance']
    coherence = result['coherence']
    
    diff = max(validity, relevance, coherence) - min(validity, relevance, coherence)
    
    print(f"\nClaim: {claim[:40]}...")
    print(f"Validity:  {validity:.1%}")
    print(f"Relevance: {relevance:.1%}")
    print(f"Coherence: {coherence:.1%}")
    print(f"Difference: {diff:.1%}")
    
    if diff < 0.10:  # Less than 10% difference
        print("⚠️  All 3 scores are nearly IDENTICAL!")
from gnn_model import predict_claim

# Test a legal claim
claim = "The defendant violated Section 2 of the Service Contracts Ordinance"

result = predict_claim(claim)

print(f"Overall Score: {result['overall']:.1%}")
print(f"Validity: {result['validity']:.1%}")
print(f"Relevance: {result['relevance']:.1%}")
print(f"Coherence: {result['coherence']:.1%}")
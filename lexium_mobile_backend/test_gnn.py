from gnn_model import predict_claim

claim = "The defendant violated Section 152 of the Motor Traffic Act by failing to exercise reasonable duty of care while operating a motor vehicle, resulting in damages to the plaintiff's property"


result = predict_claim(claim)

print(f"GNN Score: {result['gnn_score']:.1%}")
print(f"Overall: {result['overall']:.1%}")
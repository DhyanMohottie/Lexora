from symbolic_reasoning_system import validate_claim

# Test with statutes in  CSV
test_claims = [
    # Using "Ordinance" 
    "The defendant violated Section 2 of the Service Contracts Ordinance as established in precedent",
    
    # Using "Act" 
    "The plaintiff's claim under the Bribery Act and Section 10 is well-founded",
    
    # Multiple citations 
    "Based on the Animals Act and Section 4, the court must rule in favor",
]

for i, claim in enumerate(test_claims, 1):
    print(f"\n{'='*70}")
    print(f"Test {i}: {claim}")
    print('='*70)
    
    result = validate_claim(claim)
    
    print(f"Score: {result.confidence:.1%}")
    print(f"Valid: {result.is_valid}")
    print(f"Passed: {len(result.satisfied_rules)}/10 rules")
    print()
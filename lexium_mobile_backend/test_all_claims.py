# test_all_claims.py

from gnn_model import predict_claim
import pandas as pd

# =============================================================================
# TEST CLAIMS DATABASE
# =============================================================================

test_claims = [
    # =========================================================================
    # CATEGORY 1: HIGH VALIDITY (80-95%) - Well-formed legal claims
    # =========================================================================
    {
        "id": 1,
        "category": "High Validity",
        "claim": "The defendant violated Section 152 of the Motor Traffic Act by failing to exercise reasonable duty of care while operating a motor vehicle, resulting in damages to the plaintiff's property.",
        "expected_validity": "90-95%",
        "expected_relevance": "88-92%",
        "expected_coherence": "90-95%"
    },
    {
        "id": 2,
        "category": "High Validity",
        "claim": "Plaintiff alleges breach of contract under Section 2 of the Service Contracts Ordinance, as the defendant failed to fulfill agreed upon terms specified in the written agreement dated January 15, 2024.",
        "expected_validity": "85-92%",
        "expected_relevance": "88-93%",
        "expected_coherence": "85-90%"
    },
    {
        "id": 3,
        "category": "High Validity",
        "claim": "The respondent contravened Section 4 of the Animals Act by failing to secure their domestic animal, which subsequently caused injury to the complainant on public property.",
        "expected_validity": "85-90%",
        "expected_relevance": "85-90%",
        "expected_coherence": "88-92%"
    },
    {
        "id": 4,
        "category": "High Validity",
        "claim": "Under Section 10 of the Bribery Act and pursuant to established case law, the accused solicited unlawful gratification from a public official in violation of anti-corruption statutes.",
        "expected_validity": "88-93%",
        "expected_relevance": "90-95%",
        "expected_coherence": "87-92%"
    },
    {
        "id": 5,
        "category": "High Validity",
        "claim": "The plaintiff invokes Section 68 of the Civil Law Ordinance regarding negligence, asserting that the defendant's failure to maintain their property resulted in foreseeable harm to neighboring residents.",
        "expected_validity": "86-91%",
        "expected_relevance": "84-89%",
        "expected_coherence": "88-93%"
    },
    
    # =========================================================================
    # CATEGORY 2: MEDIUM VALIDITY (60-75%) - Missing elements
    # =========================================================================
    {
        "id": 6,
        "category": "Medium Validity",
        "claim": "The party may have violated traffic regulations when the incident occurred last month on Galle Road.",
        "expected_validity": "65-72%",
        "expected_relevance": "60-67%",
        "expected_coherence": "68-75%"
    },
    {
        "id": 7,
        "category": "Medium Validity",
        "claim": "There could be a contractual dispute under relevant statutes because the agreement was not honored as expected.",
        "expected_validity": "62-68%",
        "expected_relevance": "64-70%",
        "expected_coherence": "63-68%"
    },
    {
        "id": 8,
        "category": "Medium Validity",
        "claim": "Based on the Animals Act, damages are claimed for the incident involving the neighbor's dog.",
        "expected_validity": "68-74%",
        "expected_relevance": "70-76%",
        "expected_coherence": "67-72%"
    },
    {
        "id": 9,
        "category": "Medium Validity",
        "claim": "The defendant violated Section 2 but failed to provide adequate compensation.",
        "expected_validity": "60-66%",
        "expected_relevance": "58-64%",
        "expected_coherence": "64-69%"
    },
    {
        "id": 10,
        "category": "Medium Validity",
        "claim": "Pursuant to legal requirements, the respondent did not comply with standard procedures during the transaction.",
        "expected_validity": "64-70%",
        "expected_relevance": "63-69%",
        "expected_coherence": "68-73%"
    },
    
    # =========================================================================
    # CATEGORY 3: LOW VALIDITY (20-40%) - No legal basis
    # =========================================================================
    {
        "id": 11,
        "category": "Low Validity",
        "claim": "I think someone did something wrong and they should be punished for it.",
        "expected_validity": "25-32%",
        "expected_relevance": "20-27%",
        "expected_coherence": "28-35%"
    },
    {
        "id": 12,
        "category": "Low Validity",
        "claim": "The defendant is guilty because everyone knows what they did was illegal.",
        "expected_validity": "22-28%",
        "expected_relevance": "24-30%",
        "expected_coherence": "22-28%"
    },
    {
        "id": 13,
        "category": "Low Validity",
        "claim": "This violates the law of being mean and causing problems for other people.",
        "expected_validity": "15-22%",
        "expected_relevance": "13-19%",
        "expected_coherence": "18-24%"
    },
    {
        "id": 14,
        "category": "Low Validity",
        "claim": "My neighbor's actions are wrong and I want justice immediately.",
        "expected_validity": "20-26%",
        "expected_relevance": "17-23%",
        "expected_coherence": "23-29%"
    },
    {
        "id": 15,
        "category": "Low Validity",
        "claim": "They broke the rules and must face consequences under proper authorities.",
        "expected_validity": "28-35%",
        "expected_relevance": "26-32%",
        "expected_coherence": "30-37%"
    },
    
    # =========================================================================
    # CATEGORY 4: GIBBERISH/NON-LEGAL (5-15%)
    # =========================================================================
    {
        "id": 16,
        "category": "Gibberish",
        "claim": "abkjnlklnlkqd asjkdhaskjd qwoieuqowie asdjhasjkdh",
        "expected_validity": "5-12%",
        "expected_relevance": "3-10%",
        "expected_coherence": "5-12%"
    },
    {
        "id": 17,
        "category": "Non-Legal",
        "claim": "I went for a walk yesterday and bought some groceries at the store.",
        "expected_validity": "10-16%",
        "expected_relevance": "8-14%",
        "expected_coherence": "70-85%"  # High coherence! Good grammar!
    },
    {
        "id": 18,
        "category": "Non-Legal",
        "claim": "The weather is nice today so I decided to drink some water.",
        "expected_validity": "7-13%",
        "expected_relevance": "6-12%",
        "expected_coherence": "72-87%"  # High coherence! Good grammar!
    },
    
    # =========================================================================
    # CATEGORY 5: WORD ORDER TESTS
    # =========================================================================
    {
        "id": 19,
        "category": "Word Order - Intact Phrases",
        "claim": "duty care Section 2 Act violated Motor Traffic defendant",
        "expected_validity": "68-75%",
        "expected_relevance": "60-68%",
        "expected_coherence": "68-75%"
    },
    {
        "id": 20,
        "category": "Word Order - Partial Order",
        "claim": "defendant Act 2 violated Motor Section duty Traffic care",
        "expected_validity": "70-77%",
        "expected_relevance": "72-78%",
        "expected_coherence": "68-75%"
    },
    {
        "id": 21,
        "category": "Word Order - Complete Scramble",
        "claim": "Section Motor violated 2 defendant Act duty Traffic care",
        "expected_validity": "24-31%",
        "expected_relevance": "25-32%",
        "expected_coherence": "26-33%"
    },
    
    # =========================================================================
    # CATEGORY 6: EDGE CASES
    # =========================================================================
    {
        "id": 22,
        "category": "Edge Case - Hallucinated Citation",
        "claim": "The defendant violated Section 999 of the Fictitious Legal Act regarding imaginary violations that never occurred.",
        "expected_validity": "10-20%",  # Fake section!
        "expected_relevance": "35-45%",
        "expected_coherence": "40-50%"
    },
    {
        "id": 23,
        "category": "Edge Case - Over-Complex",
        "claim": "Under the Contract Act and Tort Law principles, combined with Section 5 and Section 10, the party's actions constitute multiple violations requiring comprehensive legal review.",
        "expected_validity": "54-62%",
        "expected_relevance": "58-66%",
        "expected_coherence": "50-58%"
    },
    {
        "id": 24,
        "category": "Edge Case - Good Grammar, No Legal Basis",
        "claim": "The defendant clearly demonstrated a pattern of misconduct that violated fundamental principles of justice and fairness throughout the entire proceedings.",
        "expected_validity": "20-28%",
        "expected_relevance": "35-43%",
        "expected_coherence": "88-95%"  # Excellent grammar!
    },
    {
        "id": 25,
        "category": "Edge Case - Valid Citation, Wrong Context",
        "claim": "The defendant violated Section 152 of Motor Traffic Act when preparing their birthday cake last evening.",
        "expected_validity": "78-86%",  # Valid citation!
        "expected_relevance": "15-23%",  # Wrong context!
        "expected_coherence": "65-73%"
    }
]

# =============================================================================
# TEST EXECUTION
# =============================================================================

def run_all_tests():
    """Run all test claims and display results"""
    
    print("=" * 80)
    print("LEGAL AI SYSTEM - COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    print(f"\nTotal Claims to Test: {len(test_claims)}\n")
    
    results = []
    
    for test in test_claims:
        print(f"\n{'='*80}")
        print(f"TEST #{test['id']}: {test['category']}")
        print(f"{'='*80}")
        print(f"\nClaim:\n  \"{test['claim']}\"\n")
        print(f"Expected Scores:")
        print(f"  Validity:   {test['expected_validity']}")
        print(f"  Relevance:  {test['expected_relevance']}")
        print(f"  Coherence:  {test['expected_coherence']}")
        
        # Predict
        try:
            result = predict_claim(test['claim'])
            
            print(f"\nActual Scores:")
            print(f"  Overall:    {result['overall']:.1%}")
            print(f"  Validity:   {result['validity']:.1%}")
            print(f"  Relevance:  {result['relevance']:.1%}")
            print(f"  Coherence:  {result['coherence']:.1%}")
            
            # Store results
            results.append({
                'id': test['id'],
                'category': test['category'],
                'claim': test['claim'][:50] + "...",  # Truncate for display
                'overall': result['overall'],
                'validity': result['validity'],
                'relevance': result['relevance'],
                'coherence': result['coherence'],
                'expected_validity': test['expected_validity'],
                'expected_relevance': test['expected_relevance'],
                'expected_coherence': test['expected_coherence']
            })
            
        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            results.append({
                'id': test['id'],
                'category': test['category'],
                'claim': test['claim'][:50] + "...",
                'overall': 0,
                'validity': 0,
                'relevance': 0,
                'coherence': 0,
                'error': str(e)
            })
    
    # Convert to DataFrame
    df = pd.DataFrame(results)
    
    # Summary Statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    
    print("\n📊 By Category:")
    summary = df.groupby('category')[['overall', 'validity', 'relevance', 'coherence']].mean()
    print(summary.to_string())
    
    print("\n\n📈 Overall Statistics:")
    print(f"Average Overall Score:  {df['overall'].mean():.1%}")
    print(f"Average Validity:       {df['validity'].mean():.1%}")
    print(f"Average Relevance:      {df['relevance'].mean():.1%}")
    print(f"Average Coherence:      {df['coherence'].mean():.1%}")
    
    print(f"\nStd Dev Overall:        {df['overall'].std():.1%}")
    print(f"Std Dev Validity:       {df['validity'].std():.1%}")
    print(f"Std Dev Relevance:      {df['relevance'].std():.1%}")
    print(f"Std Dev Coherence:      {df['coherence'].std():.1%}")
    
    # Save to CSV
    df.to_csv('test_results.csv', index=False)
    print("\n✅ Results saved to: test_results.csv")
    
    return df


# =============================================================================
# CATEGORY-SPECIFIC TESTS
# =============================================================================

def test_high_validity():
    """Test only high validity claims"""
    high_validity_claims = [c for c in test_claims if c['category'] == 'High Validity']
    
    print("\n🔍 Testing High Validity Claims Only...\n")
    for test in high_validity_claims:
        result = predict_claim(test['claim'])
        print(f"Claim #{test['id']}: {result['overall']:.1%}")

def test_word_order():
    """Test word order sensitivity"""
    word_order_claims = [c for c in test_claims if 'Word Order' in c['category']]
    
    print("\n🔍 Testing Word Order Sensitivity...\n")
    for test in word_order_claims:
        result = predict_claim(test['claim'])
        print(f"{test['category']}: {result['coherence']:.1%}")

def test_edge_cases():
    """Test edge cases"""
    edge_cases = [c for c in test_claims if 'Edge Case' in c['category']]
    
    print("\n🔍 Testing Edge Cases...\n")
    for test in edge_cases:
        result = predict_claim(test['claim'])
        print(f"\nClaim: {test['claim'][:60]}...")
        print(f"Validity: {result['validity']:.1%}, Relevance: {result['relevance']:.1%}, Coherence: {result['coherence']:.1%}")


# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Run specific test category
        category = sys.argv[1].lower()
        
        if category == 'high':
            test_high_validity()
        elif category == 'word':
            test_word_order()
        elif category == 'edge':
            test_edge_cases()
        else:
            print(f"Unknown category: {category}")
            print("Available: high, word, edge")
    else:
        # Run all tests
        df = run_all_tests()
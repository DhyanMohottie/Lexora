from symbolic_reasoning_system import validate_claim

# Send your message
message = "The defendant violated Section 2 of the Contract Act"
result = validate_claim(message)

# See results
print(f"Score: {result.confidence:.1%}")
print(f"Valid: {result.is_valid}")
print(result.explanation)
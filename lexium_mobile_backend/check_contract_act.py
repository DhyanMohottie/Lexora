from symbolic_reasoning_system import get_system

system = get_system()

# Check if "Contract Act" is in the valid statutes
print("Checking for 'Contract Act'...")
print(f"Is 'Contract Act' valid? {system.knowledge_base.is_valid_statute('Contract Act')}")

# Show all statutes that contain "Contract"
print("\nStatutes containing 'Contract':")
contract_statutes = [s for s in system.knowledge_base.valid_statutes if 'Contract' in s or 'contract' in s]
print(f"Found {len(contract_statutes)} statutes")
for s in contract_statutes[:10]:
    print(f"  - {s}")

# Show all statutes that contain "Act"
print("\nStatutes containing 'Act' (first 20):")
act_statutes = [s for s in system.knowledge_base.valid_statutes if 'Act' in s]
for s in act_statutes[:20]:
    print(f"  - {s}")
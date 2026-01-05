import torch

print("=" * 70)
print("INSPECTING TRAINED MODEL CHECKPOINT")
print("=" * 70)

# Load checkpoint
checkpoint = torch.load('legal_gnn_trained_no_cases.pt', map_location='cpu')

print("\n1. Checkpoint keys:")
for key in checkpoint.keys():
    print(f"   - {key}")

print("\n2. Node types:")
if 'node_types' in checkpoint:
    print(f"   {checkpoint['node_types']}")
else:
    print("   Not found in checkpoint")

print("\n3. Edge types in model:")
edge_types = set()
for key in checkpoint['model_state_dict'].keys():
    if 'convs.0.convs.<' in key:
        # Extract edge type: convs.0.convs.<edge_type>.att_src
        start = key.find('<') + 1
        end = key.find('>')
        edge_type_str = key[start:end]
        edge_types.add(edge_type_str)

print(f"\n   Found {len(edge_types)} edge types:")
for et in sorted(edge_types):
    # Parse the edge type
    parts = et.split('___')
    if len(parts) == 3:
        src, rel, dst = parts
        print(f"   - ('{src}', '{rel}', '{dst}')")

print("\n4. Output head structure:")
for key in checkpoint['model_state_dict'].keys():
    if 'output_heads' in key and '.weight' in key:
        shape = checkpoint['model_state_dict'][key].shape
        print(f"   {key}: {shape}")

print("\n5. Node embedding structure:")
for key in list(checkpoint['model_state_dict'].keys())[:20]:
    if 'node_' in key:
        print(f"   {key}")

print("\n" + "=" * 70)
print("GENERATING CORRECT CODE")
print("=" * 70)

print("\nEdge types to use in code:")
print("edge_types = [")
for et in sorted(edge_types):
    parts = et.split('___')
    if len(parts) == 3:
        src, rel, dst = parts
        print(f"    ('{src}', '{rel}', '{dst}'),")
print("]")
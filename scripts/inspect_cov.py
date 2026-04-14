import numpy as np

# Load the file
path = "data/desy5/current/STAT+SYS.npz"
data = np.load(path, allow_pickle=True)

print("Keys in file:", list(data.keys()))

# Check nsn
if 'nsn' in data:
    print("Number of Supernovae (nsn):", data['nsn'])

# Inspect the 'cov' array
if 'cov' in data:
    cov_array = data['cov']
    print("\n'cov' array shape:", cov_array.shape)
    print("'cov' array first 5 values:", cov_array[:5])
    
    # Heuristic to see if it's already inverted
    avg_val = np.mean(np.abs(cov_array))
    print(f"Average absolute value: {avg_val:.6f}")
    
    if avg_val < 1:
        print("RESULT: These look like COVARIANCE values (needs inverting).")
    else:
        print("RESULT: These look like INVERSE values (do NOT invert again).")

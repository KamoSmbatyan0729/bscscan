import random

# Read words from mnemonic.txt
with open("mnemonic.txt", "r", encoding="utf-8") as f:
    words = f.read().strip().split()

N_RANDOM = 5000  # Number of unique shuffles

output_file = "random_unique_shuffles.txt"
seen = set()

with open(output_file, "w", encoding="utf-8") as f:
    while len(seen) < N_RANDOM:
        temp = words[:]
        random.shuffle(temp)
        phrase = " ".join(temp)
        if phrase not in seen:
            seen.add(phrase)
            f.write(phrase + "\n")

print(f"✅ Done! {len(seen)} unique shuffles saved to {output_file}")

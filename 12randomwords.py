import random
import requests

# URL of the official BIP-39 English wordlist
url = "https://raw.githubusercontent.com/bitcoin/bips/master/bip-0039/english.txt"

# Fetch the wordlist
response = requests.get(url)
wordlist = response.text.splitlines()

# Pick 12 random words
mnemonic = random.sample(wordlist, 12)

# Save to file
with open("mnemonic.txt", "w") as f:
    f.write(" ".join(mnemonic))
print("✅ Done! 12 random words saved to mnemonic.txt")
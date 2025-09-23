from itertools import product
import random
import string
from web3 import Web3

special_letters = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','1','2','3','4','5','6','7','8','9','0',
                   'u','v','w','x','y','z', 'A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T',
                   'U','V','W','X','Y','Z',' ']

# WARNING: This will generate a *huge* number of combinations (len(special_letters)^60)
# It's only feasible for much smaller lengths.
def abi_encode_string_solidity_style(s: str) -> bytes:
    b = s.encode('utf-8')
    length = len(b)
    padded_len = ((length + 31) // 32) * 32

    offset = (32).to_bytes(32, byteorder='big')         # offset to data
    length_encoded = length.to_bytes(32, byteorder='big')
    padded_bytes = b + b'\x00' * (padded_len - length)

    return offset + length_encoded + padded_bytes

def hash_response(response_str: str) -> str:
    encoded = abi_encode_string_solidity_style(response_str)
    return Web3.keccak(encoded).hex()

length = 8

#target_hash = "527a3e852c67b61aac552b4d372026f34b48c9afe366e76b6c6fa9d1ebb871e3"
target_hash1 = "f152950bed091c9854229d3eecb07fae4c84127704751a692c8409543dc02bd3"
target_hash = "c6e5681654327524e821b1cccc8fd4bc351f70fc25b1f4830f971441f0ed4d4e"

for candidate in product(special_letters, repeat=length):
    string = ''.join(candidate)
    print(string)
    hash = hash_response(string)
    print(hash)
    if hash == target_hash or hash == target_hash1:
        print("Found match:", s)
        with open("funded_candidate.txt", "a") as f:
            f.write("🚨 FUNDED WALLET FOUND 🚨\n")
            f.write(f"candidate: {string}\n")
            f.write("=" * 40 + "\n")
        break
    # Here you can compute hash or check your condition

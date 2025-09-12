import random
import string
from web3 import Web3

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

target_hash = "527a3e852c67b61aac552b4d372026f34b48c9afe366e76b6c6fa9d1ebb871e3"
target_hash1 = "f152950bed091c9854229d3eecb07fae4c84127704751a692c8409543dc02bd3"

while(1):
    candidate = ''.join(random.choices(string.printable.strip(), k=random.randint(1, 60)))
    print(candidate)
    hash = hash_response(candidate)
    print(hash)
    if hash == target_hash or hash == target_hash1:
        print("Found match:", candidate)
        with open("funded_candidate.txt", "a") as f:
            f.write("🚨 FUNDED WALLET FOUND 🚨\n")
            f.write(f"candidate: {candidate}\n")
            f.write("=" * 40 + "\n")
        break
#0x342d77f13Da625B46e42764B80004702c817f770
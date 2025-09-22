import time
import base58
import requests
from mnemonic import Mnemonic
from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes
from web3 import Web3

# -------------------- CONFIG --------------------
SCAN_ACCOUNTS = 3  # Accounts per mnemonic

# RPC URLs
BSC_RPC = "https://bsc-dataseed.binance.org/"
TRON_API = "https://api.trongrid.io"  # Mainnet API

# Web3 connections
web3_bsc = Web3(Web3.HTTPProvider(BSC_RPC))

mnemo = Mnemonic("english")
count = 0

# ------------------ FUNCTIONS ------------------
def get_bnb_balance(address):
    try:
        balance_wei = web3_bsc.eth.get_balance(address)
        return web3_bsc.from_wei(balance_wei, 'ether')
    except Exception as e:
        print(f"⚠️ BSC balance error: {e}")
        return 0

def eth_to_tron_address(address):
    """Convert ETH-style address (0x...) to TRON Base58Check address (starts with T)"""
    # Remove "0x"
    hex_addr = bytes.fromhex(address[2:])
    tron_addr = b"\x41" + hex_addr  # 0x41 is TRON prefix
    # Add checksum
    checksum = __crc32(tron_addr)[:4]
    return base58.b58encode(tron_addr + checksum).decode()

def __crc32(data):
    import hashlib
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()

def get_trx_balance(tron_address):
    try:
        r = requests.get(f"{TRON_API}/v1/accounts/{tron_address}")
        if r.status_code == 200:
            data = r.json()
            if data.get("data"):
                balance = data["data"][0].get("balance", 0) / 1e6  # Sun → TRX
                return balance
        return 0
    except Exception as e:
        print(f"⚠️ TRON balance error: {e} | {tron_address}")
        return 0
# ------------------ READ MNEMONIC ARRAY ------------------
mnemonic_file = "random_unique_shuffles.txt"
with open(mnemonic_file, "r", encoding="utf-8") as f:
    mnemonic_list = [line.strip() for line in f if line.strip()]

# ------------------ SCAN LOOP ------------------
try:
    for mnemonic_phrase in mnemonic_list:
        #print(f"\n🔑 Checking mnemonic: {mnemonic_phrase}")

        try:
            seed_bytes = Bip39SeedGenerator(mnemonic_phrase).Generate()
            bip44_mst = Bip44.FromSeed(seed_bytes, Bip44Coins.ETHEREUM)
        except Exception as e:
            #print(f"⚠️ Error generating seed or master key: {e}")
            continue

        for index in range(SCAN_ACCOUNTS):
            try:
                bip44_acc = bip44_mst.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(index)
                address = bip44_acc.PublicKey().ToAddress()
                tron_address = eth_to_tron_address(address)
                private_key_hex = bip44_acc.PrivateKey().Raw().ToHex()
            except Exception as e:
                print(f"⚠️ Error deriving account {index}: {e}")
                continue

            # Check balances
            balance_bnb = get_bnb_balance(address)
            balance_trx = get_trx_balance(tron_address)

            count += 1
            print(f"[{count}] {address} - BNB: {balance_bnb} | {tron_address} -  TRX: {balance_trx}")

            if balance_bnb > 0.001 or balance_trx > 1:
                print("\n🚨 FUNDED WALLET FOUND 🚨")
                print(f"Mnemonic: {mnemonic_phrase}")
                print(f"Private Key (HEX): {private_key_hex}")
                print(f"Address: {address}")
                print(f"BNB: {balance_bnb} | TRX: {balance_trx}\n")

                try:
                    with open("funded_wallets.txt", "a") as f:
                        f.write(f"Mnemonic: {mnemonic_phrase}\n")
                        f.write(f"Private Key (HEX): {private_key_hex}\n")
                        f.write(f"Address: {address}\n")
                        f.write(f"BNB: {balance_bnb} | TRX: {balance_trx}\n")
                        f.write("="*50 + "\n")
                except Exception as e:
                    print(f"⚠️ Error writing to file: {e}")

except KeyboardInterrupt:
    print("\n🛑 Scan stopped by user.")

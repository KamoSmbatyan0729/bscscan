import time
import base58
import requests
from mnemonic import Mnemonic
from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes

# -------------------- CONFIG --------------------
SCAN_ACCOUNTS = 1  # Accounts per mnemonic
TRON_API = "https://api.trongrid.io"  # Mainnet API

mnemo = Mnemonic("english")
count = 0

# -------------------- FUNCTIONS --------------------
def eth_to_tron_address(eth_address):
    """Convert ETH-style address (0x...) to TRON Base58Check address (starts with T)"""
    # Remove "0x"
    hex_addr = bytes.fromhex(eth_address[2:])
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
        print(f"⚠️ TRON balance error: {e}")
        return 0

# ------------------ SCAN LOOP ------------------
while True:
    try:
        for strength in [128]:  # 12 words
            try:
                mnemonic_phrase = mnemo.generate(strength=strength)
            except Exception as e:
                print(f"⚠️ Error generating mnemonic: {e}")
                time.sleep(1)
                continue

            print(f"\n🔑 New mnemonic: {mnemonic_phrase}")

            try:
                seed_bytes = Bip39SeedGenerator(mnemonic_phrase).Generate()
            except Exception as e:
                print(f"⚠️ Error generating seed: {e}")
                continue

            try:
                bip44_mst = Bip44.FromSeed(seed_bytes, Bip44Coins.ETHEREUM)  # ETH path works for TRON keys
            except Exception as e:
                print(f"⚠️ Error deriving master key: {e}")
                continue

            for index in range(SCAN_ACCOUNTS):
                try:
                    bip44_acc = bip44_mst.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(index)
                    eth_address = bip44_acc.PublicKey().ToAddress()
                    private_key_hex = bip44_acc.PrivateKey().Raw().ToHex()
                    tron_address = eth_to_tron_address(eth_address)
                except Exception as e:
                    print(f"⚠️ Error deriving account {index}: {e}")
                    continue

                balance_trx = get_trx_balance(tron_address)
                count += 1
                print(f"[{count}] {tron_address} - TRX: {balance_trx}")

                if balance_trx > 0:
                    print("\n🚨 FUNDED TRON WALLET FOUND 🚨")
                    print(f"Mnemonic: {mnemonic_phrase}")
                    print(f"Private Key (HEX): {private_key_hex}")
                    print(f"TRON Address: {tron_address}")
                    print(f"TRX: {balance_trx}")

                    try:
                        with open("funded_wallets_tron.txt", "a") as f:
                            f.write(f"Mnemonic: {mnemonic_phrase}\n")
                            f.write(f"Private Key (HEX): {private_key_hex}\n")
                            f.write(f"TRON Address: {tron_address}\n")
                            f.write(f"TRX: {balance_trx}\n")
                            f.write("="*50 + "\n")
                    except Exception as e:
                        print(f"⚠️ Error writing to file: {e}")

    except KeyboardInterrupt:
        print("\n🛑 Scan stopped by user.")
        break
    except Exception as e:
        print(f"🔥 Unexpected error in main loop: {e}")
        time.sleep(2)

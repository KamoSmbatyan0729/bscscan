import time
from mnemonic import Mnemonic
from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes
from web3 import Web3

# -------------------- CONFIG --------------------
SCAN_ACCOUNTS = 1  # Accounts per mnemonic

# RPC URLs
BSC_RPC = "https://bsc-dataseed.binance.org/"      # BSC Mainnet
ETH_RPC = "https://rpc.ankr.com/eth/81b91c7b7d1f515c560b21b2af020e3bcd1aad818e746f7d404ca2bff38eab77"               # Ethereum Mainnet

# Web3 connections
web3_bsc = Web3(Web3.HTTPProvider(BSC_RPC))
web3_eth = Web3(Web3.HTTPProvider(ETH_RPC))

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

def get_eth_balance(address):
    try:
        balance_wei = web3_eth.eth.get_balance(address)
        return web3_eth.from_wei(balance_wei, 'ether')
    except Exception as e:
        print(f"⚠️ ETH balance error: {e}")
        return 0

# ------------------ SCAN LOOP ------------------
while True:
    try:
        for strength in [128]:  # 128 = 12 words, 256 = 24 words
            try:
                mnemonic_phrase = mnemo.generate(strength=strength)
            except Exception as e:
                print(f"⚠️ Error generating mnemonic: {e}")
                time.sleep(1)
                continue

            word_count = 12 if strength == 128 else 24
            print(f"\n🔑 New {word_count}-word mnemonic: {mnemonic_phrase}")

            try:
                seed_bytes = Bip39SeedGenerator(mnemonic_phrase).Generate()
            except Exception as e:
                print(f"⚠️ Error generating seed: {e}")
                continue

            try:
                bip44_mst = Bip44.FromSeed(seed_bytes, Bip44Coins.ETHEREUM)
            except Exception as e:
                print(f"⚠️ Error deriving master key: {e}")
                continue
            
            for index in range(SCAN_ACCOUNTS):
                try:
                    bip44_acc = bip44_mst.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(index)
                    address = bip44_acc.PublicKey().ToAddress()
                    private_key_hex = bip44_acc.PrivateKey().Raw().ToHex()
                except Exception as e:
                    print(f"⚠️ Error deriving account {index}: {e}")
                    continue

                # Check balances
                balance_bnb = get_bnb_balance(address)
                balance_eth = get_eth_balance(address)

                count += 1
                print(f"[{count}] {address} - BNB: {balance_bnb} | ETH: {balance_eth}")

                if balance_bnb > 0 or balance_eth > 0:
                    print("\n🚨 FUNDED WALLET FOUND 🚨")
                    print(f"Mnemonic: {mnemonic_phrase}")
                    print(f"Private Key (HEX): {private_key_hex}")
                    print(f"Address: {address}")
                    print(f"BNB: {balance_bnb} | ETH: {balance_eth}")

                    try:
                        with open("funded_wallets.txt", "a") as f:
                            f.write(f"Mnemonic: {mnemonic_phrase}\n")
                            f.write(f"Private Key (HEX): {private_key_hex}\n")
                            f.write(f"Address: {address}\n")
                            f.write(f"BNB: {balance_bnb} | ETH: {balance_eth}\n")
                            f.write("="*50 + "\n")
                    except Exception as e:
                        print(f"⚠️ Error writing to file: {e}")

    except KeyboardInterrupt:
        print("\n🛑 Scan stopped by user.")
        break
    except Exception as e:
        print(f"🔥 Unexpected error in main loop: {e}")
        time.sleep(2)

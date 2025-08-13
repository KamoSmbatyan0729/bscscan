import time
from mnemonic import Mnemonic
from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes
from web3 import Web3

# -------------------- CONFIG --------------------
SCAN_ACCOUNTS = 1  # Accounts per mnemonic
BSC_RPC = "https://bsc-dataseed.binance.org/"  # Mainnet RPC
web3 = Web3(Web3.HTTPProvider(BSC_RPC))

mnemo = Mnemonic("english")
count = 0

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

            # Generate seed from mnemonic
            try:
                seed_bytes = Bip39SeedGenerator(mnemonic_phrase).Generate()
            except Exception as e:
                print(f"⚠️ Error generating seed: {e}")
                continue

            # Derive BSC (same as ETH)
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

                try:
                    # Get balance in BNB
                    balance_wei = web3.eth.get_balance(address)
                    balance_bnb = web3.from_wei(balance_wei, 'ether')
                except Exception as e:
                    print(f"⚠️ RPC error getting balance for {address}: {e}")
                    time.sleep(1)
                    continue

                count += 1
                print(f"[{count}] {address} - Balance: {balance_bnb} BNB")

                if balance_bnb > 0:
                    print("\n🚨 FUNDED WALLET FOUND 🚨")
                    print(f"Mnemonic: {mnemonic_phrase}")
                    print(f"Private Key (HEX): {private_key_hex}")
                    print(f"Address: {address}")
                    print(f"Balance: {balance_bnb} BNB")

                    try:
                        with open("funded_wallets_bsc.txt", "a") as f:
                            f.write(f"Mnemonic: {mnemonic_phrase}\n")
                            f.write(f"Private Key (HEX): {private_key_hex}\n")
                            f.write(f"Address: {address}\n")
                            f.write(f"Balance: {balance_bnb} BNB\n")
                            f.write("="*50 + "\n")
                    except Exception as e:
                        print(f"⚠️ Error writing to file: {e}")

    except KeyboardInterrupt:
        print("\n🛑 Scan stopped by user.")
        break
    except Exception as e:
        print(f"🔥 Unexpected error in main loop: {e}")
        time.sleep(2)

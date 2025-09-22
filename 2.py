#!/usr/bin/env python3
"""
keccak_bruteforce_fixed_windows.py

Parallel keccak256 preimage search (Solidity-ABI string style) — Windows-friendly
(using multiprocessing.Manager() with Namespace + Lock for progress counting).
"""

import argparse
import os
import random
import string
import sys
import time
from multiprocessing import Pool, Manager, current_process
from typing import Iterable, List, Optional

# ---- Keccak backend selection (fast preferred) ----
try:
    from eth_hash.auto import keccak  # eth-hash (fast, recommended)
    def keccak256(data: bytes) -> bytes:
        return keccak(data)
except Exception:
    try:
        from Crypto.Hash import keccak as pycrypto_keccak  # pycryptodome fallback
        def keccak256(data: bytes) -> bytes:
            k = pycrypto_keccak.new(digest_bits=256)
            k.update(data)
            return k.digest()
    except Exception:
        # Last fallback to web3 (slower)
        from web3 import Web3
        def keccak256(data: bytes) -> bytes:
            return Web3.keccak(data)

# ---- ABI encoding helper ----
def abi_encode_string_solidity_style(s: str) -> bytes:
    b = s.encode("utf-8")
    length = len(b)
    padded_len = ((length + 31) // 32) * 32
    offset = (32).to_bytes(32, byteorder="big")
    length_encoded = length.to_bytes(32, byteorder="big")
    padded_bytes = b + b"\x00" * (padded_len - length)
    return offset + length_encoded + padded_bytes

def hash_response(response_str: str) -> str:
    encoded = abi_encode_string_solidity_style(response_str)
    return keccak256(encoded).hex()

# ---- Candidate helpers ----
def random_candidate_batch(charset: str, length: int, batch_size: int) -> List[str]:
    return ["".join(random.choices(charset, k=length)) for _ in range(batch_size)]

# ---- Worker functions (expect a single tuple arg) ----
def worker_check_random(args):
    (target_hexes, charset, length, batch_size, found_event, progress_ns, progress_lock) = args
    target_set = set(h.lower() for h in target_hexes)
    try:
        while not found_event.is_set():
            batch = random_candidate_batch(charset, length, batch_size)
            for candidate in batch:
                h = hash_response(candidate)
                if h in target_set:
                    with open("funded_candidate.txt", "a", encoding="utf-8") as f:
                        f.write("FUNDED WALLET FOUND\n")
                        f.write(f"candidate: {candidate}\n")
                        f.write(f"hash: {h}\n")
                        f.write("=" * 40 + "\n")
                    found_event.set()
                    return candidate, h
            # update progress using Manager.Lock + Namespace
            with progress_lock:
                progress_ns.count += len(batch)
    except KeyboardInterrupt:
        return None
    return None

def worker_check_dict(args):
    (target_hexes, dict_path, prefix, suffix, found_event, progress_ns, progress_lock, chunk_index, num_chunks) = args
    target_set = set(h.lower() for h in target_hexes)
    try:
        with open(dict_path, "r", encoding="utf-8", errors="ignore") as fh:
            for idx, line in enumerate(fh):
                if found_event.is_set():
                    return None
                if (idx % num_chunks) != chunk_index:
                    continue
                word = line.rstrip("\n\r")
                candidate = f"{prefix}{word}{suffix}"
                h = hash_response(candidate)
                if h in target_set:
                    with open("funded_candidate.txt", "a", encoding="utf-8") as f:
                        f.write("FUNDED WALLET FOUND\n")
                        f.write(f"candidate: {candidate}\n")
                        f.write(f"hash: {h}\n")
                        f.write("=" * 40 + "\n")
                    found_event.set()
                    return candidate, h
                with progress_lock:
                    progress_ns.count += 1
    except KeyboardInterrupt:
        return None
    return None

# ---- CLI / main ----
def parse_args():
    p = argparse.ArgumentParser(description="Parallel keccak256 preimage search (Solidity-ABI string style)")
    p.add_argument("--target", "-t", action="append", required=True,
                   help="Target hash(es) in hex (without 0x). Can be used multiple times.")
    p.add_argument("--length", "-L", type=int, default=50,
                   help="Length of random candidates (default: 50).")
    p.add_argument("--charset", "-c", type=str, default=string.ascii_letters + string.digits,
                   help="Characters to use for random candidates (default: alphanumeric).")
    p.add_argument("--processes", "-p", type=int, default=max(1, (os.cpu_count() or 1)),
                   help="Number of parallel processes (default: CPU count).")
    p.add_argument("--batch-size", "-b", type=int, default=4096,
                   help="How many candidates each process hashes per inner loop (default: 4096).")
    p.add_argument("--dict-file", "-d", type=str, default=None,
                   help="Path to dictionary file (one candidate per line). If provided, uses dict attack instead of pure random.")
    p.add_argument("--prefix", type=str, default="",
                   help="Prefix to add to each generated or dictionary candidate.")
    p.add_argument("--suffix", type=str, default="",
                   help="Suffix to add to each generated or dictionary candidate.")
    p.add_argument("--progress-interval", type=int, default=5,
                   help="Seconds between progress prints.")
    return p.parse_args()

def main():
    args = parse_args()
    target_hexes = [t.lower().lstrip("0x") for t in args.target]
    processes = max(1, args.processes)
    batch_size = max(1, args.batch_size)
    length = args.length
    charset = args.charset
    dict_file = args.dict_file
    prefix = args.prefix or ""
    suffix = args.suffix or ""

    print("Starting keccak preimage search")
    print(f"Targets: {target_hexes}")
    print(f"Processes: {processes}, batch_size: {batch_size}, length: {length}")
    print(f"Charset length: {len(charset)}")
    if dict_file:
        print(f"Dictionary file: {dict_file}")
    if prefix or suffix:
        print(f"Prefix: '{prefix}'  Suffix: '{suffix}'")

    # Create Manager-shared objects (Windows-friendly)
    manager = Manager()
    found_event = manager.Event()
    progress_ns = manager.Namespace()
    progress_ns.count = 0
    progress_lock = manager.Lock()

    start_time = time.time()
    pool = None
    try:
        pool = Pool(processes=processes)
        async_results = []

        if dict_file:
            # each worker gets a round-robin slice of dictionary
            for i in range(processes):
                wa = (target_hexes, dict_file, prefix, suffix, found_event, progress_ns, progress_lock, i, processes)
                async_results.append(pool.apply_async(worker_check_dict, (wa,)))
        else:
            for _ in range(processes):
                wa = (target_hexes, charset, length, batch_size, found_event, progress_ns, progress_lock)
                async_results.append(pool.apply_async(worker_check_random, (wa,)))

        # Progress loop
        try:
            while True:
                time.sleep(args.progress_interval)
                count = progress_ns.count
                elapsed = time.time() - start_time
                rate = (count / elapsed) if elapsed > 0 else 0.0
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Tried {count:,} candidates — {rate:,.2f} tries/sec")
                # check results
                for ar in async_results:
                    if ar.ready():
                        res = ar.get()
                        if res:
                            candidate, h = res
                            print(f"Found match in pool: {candidate} -> {h}")
                            found_event.set()
                            pool.terminate()
                            pool.join()
                            return
                if found_event.is_set():
                    print("Found event set, collecting results...")
                    pool.terminate()
                    pool.join()
                    return
        except KeyboardInterrupt:
            print("User interrupted (Ctrl+C). Stopping pool...")
            found_event.set()
            pool.terminate()
            pool.join()
    finally:
        elapsed = time.time() - start_time
        total_tried = progress_ns.count
        print(f"Finished. Time elapsed: {elapsed:.2f}s. Total tried: {total_tried:,}")

if __name__ == "__main__":
    main()

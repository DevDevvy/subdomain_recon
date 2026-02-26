#!/usr/bin/env python3
import secrets
import sys

def read_domains(path: str):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.split("#", 1)[0].strip().lower().rstrip(".")
            if line:
                yield line

def rand_label(n=18):
    alphabet = "abcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(secrets.choice(alphabet) for _ in range(n))

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} input/domains.txt SAMPLES", file=sys.stderr)
        sys.exit(2)

    domains = list(read_domains(sys.argv[1]))
    samples = int(sys.argv[2])

    for d in domains:
        for _ in range(samples):
            print(f"{rand_label()}.{d}")

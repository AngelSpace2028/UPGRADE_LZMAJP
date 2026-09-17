#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified PAQJP+PJP — Dual Method + 12 Downloads + Real Dictionary
★ ZSTANDARD MANDATORY — will retry import after every install attempt ★
"""

import math, random, decimal, hashlib, base64, heapq, struct, os, tempfile
import re, sys, subprocess, importlib, time, urllib.request, site
from typing import Optional, List, Tuple, Dict, Callable, Any
from collections import Counter

# ============================ BACKENDS ============================
try: import paq
except ImportError: paq = None
try:
    import brotli; HAS_BROTLI = True
except ImportError:
    brotli = None; HAS_BROTLI = False

USE_QUANTUM = False
HAS_QISKIT = False
HAS_ZSTD = False

# ==================================================================
# ★ BULLET-PROOF ZSTANDARD INSTALLER ★
# ==================================================================
def _try_import_zstd():
    """Try to import zstandard; refresh sys.path first in case it was just installed."""
    # Refresh sys.path so a freshly-installed package is visible
    try:
        importlib.invalidate_caches()
        # Re-add user site-packages if it exists
        user_site = site.getusersitepackages()
        if user_site and user_site not in sys.path:
            sys.path.insert(0, user_site)
    except Exception:
        pass
    try:
        import zstandard as zstd
        return zstd
    except ImportError:
        return None

def _try_install_zstd():
    """Try 5 different install strategies. Returns True if any succeeds."""
    cmds = [
        [sys.executable, '-m', 'pip', 'install', '--no-input', '--disable-pip-version-check', 'zstandard'],
        [sys.executable, '-m', 'pip', 'install', '--user', '--no-input', '--disable-pip-version-check', 'zstandard'],
        [sys.executable, '-m', 'pip', 'install', '--break-system-packages', '--no-input', '--disable-pip-version-check', 'zstandard'],
        ['pip', 'install', '--no-input', '--disable-pip-version-check', 'zstandard'],
        ['pip3', 'install', '--no-input', '--disable-pip-version-check', 'zstandard'],
    ]
    for cmd in cmds:
        print(f"  Trying: {' '.join(cmd)}")
        try:
            subprocess.check_call(cmd)
            print(f"  OK command succeeded, retrying import...")
            # Re-check import after each attempt
            if _try_import_zstd() is not None:
                print(f"  SUCCESS!")
                return True
        except Exception as e:
            print(f"  FAILED: {e}")
    return False

print("=" * 70)
print("Checking zstandard (MANDATORY backend)...")
print("=" * 70)

_zstd = _try_import_zstd()

if _zstd is None:
    print("zstandard NOT FOUND. Trying to install automatically...")
    if not _try_install_zstd():
        print()
        print("=" * 70)
        print("FATAL: Could not install zstandard automatically.")
        print()
        print("Please open a TERMINAL and run one of these commands:")
        print()
        print("    pip install zstandard")
        print("    pip install --user zstandard")
        print("    pip install --break-system-packages zstandard")
        print()
        print("Then re-run this script.")
        print("=" * 70)
        sys.exit(1)
    _zstd = _try_import_zstd()
    if _zstd is None:
        print("FATAL: zstandard installed but still cannot be imported.")
        print("Try closing and reopening the Python process / Codespace.")
        sys.exit(1)

zstd = _zstd
zstd_cctx = zstd.ZstdCompressor(level=22)
zstd_dctx = zstd.ZstdDecompressor()
HAS_ZSTD = True
print("zstandard loaded successfully.")

# ==================================================================
# Optional: other backends
# ==================================================================
def install_package(pkg):
    print(f"Installing {pkg}...")
    for cmd in [
        [sys.executable, '-m', 'pip', 'install', '--no-input', '--disable-pip-version-check', pkg],
        [sys.executable, '-m', 'pip', 'install', '--user', '--no-input', '--disable-pip-version-check', pkg],
        ['pip', 'install', '--no-input', '--disable-pip-version-check', pkg],
    ]:
        try: subprocess.check_call(cmd); print(f"  OK {pkg}"); return True
        except Exception as e: print(f"  FAIL: {e}")
    return False

if input("Option 1: Quantum (Qiskit)? (y/n) [n]: ").strip().lower() == 'y':
    try:
        from qiskit import QuantumCircuit
        HAS_QISKIT = True; USE_QUANTUM = True; print("Quantum ENABLED.")
    except ImportError:
        if install_package('qiskit'):
            try:
                from qiskit import QuantumCircuit
                HAS_QISKIT = True; USE_QUANTUM = True; print("Quantum ENABLED.")
            except ImportError: print("Qiskit failed.")
        else: print("Qiskit failed.")
else: print("Quantum disabled.")

if input("Option 2: Install paq + brotli? (y/n) [y]: ").strip().lower() != 'n':
    for pkg in ['paq', 'brotli']:
        try: importlib.import_module(pkg); print(f"{pkg} present.")
        except ImportError: install_package(pkg)
    try: import paq
    except ImportError: paq = None
    try: import brotli; HAS_BROTLI = True
    except ImportError: brotli = None; HAS_BROTLI = False
else: print("Skipping paq + brotli.")

print(f"\nBackends: zstd=Y paq={'Y' if paq else 'N'} brotli={'Y' if HAS_BROTLI else 'N'}")

PROGNAME = "UnifiedPAQJP+PJP (Dual-Method + 12 Downloads + Real Dict)"

# ============================ DICTIONARY ============================
DICT_DIR = "Dictionaries"
COMBINED_DICTIONARY_FILE = os.path.join(DICT_DIR, "dictionary_combined.txt")
MAX_LINE_ENTRIES = 1024

DICTIONARY_FILES = [
    "generated.txt", "eng_news_2005_1M-sentences.txt", "eng_news_2005_1M-words.txt",
    "eng_news_2005_1M-sources.txt", "eng_news_2005_1M-co_n.txt", "eng_news_2005_1M-co_s.txt",
    "eng_news_2005_1M-inv_w_2.txt", "eng_news_2005_1M-inv_w_3.txt", "eng_news_2005_1M-inv_so.txt",
    "eng_news_2005_1M-meta.txt", "Dictionary.txt",
    "the-complete-reference-html-css-fifth-edition.txt",
]
DICTIONARY_URLS = [
    "https://drive.google.com/uc?export=download&id=1u_1dCEl8hhdEug6GwkOxHAuSx_6_Pme9",
    "https://drive.google.com/uc?export=download&id=1pVqNN5JZ2AeOCgRaHkv4Vv6Byr4zK20e",
    "https://drive.google.com/uc?export=download&id=1ZSC-Tn76x8itdN0rCp-Zw17hGudxbjxo",
    "https://drive.google.com/uc?export=download&id=1VB_7tzngs4GxjclSRyRDnxgS8znT2w2S",
    "https://drive.google.com/uc?export=download&id=1KVIRgiMrhCUCqQZJ3UT67ztls2GqGJzz",
    "https://drive.google.com/uc?export=download&id=1Z3Lx6SqL4HWsnmbJCez4kXWRQQhUXWKL",
    "https://drive.google.com/uc?export=download&id=1br2bdRMkZEVVRPKYmC4IIaZuAjxFJE4N",
    "https://drive.google.com/uc?export=download&id=1aE6ubPZiJ8rr3lEVk8fFJYjDQ1y1rU0X",
    "https://drive.google.com/uc?export=download&id=1uro3TZe-t5zPx2Qu2xrTL3lU8N0melk9",
    "https://drive.google.com/uc?export=download&id=1HqsTH1DqpWNpGbn9VtD7-SB6wVqA90R2",
    "https://drive.google.com/uc?export=download&id=1zZ8iMeBC3605NZhuc4UE9jx_w_lZFg5B",
    "https://drive.google.com/uc?export=download&id=1dDdqYDgm7f-smS7KF70Wf0KmyFo-ft1M",
]

def download_12_dictionaries():
    if not os.path.exists(DICT_DIR):
        try: os.makedirs(DICT_DIR)
        except Exception: pass
    all_words = set(); success = 0
    for filename, url in zip(DICTIONARY_FILES, DICTIONARY_URLS):
        local_path = os.path.join(DICT_DIR, filename)
        print(f"  Downloading {filename} ...")
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=20) as response:
                content = response.read()
            if b'<html' in content[:200].lower():
                print(f"    WARNING: HTML. Skip."); continue
            with open(local_path, 'wb') as f: f.write(content)
            text = content.decode('utf-8', errors='ignore')
            for line in text.splitlines():
                w = line.strip()
                if not w: continue
                try:
                    decoded = base64.b64decode(w, validate=True).decode('utf-8')
                    all_words.add(decoded)
                except Exception:
                    all_words.add(w)
            print(f"    OK ({len(content)} bytes)")
            success += 1
        except Exception as e:
            print(f"    FAIL: {e}")
    print(f"  Downloaded {success}/12 → {len(all_words):,} raw entries")
    return all_words

def build_real_dictionary(target=100_000, try_download=True):
    words = set()
    if try_download:
        print("\nStep 1: 12 Google Drive dictionary files")
        try:
            words |= download_12_dictionaries()
            print(f"  Running total: {len(words):,}")
        except Exception as e:
            print(f"  Download error (ignored): {e}")

    if len(words) < target:
        print("\nStep 2: System dictionaries")
        for path in ["/usr/share/dict/words", "/usr/share/dict/american-english",
                     "/usr/share/dict/british-english", "/usr/share/hunspell/en_US.dic",
                     os.path.expanduser("~/.local/share/dict/words")]:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            w = line.split('/')[0].strip().lower()
                            if w and w.isalpha() and 1 <= len(w) <= 64:
                                words.add(w)
                    print(f"  {path}: total {len(words):,}")
                    if len(words) >= target: break
                except Exception as e:
                    print(f"  Skip {path}: {e}")

    if len(words) < target:
        print("\nStep 3: english-words pip package")
        try:
            from english_words import get_english_words_set
            extra = {w.lower() for w in get_english_words_set(['web2', 'gcide'], lower=True)
                     if w.isalpha() and len(w) <= 64}
            words |= extra
            print(f"  Total: {len(words):,}")
        except ImportError:
            print("  Not installed")
        except Exception as e:
            print(f"  Failed: {e}")

    if len(words) < target:
        print("\nStep 4: NLTK WordNet")
        try:
            from nltk.corpus import words as nltk_words
            extra = {w.lower() for w in nltk_words.words() if w.isalpha() and len(w) <= 64}
            words |= extra
            print(f"  Total: {len(words):,}")
        except Exception:
            print("  Not available")

    if len(words) < 1000:
        print("\nStep 5: AI-generated fallback")
        words |= _build_ai_dictionary()

    words = sorted(w for w in words if w and w.isascii() and 1 <= len(w) <= 64)
    print(f"\nFINAL dictionary: {len(words):,} words")
    return words

def _build_ai_dictionary():
    BASE = """the be to of and a in that have i it for not on with he as you do at this
    but his by from they we say her she or an will my one all would there their what
    data file code program computer system network server client software hardware
    internet website email message password user account login database algorithm
    function variable constant array list queue stack tree graph node compress
    decompress encode decode encrypt decrypt hash checksum verify lossless test
    build compile run execute debug error bug crash fix patch update version
    document folder directory path link address url http https protocol port socket
    bit byte word block stream buffer cache memory disk drive cpu gpu ram rom
    python java cpp c rust go ruby php swift kotlin scala perl lua
    lorem ipsum dolor sit amet consectetur adipiscing elit sed eiusmod tempor
    incididunt labore dolore magna aliqua enim minim veniam quis nostrud exercitation
    ullamco laboris nisi aliquip commodo consequat duis aute irure reprehenderit
    voluptate velit esse cillum fugiat nulla pariatur excepteur occaecat cupidatat
    proident sunt culpa officia deserunt mollit anim laborum""".split()
    PREFIXES = ["un","re","pre","dis","non","anti","over","under","multi","inter",
                "trans","auto","micro","macro","bio","eco","neuro","techno","cyber",
                "nano","astro","hydro","thermo","meta","proto","pseudo","quasi"]
    SUFFIXES = ["ing","ed","er","est","ly","tion","ment","ness","ful","less","able",
                "ible","ous","ive","al","ic","ity","ize","ance","ence","ate","ify",
                "ship","hood","ward","wise","ist","ism","ology","ography","scope",
                "graph","gram","logy","nomy","pathy"]
    words = set(BASE)
    for w in BASE:
        if len(w) >= 3:
            for sfx in ["s","es","ed","ing","er","est","ly"]: words.add(w + sfx)
    for p in PREFIXES:
        for w in BASE:
            if len(w) >= 3:
                words.add(p + w); words.add(p + w + "ed"); words.add(p + w + "ing")
    for w in BASE:
        for s in SUFFIXES:
            if len(w) >= 3: words.add(w + s)
    for n in ["zero","one","two","three","four","five","six","seven","eight",
              "nine","ten","eleven","twelve","twenty","thirty","forty","fifty",
              "hundred","thousand","million","billion"]:
        words.add(n); words.add(n + "th")
    return words

# ============================ CONSTANTS ============================
PRIMES = [p for p in range(2, 256) if all(p % d != 0 for d in range(2, int(p ** 0.5) + 1))]
PI_DIGITS = [79, 17, 111]

def find_nearest_prime_around(n):
    if n < 2: return 2
    o = 0
    while True:
        c1, c2 = n - o, n + o
        if c1 >= 2 and all(c1 % d != 0 for d in range(2, int(c1 ** 0.5) + 1)): return c1
        if c2 >= 2 and all(c2 % d != 0 for d in range(2, int(c2 ** 0.5) + 1)): return c2
        o += 1

_CONST_DIAPASON_ITER_CODE = [
    (2, 0b10), (2, 0b11), (3, 0b010), (3, 0b011), (4, 0b0010), (4, 0b0011),
    (5, 0b00010), (5, 0b00011), (6, 0b000010), (6, 0b000011), (7, 0b0000010),
    (7, 0b0000011), (8, 0b00000010), (8, 0b00000011), (9, 0b000000010),
    (9, 0b000000011),
]
_CONST_DIAPASON_ITER_DECODE = {v: k for k, v in enumerate(_CONST_DIAPASON_ITER_CODE)}

ALPHABET_6BIT = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 \n"
CHAR_TO_6BIT = {ch: i for i, ch in enumerate(ALPHABET_6BIT)}
SIXBIT_TO_CHAR = {i: ch for ch, i in CHAR_TO_6BIT.items()}

PAQ_STATE_TABLE = [
    [1,2,0,0],[3,5,0,1],[4,6,2,0],[7,10,0,2],[8,12,3,0],[9,13,1,1],[11,14,0,3],
    [15,19,4,0],[16,23,2,1],[17,24,2,1],[18,25,2,1],[20,27,1,2],[21,28,1,2],
    [22,29,1,2],[26,30,0,4],[31,33,5,0],[32,34,3,1],[35,37,1,3],[36,38,1,3],
    [39,42,0,5],[40,43,4,1],[41,44,2,2],[45,48,1,4],[46,49,1,4],[47,50,1,4],
    [51,52,0,6],[53,55,6,0],[54,56,4,1],[57,59,2,3],[58,60,2,3],[61,63,0,7],
    [62,64,5,1],[65,66,3,2],[67,69,1,5],[68,70,1,5],[71,73,0,8],[72,74,6,1],
    [75,76,4,2],[77,78,2,4],[79,80,2,4],[81,82,0,9],[83,84,7,1],[85,86,5,2],
    [87,88,3,3],[89,90,1,6],[91,92,0,10],[93,94,8,1],[95,96,6,2],[97,98,4,3],
    [99,100,2,5],[101,102,0,11],[103,104,9,1],[105,106,7,2],[107,108,5,3],
    [109,110,3,4],[111,112,1,7],[113,114,0,12],[115,116,10,1],[117,118,8,2],
    [119,120,6,3],[121,122,4,4],[123,124,2,6],[125,126,0,13],[127,128,11,1],
    [129,130,9,2],[131,132,7,3],[133,134,5,4],[135,136,3,5],[137,138,1,8],
    [139,140,0,14],[141,142,12,1],[143,144,10,2],[145,146,8,3],[147,148,6,4],
    [149,150,4,5],[151,152,2,7],[153,154,0,15],[155,156,13,1],[157,158,11,2],
    [159,160,9,3],[161,162,7,4],[163,164,5,5],[165,166,3,6],[167,168,1,9],
    [169,170,0,16],[171,172,14,1],[173,174,12,2],[175,176,10,3],[177,178,8,4],
    [179,180,6,5],[181,182,4,6],[183,184,2,8],[185,186,0,17],[187,188,15,1],
    [189,190,13,2],[191,192,11,3],[193,194,9,4],[195,196,7,5],[197,198,5,6],
    [199,200,3,7],[201,202,1,10],[203,204,0,18],[205,206,16,1],[207,208,14,2],
    [209,210,12,3],[211,212,10,4],[213,214,8,5],[215,216,6,6],[217,218,4,7],
    [219,220,2,9],[221,222,0,19],[223,224,17,1],[225,226,15,2],[227,228,13,3],
    [229,230,11,4],[231,232,9,5],[233,234,7,6],[235,236,5,7],[237,238,3,8],
    [239,240,1,11],[241,242,0,20],[243,244,18,1],[245,246,16,2],[247,248,14,3],
    [249,250,12,4],[251,252,10,5],[253,254,8,6],[255,255,6,7],
]

class TransformError(Exception): pass
class DecompressionError(Exception): pass
class IntegrityError(Exception): pass

def mod_inv(a, m):
    if a == 0: return None
    m0 = m; y = 0; x = 1
    if m == 1: return 0
    while a > 1:
        q = a // m; t = m; m = a % m; a = t
        t = y; y = x - q * y; x = t
    if x < 0: x += m0
    return x

MAGIC = b'PJP4'
MAGIC_LEN = 4
HASH_LEN = 32
HEADER_LEN = MAGIC_LEN + HASH_LEN

# ============================ COMPRESSOR ============================
class UnifiedCompressor:
    ULTRA_TIME_LIMIT = 300
    QUANTUM_QUBITS = 8
    WINDOW_SIZE = 2048
    MIN_MATCH = 3
    MAX_MATCH = 2048
    MAX_DIST = 2048

    def __init__(self, try_download=True):
        print("\n" + "=" * 60)
        print("BUILDING DICTIONARY")
        print("=" * 60)
        words = build_real_dictionary(target=100_000, try_download=try_download)
        self.static_dict = words
        self.word_to_index = {w: i for i, w in enumerate(words)}

        self.PI_DIGITS = PI_DIGITS.copy()
        self.seed_tables = self._gen_seed_tables()
        self.fibonacci = self._gen_fib(100)
        self.PI_STR = "3.14159265358979323846264338327950288419716939937510"
        self.repeat_count = 100
        self.mod_state_table = [[(v - 400) & 0xFF for v in row] for row in PAQ_STATE_TABLE]
        self._build_mask_46()
        self._build_transform_maps()
        if USE_QUANTUM and HAS_QISKIT:
            self._precompute_quantum_transforms()

    # ---------- helpers ----------
    def _build_mask_46(self):
        base = [1, 2, 4, 8, 16, 32, 64, 128, 3, 6]
        self.mask_46 = [(b - 10) & 0xFF for b in base] * 10
    def _gen_seed_tables(self, num=126, size=40, seed=42):
        random.seed(seed)
        return [[random.randint(5, 255) for _ in range(size)] for _ in range(num)]
    def _gen_fib(self, n):
        a, b = 0, 1; res = [a, b]
        for _ in range(2, n): a, b = b, a + b; res.append(b)
        return res
    def get_seed(self, idx, val):
        return self.seed_tables[idx][val % 40] if 0 <= idx < len(self.seed_tables) else 0
    def _append_bits(self, bl, v, c):
        for i in range(c - 1, -1, -1): bl.append((v >> i) & 1)
    def _read_bits(self, bits, pos, cnt):
        v = 0
        for i in range(cnt):
            if pos + i >= len(bits): return 0
            v = (v << 1) | bits[pos + i]
        return v
    def _get_pattern(self, size, index):
        random.seed(12345 + size * 100 + index)
        return [random.randint(0, 255) for _ in range(size)]
    def _calculate_repeats(self, data):
        if not data: return 1
        L = len(data); s = sum(data) % 256
        return max(1, min(256, ((L * 13 + s * 17) % 256) + 1))
    def _verify_lossless(self, orig, trans, rev):
        try: return rev(trans) == orig
        except Exception: return False

    # ---------------- Transform 00 ----------------
    def transform_00(self, data):
        if not data: return struct.pack('>I', 0)
        br, bl, bsh = None, float('inf'), []
        cur = bytearray(data); ap = []; orig = bytes(data)
        for _ in range(10):
            bs = 0; bsh_ = cur; bsc = float('-inf')
            for sh in range(256):
                tmp = bytearray(cur)
                for j in range(len(tmp)): tmp[j] = (tmp[j] + sh) % 256
                sc = 0; i = 0
                while i < len(tmp):
                    val = tmp[i]; run = 1; i += 1
                    while i < len(tmp) and tmp[i] == val: run += 1; i += 1
                    sc += run * run
                if sc > bsc: bsc = sc; bsh_ = tmp; bs = sh
            ap.append(bs)
            rle = self._apply_rle(bsh_, bs)
            dec = self._rle_decode(rle)
            if dec is not None:
                test = bytearray(dec)
                for s in ap:
                    for j in range(len(test)): test[j] = (test[j] - s) % 256
                if bytes(test) == orig and len(rle) < bl:
                    bl = len(rle); br = rle; bsh = ap.copy()
            cur = bsh_
            if len(rle) >= len(data): break
        if br is None or bl >= len(data):
            return struct.pack('>I', len(data)) + bytes([0]) + data
        h = bytearray(struct.pack('>I', len(data)))
        h.append(len(bsh)); h.extend(bsh)
        return bytes(h) + br

    def _apply_rle(self, sd, shift):
        bits = []
        self._append_bits(bits, 0b010, 3); self._append_bits(bits, shift, 8)
        i = 0; n = len(sd)
        while i < n:
            val = sd[i]; run = 1; i += 1
            while i < n and sd[i] == val: run += 1; i += 1
            while run >= 13:
                ch = min(run, 268)
                self._append_bits(bits, 0b1111, 4)
                self._append_bits(bits, ch - 13, 8); self._append_bits(bits, val, 8)
                run -= ch
            if run == 1:
                self._append_bits(bits, 0b00, 2); self._append_bits(bits, val, 8)
            elif run <= 5:
                self._append_bits(bits, 0b01, 2)
                self._append_bits(bits, run - 2, 2); self._append_bits(bits, val, 8)
            elif run <= 12:
                self._append_bits(bits, 0b10, 2)
                self._append_bits(bits, run - 6, 3); self._append_bits(bits, val, 8)
        pad = (8 - len(bits) % 8) % 8; self._append_bits(bits, 0, pad)
        out = bytearray()
        for j in range(0, len(bits), 8):
            b = 0
            for k in range(8):
                if j + k < len(bits): b = (b << 1) | bits[j + k]
            out.append(b)
        return bytes(out)

    def reverse_transform_00(self, cdata):
        if not cdata or cdata == struct.pack('>I', 0): return b''
        if len(cdata) < 4: raise TransformError("RLE short")
        ol = struct.unpack('>I', cdata[:4])[0]; cdata = cdata[4:]
        if not cdata: return b''
        if cdata[0] == 0: return cdata[1:ol + 1]
        np = cdata[0]
        if np == 0 or len(cdata) < 1 + np: raise TransformError("RLE hdr")
        shifts = list(cdata[1:1 + np]); rle = cdata[1 + np:]
        dec = self._rle_decode(rle)
        if dec is None: raise TransformError("RLE dec")
        cur = bytearray(dec[:ol])
        for sh in reversed(shifts):
            for i in range(len(cur)): cur[i] = (cur[i] - sh) % 256
        return bytes(cur)

    def _rle_decode(self, data):
        if not data: return None
        bits = []
        for b in data:
            for i in range(7, -1, -1): bits.append((b >> i) & 1)
        pos = 0; nb = len(bits)
        if nb < 11: return None
        if self._read_bits(bits, pos, 3) != 0b010: return None
        pos += 3 + 8
        out = bytearray()
        while pos < nb:
            if pos + 2 > nb: break
            pfx = self._read_bits(bits, pos, 2); pos += 2
            if pfx == 0b00:
                if pos + 8 > nb: break
                run = 1
            elif pfx == 0b01:
                if pos + 2 + 8 > nb: break
                run = 2 + self._read_bits(bits, pos, 2); pos += 2
            elif pfx == 0b10:
                if pos + 3 + 8 > nb: break
                run = 6 + self._read_bits(bits, pos, 3); pos += 3
            else:
                if pos + 2 + 8 + 8 > nb: break
                if self._read_bits(bits, pos, 2) != 0b11: return None
                pos += 2
                run = 13 + self._read_bits(bits, pos, 8); pos += 8
            if pos + 8 > nb: break
            val = self._read_bits(bits, pos, 8); pos += 8
            out.extend([val] * run)
        for i in range(pos, nb):
            if bits[i] != 0: return None
        return out

    # ---------------- Transforms 01-21 ----------------
    def transform_01(self, d):
        t = bytearray(d); r = self.repeat_count
        for prime in PRIMES:
            xv = prime if prime == 2 else max(1, math.ceil(prime * 4096 / 28672))
            for _ in range(r):
                for i in range(0, len(t), 3):
                    if i < len(t): t[i] ^= xv
        return bytes(t)
    reverse_transform_01 = transform_01

    def transform_02(self, d):
        if not d: return b'\x00'
        t = bytearray(d); pi = (len(d) + sum(d)) % 256
        pv = self._get_pattern(4, pi)
        for i in range(1, len(t), 4):
            if i < len(t): t[i] ^= pv[i % len(pv)]
        return bytes([pi]) + bytes(t)
    def reverse_transform_02(self, d):
        if d == b'\x00': return b''
        if len(d) < 2: raise TransformError("T02")
        pi = d[0]; t = bytearray(d[1:]); pv = self._get_pattern(4, pi)
        for i in range(1, len(t), 4):
            if i < len(t): t[i] ^= pv[i % len(pv)]
        return bytes(t)

    def transform_03(self, d):
        if not d: return b'\x00'
        t = bytearray(d); rot = (len(d) * 13 + sum(d)) % 8
        if rot == 0: rot = 1
        for i in range(2, len(t), 5):
            if i < len(t): t[i] = ((t[i] << rot) | (t[i] >> (8 - rot))) & 0xFF
        return bytes([rot]) + bytes(t)
    def reverse_transform_03(self, d):
        if d == b'\x00': return b''
        if len(d) < 2: raise TransformError("T03")
        rot = d[0]; t = bytearray(d[1:])
        for i in range(2, len(t), 5):
            if i < len(t): t[i] = ((t[i] >> rot) | (t[i] << (8 - rot))) & 0xFF
        return bytes(t)

    def transform_04(self, d):
        t = bytearray(d)
        for _ in range(self.repeat_count):
            for i in range(len(t)): t[i] = (t[i] - (i % 256)) % 256
        return bytes(t)
    def reverse_transform_04(self, d):
        t = bytearray(d)
        for _ in range(self.repeat_count):
            for i in range(len(t)): t[i] = (t[i] + (i % 256)) % 256
        return bytes(t)

    def transform_05(self, d, s=3):
        return bytes(((b << s) | (b >> (8 - s))) & 0xFF for b in d)
    def reverse_transform_05(self, d, s=3):
        return bytes(((b >> s) | (b << (8 - s))) & 0xFF for b in d)

    def transform_06(self, d, sd=42):
        random.seed(sd); sub = list(range(256)); random.shuffle(sub)
        return bytes(sub[b] for b in d)
    def reverse_transform_06(self, d, sd=42):
        random.seed(sd); sub = list(range(256)); random.shuffle(sub)
        inv = [0] * 256
        for i in range(256): inv[sub[i]] = i
        return bytes(inv[b] for b in d)

    def transform_07(self, d):
        t = bytearray(d); r = self.repeat_count
        sh = len(d) % len(self.PI_DIGITS)
        pr = self.PI_DIGITS[sh:] + self.PI_DIGITS[:sh]
        sz = len(d) % 256
        for i in range(len(t)): t[i] ^= sz
        for _ in range(r):
            for i in range(len(t)): t[i] ^= pr[i % len(pr)]
        return bytes(t)
    reverse_transform_07 = transform_07

    def transform_08(self, d):
        t = bytearray(d); r = self.repeat_count
        sh = len(d) % len(self.PI_DIGITS)
        pr = self.PI_DIGITS[sh:] + self.PI_DIGITS[:sh]
        p = find_nearest_prime_around(len(d) % 256)
        for i in range(len(t)): t[i] ^= p
        for _ in range(r):
            for i in range(len(t)): t[i] ^= pr[i % len(pr)]
        return bytes(t)
    reverse_transform_08 = transform_08

    def transform_09(self, d):
        t = bytearray(d); r = self.repeat_count
        sh = len(d) % len(self.PI_DIGITS)
        pr = self.PI_DIGITS[sh:] + self.PI_DIGITS[:sh]
        p = find_nearest_prime_around(len(d) % 256)
        sd = self.get_seed(len(d) % len(self.seed_tables), len(d))
        for i in range(len(t)): t[i] ^= p ^ sd
        for _ in range(r):
            for i in range(len(t)): t[i] ^= pr[i % len(pr)] ^ (i % 256)
        return bytes(t)
    reverse_transform_09 = transform_09

    def transform_10(self, data):
        if not data: return b'\x00'
        cnt = sum(1 for i in range(len(data) - 1) if data[i:i + 2] == b'X1')
        n = (((cnt * 2) + 1) // 3) * 3 % 256
        t = bytearray(data)
        for i in range(len(t)): t[i] ^= n
        return bytes([n]) + bytes(t)
    def reverse_transform_10(self, data):
        if len(data) < 1: raise TransformError("T10")
        n = data[0]; t = bytearray(data[1:])
        for i in range(len(t)): t[i] ^= n
        return bytes(t)

    def transform_11(self, data):
        if not data: return b''
        t = bytearray(data); L = len(t)
        for i in range(L):
            fi = (i + L) % len(self.fibonacci)
            fv = self.fibonacci[fi] % 256
            pv = (i * 13 + L * 17) % 256
            t[i] ^= (fv ^ pv) % 256
        return bytes(t)
    reverse_transform_11 = transform_11

    def transform_12(self, data):
        t = bytearray(data)
        for i in range(len(t)): t[i] ^= self.fibonacci[i % len(self.fibonacci)] % 256
        return bytes(t)
    reverse_transform_12 = transform_12

    def transform_13(self, d):
        if not d: return b'\x00'
        r = self._calculate_repeats(d); cv = len(d) % 256; pv = []
        for _ in range(r): cv = find_nearest_prime_around(cv); pv.append(cv)
        t = bytearray(d); xv = pv[-1] if pv else 0
        for i in range(len(t)): t[i] ^= xv
        return bytes([(r - 1) % 256]) + bytes(t)
    def reverse_transform_13(self, d):
        if d == b'\x00': return b''
        if len(d) < 2: raise TransformError("T13")
        r = (d[0] + 1) % 256
        if r == 0: r = 256
        t = bytearray(d[1:]); cv = len(t) % 256; pv = []
        for _ in range(r): cv = find_nearest_prime_around(cv); pv.append(cv)
        xv = pv[-1] if pv else 0
        for i in range(len(t)): t[i] ^= xv
        return bytes(t)

    def transform_14(self, d):
        if not d: return b'\x00'
        return d + bytes([sum(d) % 256])
    def reverse_transform_14(self, d):
        if not d: raise TransformError("T14")
        return d[:-1]

    def transform_15(self, d):
        if not d: return b'\x00'
        t = bytearray(d); pi = len(d) % 256
        pv = self._get_pattern(3, pi)
        for i in range(0, len(t), 3):
            if i < len(t): t[i] = (t[i] + pv[i % len(pv)]) % 256
        return bytes([pi]) + bytes(t)
    def reverse_transform_15(self, d):
        if d == b'\x00': return b''
        if len(d) < 2: raise TransformError("T15")
        pi = d[0]; t = bytearray(d[1:]); pv = self._get_pattern(3, pi)
        for i in range(0, len(t), 3):
            if i < len(t): t[i] = (t[i] - pv[i % len(pv)]) % 256
        return bytes(t)

    def transform_16(self, data):
        if not data: return b''
        xv = (len(data) * 7 + 13) % 256
        return bytes(b ^ xv for b in data)
    reverse_transform_16 = transform_16

    def transform_17(self, data):
        if not data: return b''
        mask = bytes([0x24, 0x3F, 0x6A, 0x88])
        t = bytearray(data)
        for i in range(len(t)): t[i] ^= mask[i % len(mask)]
        return bytes(t)
    reverse_transform_17 = transform_17

    def transform_18(self, data):
        if not data: return b''
        decimal.getcontext().prec = 60
        pi = decimal.Decimal("3.14159265358979323846264338327950288419716939937510")
        basel = (pi * pi) / decimal.Decimal(6)
        s = str(basel).replace('.', '')[:max(10, len(data) // 2 + 5)]
        mask = bytes(int(s[i:i + 2]) % 256 for i in range(0, len(s), 2))
        t = bytearray(data)
        for i in range(len(t)): t[i] ^= mask[i % len(mask)]
        return bytes(t)
    reverse_transform_18 = transform_18

    def transform_19(self, data):
        if not data: return b''
        decimal.getcontext().prec = 60
        e = decimal.Decimal(1).exp(); inv_e = decimal.Decimal(1) / e
        s = str(inv_e).replace('.', '')[:max(10, len(data) // 2 + 5)]
        mask = bytes(int(s[i:i + 2]) % 256 for i in range(0, len(s), 2))
        t = bytearray(data)
        for i in range(len(t)): t[i] ^= mask[i % len(mask)]
        return bytes(t)
    reverse_transform_19 = transform_19

    def transform_20(self, data):
        if not data: return b''
        decimal.getcontext().prec = 60
        e = decimal.Decimal(1).exp(); five_e = decimal.Decimal(5) * e
        s = str(five_e).replace('.', '')[:max(10, len(data) // 2 + 5)]
        mask = bytes(int(s[i:i + 2]) % 256 for i in range(0, len(s), 2))
        t = bytearray(data)
        for i in range(len(t)): t[i] ^= mask[i % len(mask)]
        return bytes(t)
    reverse_transform_20 = transform_20

    def transform_21(self, data):
        if not data: return b''
        return bytes((b + 255) % 256 for b in data)
    def reverse_transform_21(self, data):
        if not data: return b''
        return bytes((b - 255) % 256 for b in data)

    # ---------------- 22-30 ----------------
    def transform_22(self, data): return base64.b64encode(data)
    def reverse_transform_22(self, data):
        try: return base64.b64decode(data, validate=False)
        except Exception as e: raise TransformError(f"b64: {e}")

    def transform_23(self, data):
        if not data: return b'\x00'
        try: text = data.decode('utf-8')
        except UnicodeDecodeError: return b'\x00' + data
        tokens = re.split(r'([A-Za-z0-9_]+)', text)
        wl = []; wi = {}; ts = []
        for i, tok in enumerate(tokens):
            if i % 2 == 1:
                wb = tok.encode('utf-8')
                idx = wi.get(wb)
                if idx is None:
                    idx = len(wl); wi[wb] = idx; wl.append(wb)
                ts.append((1, idx))
            else:
                ts.append((0, tok.encode('utf-8')))
        out = bytearray([1]) + struct.pack('>I', len(wl))
        for wb in wl: out += struct.pack('>I', len(wb)) + wb
        for typ, pay in ts:
            if typ == 1: out += b'\x01' + struct.pack('>I', pay)
            else: out += b'\x00' + struct.pack('>I', len(pay)) + pay
        tok_bytes = bytes(out)
        try:
            if self.reverse_transform_23(tok_bytes) == data: return tok_bytes
        except Exception: pass
        return b'\x00' + data

    def reverse_transform_23(self, data):
        if not data: return b''
        flag = data[0]
        if flag == 0: return data[1:]
        if flag != 1: raise TransformError(f"T23 flag {flag}")
        pos = 1
        if len(data) < pos + 4: raise TransformError("T23 short")
        nw = struct.unpack('>I', data[pos:pos + 4])[0]; pos += 4
        wl = []
        for _ in range(nw):
            if pos + 4 > len(data): raise TransformError("T23 t1")
            wlen = struct.unpack('>I', data[pos:pos + 4])[0]; pos += 4
            if pos + wlen > len(data): raise TransformError("T23 t2")
            wl.append(data[pos:pos + wlen]); pos += wlen
        out = bytearray()
        while pos < len(data):
            typ = data[pos]; pos += 1
            if typ == 1:
                if pos + 4 > len(data): raise TransformError("T23 i")
                idx = struct.unpack('>I', data[pos:pos + 4])[0]; pos += 4
                if idx >= len(wl): raise TransformError("T23 r")
                out += wl[idx]
            elif typ == 0:
                if pos + 4 > len(data): raise TransformError("T23 l")
                ll = struct.unpack('>I', data[pos:pos + 4])[0]; pos += 4
                if pos + ll > len(data): raise TransformError("T23 t3")
                out += data[pos:pos + ll]; pos += ll
            else: raise TransformError(f"T23 tok {typ}")
        return bytes(out)

    def transform_24(self, data): return self.transform_23(data)
    def reverse_transform_24(self, data): return self.reverse_transform_23(data)

    def _split_chunks(self, text):
        chunks = []
        for i, para in enumerate(re.split(r'(\n\n)', text)):
            if i % 2 == 1: chunks.append(para); continue
            for j, line in enumerate(re.split(r'(\n)', para)):
                if j % 2 == 1: chunks.append(line); continue
                for k, sent in enumerate(re.split(r'([.!?]+)', line)):
                    if k % 2 == 1: chunks.append(sent); continue
                    chunks.extend(re.split(r'(\s+|\b)', sent))
        return chunks

    def _dyn_tok(self, data, ib=3):
        try: text = data.decode('utf-8')
        except Exception: return b'\x00' + data
        chunks = self._split_chunks(text)
        freq = Counter(chunks)
        sc = sorted(freq.keys(), key=lambda x: (-freq[x], -len(x), x))
        ci = {ch: i for i, ch in enumerate(sc)}
        ne = len(sc)
        if ib == 2 and ne > 65535: ib = 3
        if ib == 3 and ne > 16777215: ib = 8
        h = bytearray([ib]) + struct.pack('>I', ne)
        for ch in sc:
            cb = ch.encode('utf-8')
            h += struct.pack('>I', len(cb)) + cb
        ts = bytearray()
        for ch in chunks:
            idx = ci[ch]
            if ib == 2: ts += struct.pack('>H', idx)
            elif ib == 3: ts += struct.pack('>I', idx)[1:4]
            else: ts += struct.pack('>Q', idx)
        return bytes(h) + bytes(ts)

    def _dyn_detok(self, data):
        if not data: return b''
        if data[0] == 0: return data[1:]
        ib = data[0]
        if ib not in (2, 3, 8): raise TransformError(f"dict ib {ib}")
        pos = 1
        if pos + 4 > len(data): raise TransformError("dict s")
        ne = struct.unpack('>I', data[pos:pos + 4])[0]; pos += 4
        dd = []
        for _ in range(ne):
            if pos + 4 > len(data): raise TransformError("dict t1")
            cl = struct.unpack('>I', data[pos:pos + 4])[0]; pos += 4
            if pos + cl > len(data): raise TransformError("dict t2")
            dd.append(data[pos:pos + cl].decode('utf-8')); pos += cl
        toks = []
        while pos < len(data):
            if ib == 2:
                if pos + 2 > len(data): break
                idx = struct.unpack('>H', data[pos:pos + 2])[0]; pos += 2
            elif ib == 3:
                if pos + 3 > len(data): break
                idx = struct.unpack('>I', b'\x00' + data[pos:pos + 3])[0]; pos += 3
            else:
                if pos + 8 > len(data): break
                idx = struct.unpack('>Q', data[pos:pos + 8])[0]; pos += 8
            if idx >= len(dd): raise TransformError(f"dict idx {idx}")
            toks.append(dd[idx])
        return ''.join(toks).encode('utf-8')

    def transform_25(self, data): return self._dyn_tok(data, 3)
    def reverse_transform_25(self, data): return self._dyn_detok(data)

    def transform_26(self, data):
        if not data: return b''
        secret = b"PJP_T26"
        r = bytearray()
        for idx in range(0, len(data), 1024):
            ch = data[idx:idx + 1024]; bn = idx // 1024
            h = hashlib.sha256(secret + struct.pack(">Q", bn)).digest()
            m = (h * ((len(ch) // len(h)) + 1))[:len(ch)]
            r.extend(a ^ b for a, b in zip(ch, m))
        return bytes(r)
    reverse_transform_26 = transform_26

    def transform_27(self, data):
        try: text = data.decode('utf-8')
        except UnicodeDecodeError: return b'\x00' + data
        for ch in text:
            if ch not in CHAR_TO_6BIT: return b'\x00' + data
        bits = []
        for ch in text:
            v = CHAR_TO_6BIT[ch]
            for i in range(5, -1, -1): bits.append((v >> i) & 1)
        pad = (8 - len(bits) % 8) % 8; bits.extend([0] * pad)
        out = bytearray()
        for i in range(0, len(bits), 8):
            b = 0
            for j in range(8): b = (b << 1) | bits[i + j]
            out.append(b)
        return b'\x01' + struct.pack('<I', len(text)) + bytes(out)

    def reverse_transform_27(self, data):
        if len(data) < 1: raise TransformError("T27")
        flag = data[0]
        if flag == 0: return data[1:]
        if flag != 1: raise TransformError(f"T27 {flag}")
        p = data[1:]
        if len(p) < 4: raise TransformError("T27 p")
        nc = struct.unpack('<I', p[:4])[0]; packed = p[4:]
        nb = (nc * 6 + 7) // 8
        if len(packed) != nb: raise TransformError("T27 mm")
        pb = (8 - (nc * 6) % 8) % 8
        if pb > 0 and packed:
            m = (1 << pb) - 1
            if packed[-1] & m: raise TransformError("T27 pad")
        bits = []
        for b in packed:
            for i in range(7, -1, -1): bits.append((b >> i) & 1)
        chars = []
        for i in range(nc):
            v = 0
            for j in range(6): v = (v << 1) | bits[i * 6 + j]
            if v >= 64: raise TransformError(f"T27 v {v}")
            chars.append(SIXBIT_TO_CHAR[v])
        return ''.join(chars).encode('utf-8')

    def transform_28(self, data):
        if not data: return b'\x00'
        pad = (3 - len(data) % 3) % 3
        padded = data + b'\x00' * pad
        out = bytearray([pad])
        for i in range(0, len(padded), 3):
            v = int.from_bytes(padded[i:i + 3], 'little')
            bi = i // 3; k = (bi * 65537 + 12345) & 0xFFFF
            out.extend(((v - k) % (1 << 24)).to_bytes(3, 'little'))
        return bytes(out)
    def reverse_transform_28(self, data):
        if data == b'\x00': return b''
        if not data: raise TransformError("T28")
        pad = data[0]; p = data[1:]
        if len(p) % 3 != 0: raise TransformError("T28 l")
        out = bytearray()
        for i in range(0, len(p), 3):
            v = int.from_bytes(p[i:i + 3], 'little')
            bi = i // 3; k = (bi * 65537 + 12345) & 0xFFFF
            out.extend(((v + k) % (1 << 24)).to_bytes(3, 'little'))
        if pad: out = out[:-pad]
        return bytes(out)

    def _best16(self, data):
        if len(data) < 3: return 0
        pad = (3 - len(data) % 3) % 3
        padded = data + b'\x00' * pad
        vals = [int.from_bytes(padded[i:i + 3], 'little') for i in range(0, len(padded), 3)]
        bk, bc = 0, float('inf')
        for k in range(65536):
            tr = [(v - k) & 0xFFFFFF for v in vals]
            m = sum(tr) // len(tr)
            c = sum(abs(t - m) for t in tr)
            if c < bc: bc = c; bk = k
            if c == 0: break
        return bk

    def transform_29(self, data):
        if not data: return b'\x00'
        k = self._best16(data)
        pad = (3 - len(data) % 3) % 3
        padded = data + b'\x00' * pad
        out = bytearray([pad]) + k.to_bytes(2, 'little')
        for i in range(0, len(padded), 3):
            v = int.from_bytes(padded[i:i + 3], 'little')
            out.extend(((v - k) % (1 << 24)).to_bytes(3, 'little'))
        return bytes(out)
    def reverse_transform_29(self, data):
        if data == b'\x00': return b''
        if len(data) < 3: raise TransformError("T29")
        pad = data[0]; k = int.from_bytes(data[1:3], 'little')
        p = data[3:]
        if len(p) % 3 != 0: raise TransformError("T29 l")
        out = bytearray()
        for i in range(0, len(p), 3):
            v = int.from_bytes(p[i:i + 3], 'little')
            out.extend(((v + k) % (1 << 24)).to_bytes(3, 'little'))
        if pad: out = out[:-pad]
        return bytes(out)

    def transform_30(self, data):
        if not data: return b'\x00'
        pad = (3 - len(data) % 3) % 3
        padded = data + b'\x00' * pad
        vals = [int.from_bytes(padded[i:i + 3], 'little') for i in range(0, len(padded), 3)]
        mean = sum(vals) // len(vals)
        sv = sorted(vals); med = sv[len(sv) // 2]
        cands = set()
        for b in [mean, med]:
            for o in [0, 1, -1, 10, -10, 100, -100, 1000, -1000]:
                cands.add((b + o) % (1 << 24))
        rng = random.Random(42)
        for _ in range(10): cands.add(rng.randint(0, (1 << 24) - 1))
        bk, bc = 0, float('inf')
        for k in cands:
            tr = [(v - k) & 0xFFFFFF for v in vals]
            m = sum(tr) // len(tr)
            c = sum(abs(t - m) for t in tr)
            if c < bc: bc = c; bk = k
        out = bytearray([pad]) + bk.to_bytes(3, 'little')
        for i in range(0, len(padded), 3):
            v = int.from_bytes(padded[i:i + 3], 'little')
            out.extend(((v - bk) % (1 << 24)).to_bytes(3, 'little'))
        return bytes(out)
    def reverse_transform_30(self, data):
        if data == b'\x00': return b''
        if len(data) < 4: raise TransformError("T30")
        pad = data[0]; k = int.from_bytes(data[1:4], 'little')
        p = data[4:]
        if len(p) % 3 != 0: raise TransformError("T30 l")
        out = bytearray()
        for i in range(0, len(p), 3):
            v = int.from_bytes(p[i:i + 3], 'little')
            out.extend(((v + k) % (1 << 24)).to_bytes(3, 'little'))
        if pad: out = out[:-pad]
        return bytes(out)

    def transform_31(self, d): return d
    reverse_transform_31 = transform_31
    def transform_32(self, d): return d
    reverse_transform_32 = transform_32

    # ---------------- PAQJP 33-40 ----------------
    def _paqjp_t23(self, data):
        if not data: return b'\x00' * 5
        bits = []
        for b in data:
            for i in range(7, -1, -1): bits.append((b >> i) & 1)
        return self._compress_bits(bits)
    def _paqjp_r23(self, data):
        if not data or data == b'\x00' * 5: return b''
        bits = self._decompress_bits(data)
        if not bits: return b''
        out = bytearray()
        for i in range(0, len(bits), 8):
            v = 0
            for j in range(i, min(i + 8, len(bits))): v = (v << 1) | bits[j]
            if i + 8 > len(bits): v <<= (8 - (len(bits) - i))
            out.append(v)
        return bytes(out)
    def _compress_bits(self, bits):
        obl = len(bits)
        if obl == 0: return b'\x00' * 5
        cur = bits[:]; pl = obl; pc = 0
        while pc < 255:
            pad = (4 - len(cur) % 4) % 4
            padded = cur + [0] * pad
            nc = len(padded) // 4; enc = []
            for i in range(nc):
                nib = (padded[i * 4] << 3) | (padded[i * 4 + 1] << 2) | (padded[i * 4 + 2] << 1) | padded[i * 4 + 3]
                L, cw = _CONST_DIAPASON_ITER_CODE[nib]
                for b in range(L - 1, -1, -1): enc.append((cw >> b) & 1)
            if len(enc) < pl: cur = enc; pl = len(enc); pc += 1
            else: break
        cbl = len(cur)
        hdr = struct.pack('>H', obl) + bytes([pc]) + struct.pack('>H', cbl)
        pad = (8 - len(cur) % 8) % 8; cur += [0] * pad
        out = bytearray()
        for i in range(0, len(cur), 8):
            v = 0
            for j in range(8): v = (v << 1) | cur[i + j]
            out.append(v)
        return hdr + bytes(out)
    def _decompress_bits(self, data):
        if len(data) < 5: raise TransformError("Diap")
        obl = struct.unpack('>H', data[:2])[0]
        pc = data[2]
        cbl = struct.unpack('>H', data[3:5])[0]
        pay = data[5:]
        bits = []
        for b in pay:
            for i in range(7, -1, -1): bits.append((b >> i) & 1)
        if len(bits) < cbl: raise TransformError("Diap p")
        cur = bits[:cbl]
        if pc == 0: return cur[:obl]
        for _ in range(pc):
            pos = 0; nb = len(cur); dn = []
            while pos < nb:
                m = False
                for L in range(2, 10):
                    if pos + L > nb: continue
                    cw = 0
                    for k in range(L): cw = (cw << 1) | cur[pos + k]
                    if (L, cw) in _CONST_DIAPASON_ITER_DECODE:
                        dn.append(_CONST_DIAPASON_ITER_DECODE[(L, cw)])
                        pos += L; m = True; break
                if not m: raise TransformError("Diap cw")
            new_bits = []
            for nib in dn:
                for j in range(3, -1, -1): new_bits.append((nib >> j) & 1)
            cur = new_bits
        if len(cur) < obl: raise TransformError("Diap s")
        return cur[:obl]

    def _paqjp_t24(self, data):
        if not data: return struct.pack('>I', 0)
        MAX = 43; bits = []; i = 0; n = len(data)
        while i < n:
            cl = min(MAX, n - i); ch = data[i:i + cl]
            f = ch[0]; same = all(b == f for b in ch)
            if same:
                self._append_bits(bits, 1, 1); self._append_bits(bits, f, 8)
                self._append_bits(bits, cl - 1, 6)
            else:
                self._append_bits(bits, 0, 1); self._append_bits(bits, cl, 6)
                for b in ch: self._append_bits(bits, b, 8)
            i += cl
        pad = (8 - len(bits) % 8) % 8; self._append_bits(bits, 0, pad)
        out = bytearray()
        for j in range(0, len(bits), 8):
            b = 0
            for k in range(8): b = (b << 1) | bits[j + k]
            out.append(b)
        return struct.pack('>I', len(data)) + bytes(out)
    def _paqjp_r24(self, data):
        if not data: return b''
        if len(data) < 4: raise TransformError("BlkRun")
        ol = struct.unpack('>I', data[:4])[0]
        p = data[4:]
        bits = []
        for b in p:
            for i in range(7, -1, -1): bits.append((b >> i) & 1)
        pos = 0; nb = len(bits); out = bytearray()
        while pos < nb and len(out) < ol:
            if pos + 1 > nb: break
            flag = self._read_bits(bits, pos, 1); pos += 1
            if flag == 1:
                if pos + 14 > nb: raise TransformError("BlkRun t")
                bv = self._read_bits(bits, pos, 8); pos += 8
                cm = self._read_bits(bits, pos, 6); pos += 6
                rl = min(cm + 1, ol - len(out))
                out.extend([bv] * rl)
            else:
                if pos + 6 > nb: raise TransformError("BlkRun l")
                cl = self._read_bits(bits, pos, 6); pos += 6
                if cl == 0: break
                if pos + cl * 8 > nb: raise TransformError("BlkRun b")
                for _ in range(cl):
                    out.append(self._read_bits(bits, pos, 8)); pos += 8
        return bytes(out[:ol])

    def _paqjp_t25(self, data):
        if not data: return b'\x01'
        n = 3; res = bytearray(data)
        for i in range(len(res)): res[i] = (pow(res[i] + 1, n, 257) - 1) & 0xFF
        return bytes([n]) + bytes(res)
    def _paqjp_r25(self, data):
        if data == b'\x01': return b''
        if len(data) < 2: raise TransformError("FLT25")
        n = data[0]; inv = mod_inv(n, 256)
        if inv is None: raise TransformError(f"FLT25 {n}")
        res = bytearray(data[1:])
        for i in range(len(res)): res[i] = (pow(res[i] + 1, inv, 257) - 1) & 0xFF
        return bytes(res)

    def _paqjp_t26(self, data):
        if not data: return b'\x01\x00'
        n = (len(data) * 7 + 13) & 0xFFFF
        if n % 2 == 0: n ^= 1
        e = pow(n, 16777216, 256) | 1
        res = bytearray(data)
        for i in range(len(res)): res[i] = (pow(res[i] + 1, e, 257) - 1) & 0xFF
        return bytes([n & 0xFF, (n >> 8) & 0xFF]) + bytes(res)
    def _paqjp_r26(self, data):
        if data == b'\x01\x00': return b''
        if len(data) < 2: raise TransformError("FLT26")
        n = data[0] | (data[1] << 8)
        if n % 2 == 0: n ^= 1
        e = pow(n, 16777216, 256) | 1
        inv = mod_inv(e, 256)
        if inv is None: raise TransformError(f"FLT26 {e}")
        res = bytearray(data[2:])
        for i in range(len(res)): res[i] = (pow(res[i] + 1, inv, 257) - 1) & 0xFF
        return bytes(res)

    def _paqjp_t27(self, data):
        if not data:
            o = bytearray(b'\x00\x00\x00\x00\x01\x00'); o.extend(b'\x00' * 1024)
            return bytes(o)
        BS = 1024; tb = (len(data) + BS - 1) // BS
        out = bytearray(); out.extend(len(data).to_bytes(4, 'big'))
        for bi in range(tb):
            s = bi * BS; e = min(s + BS, len(data))
            ch = data[s:e]; pad = BS - len(ch)
            if pad: ch = ch + b'\x00' * pad
            n = ((len(data) * 7 + bi * 13 + 1) & 0xFFFF) | 1
            e_ = pow(n, 16777216, 256) | 1
            e200 = pow(e_, 200, 256)
            t = bytearray(ch)
            for i in range(BS): t[i] = (pow(t[i] + 1, e200, 257) - 1) & 0xFF
            out.append(n & 0xFF); out.append((n >> 8) & 0xFF); out.extend(t)
        return bytes(out)
    def _paqjp_r27(self, data):
        if len(data) < 4: raise TransformError("FLT27")
        ol = int.from_bytes(data[:4], 'big')
        p = data[4:]; BS = 1024; btl = 2 + BS
        if len(p) % btl != 0: raise TransformError("FLT27 a")
        nb = len(p) // btl; dec = bytearray()
        for bi in range(nb):
            off = bi * btl
            n = p[off] | (p[off + 1] << 8); ch = p[off + 2:off + 2 + BS]
            n |= 1
            e_ = pow(n, 16777216, 256) | 1
            e200 = pow(e_, 200, 256)
            inv = mod_inv(e200, 256)
            if inv is None: raise TransformError(f"FLT27 {e200}")
            for i in range(BS): dec.append((pow(ch[i] + 1, inv, 257) - 1) & 0xFF)
        return bytes(dec[:ol])

    def _compress_backend_with_flag(self, data):
        cands = []
        try: cands.append((1, zstd_cctx.compress(data)))
        except Exception: pass
        if paq is not None:
            try: cands.append((2, paq.compress(data)))
            except Exception: pass
        if HAS_BROTLI:
            try: cands.append((3, brotli.compress(data, quality=11)))
            except Exception: pass
        cands.append((0, data))
        bf, bd = min(cands, key=lambda x: len(x[1]))
        return bytes([bf]) + bd
    def _decompress_backend_with_flag(self, data):
        if not data: return b''
        f = data[0]; p = data[1:]
        if f == 0: return p
        if f == 1: return zstd_dctx.decompress(p)
        if f == 2 and paq is not None: return paq.decompress(p)
        if f == 3 and HAS_BROTLI: return brotli.decompress(p)
        raise TransformError(f"bkf {f}")

    def _paqjp_t28(self, data):
        BS = 1024
        if not data:
            ch = b'\x00' * BS; c = self._compress_backend_with_flag(ch)
            o = bytearray(struct.pack('>I', 0))
            o += b'\x01\x00' + bytes([(len(c) >> 8) & 0xFF, len(c) & 0xFF]) + c
            return bytes(o)
        tb = (len(data) + BS - 1) // BS
        out = bytearray(); out.extend(len(data).to_bytes(4, 'big'))
        for bi in range(tb):
            s = bi * BS; e = min(s + BS, len(data))
            ch = data[s:e] + b'\x00' * (BS - len(data[s:e]))
            n = ((len(data) * 7 + bi * 13 + 1) & 0xFFFF) | 1
            e_ = pow(n, 16777216, 256) | 1; e200 = pow(e_, 200, 256)
            t = bytearray(ch)
            for i in range(BS): t[i] = (pow(t[i] + 1, e200, 257) - 1) & 0xFF
            c = self._compress_backend_with_flag(bytes(t))
            out += bytes([n & 0xFF, (n >> 8) & 0xFF,
                          (len(c) >> 8) & 0xFF, len(c) & 0xFF]) + c
        return bytes(out)
    def _paqjp_r28(self, data):
        if len(data) < 4: raise TransformError("FLT28")
        ol = int.from_bytes(data[:4], 'big'); p = data[4:]
        pos = 0; dec = bytearray()
        while pos < len(p):
            n = p[pos] | (p[pos + 1] << 8); pos += 2
            cl = (p[pos] << 8) | p[pos + 1]; pos += 2
            cb = p[pos:pos + cl]; pos += cl
            b = self._decompress_backend_with_flag(cb)
            n |= 1; e_ = pow(n, 16777216, 256) | 1; e200 = pow(e_, 200, 256)
            inv = mod_inv(e200, 256)
            if inv is None: raise TransformError(f"FLT28 {e200}")
            t = bytearray(b)
            for i in range(len(t)): t[i] = (pow(t[i] + 1, inv, 257) - 1) & 0xFF
            dec.extend(t)
        return bytes(dec[:ol])

    def _paqjp_t29(self, data):
        BS = 32
        if not data:
            ch = b'\x00' * BS; c = self._compress_backend_with_flag(ch)
            o = bytearray(struct.pack('>I', 0))
            o += b'\x01\x00' + bytes([(len(c) >> 8) & 0xFF, len(c) & 0xFF]) + c
            return bytes(o)
        tb = (len(data) + BS - 1) // BS
        out = bytearray(); out.extend(len(data).to_bytes(4, 'big'))
        for bi in range(tb):
            s = bi * BS; e = min(s + BS, len(data))
            ch = data[s:e] + b'\x00' * (BS - len(data[s:e]))
            n = ((len(data) * 7 + bi * 13 + 1) & 0xFFFF) | 1
            c = self._compress_backend_with_flag(bytes(ch))
            out += bytes([n & 0xFF, (n >> 8) & 0xFF,
                          (len(c) >> 8) & 0xFF, len(c) & 0xFF]) + c
        return bytes(out)
    def _paqjp_r29(self, data):
        if len(data) < 4: raise TransformError("FLT29")
        ol = int.from_bytes(data[:4], 'big'); p = data[4:]
        pos = 0; dec = bytearray()
        while pos < len(p):
            n = p[pos] | (p[pos + 1] << 8); pos += 2
            cl = (p[pos] << 8) | p[pos + 1]; pos += 2
            cb = p[pos:pos + cl]; pos += cl
            dec.extend(self._decompress_backend_with_flag(cb))
        return bytes(dec[:ol])

    def _paqjp_t30(self, data):
        BS = 33
        if not data:
            ch = b'\x00' * BS; c = self._compress_backend_with_flag(ch)
            o = bytearray(struct.pack('>I', 0))
            o += b'\x01\x01' + bytes([(len(c) >> 8) & 0xFF, len(c) & 0xFF]) + c
            return bytes(o)
        tb = (len(data) + BS - 1) // BS
        out = bytearray(); out.extend(len(data).to_bytes(4, 'big'))
        for bi in range(tb):
            s = bi * BS; e = min(s + BS, len(data))
            ch = data[s:e] + b'\x00' * (BS - len(data[s:e]))
            h = hashlib.sha256(ch + bytes([bi & 0xFF, (len(data) >> 8) & 0xFF,
                                           len(data) & 0xFF])).digest()
            enc = bytes([32]) + h
            c = self._compress_backend_with_flag(ch)
            out += enc + bytes([(len(c) >> 8) & 0xFF, len(c) & 0xFF]) + c
        return bytes(out)
    def _paqjp_r30(self, data):
        if len(data) < 4: raise TransformError("FLT30")
        ol = int.from_bytes(data[:4], 'big'); p = data[4:]
        pos = 0; dec = bytearray()
        while pos < len(p):
            Ln = p[pos]; pos += 1
            if Ln > 32 or pos + Ln > len(p): raise TransformError("FLT30 n")
            pos += Ln
            cl = (p[pos] << 8) | p[pos + 1]; pos += 2
            cb = p[pos:pos + cl]; pos += cl
            dec.extend(self._decompress_backend_with_flag(cb))
        return bytes(dec[:ol])

    # ---------------- 41-47 ----------------
    def transform_41(self, data):
        if not data: return b''
        t = bytearray(data); m = bytes([0x27, 0x03])
        for i in range(min(len(t), 8)): t[i] ^= m[i % 2]
        return bytes(t)
    reverse_transform_41 = transform_41
    def transform_42(self, data):
        if not data: return b''
        t = bytearray(data); m = bytes([0x27, 0x03])
        for i in range(len(t)): t[i] ^= m[i % 2]
        return bytes(t)
    reverse_transform_42 = transform_42
    def transform_43(self, data):
        if not data: return b''
        t = bytearray(data); m = bytes([0x10, 0x00, 0x00])
        for i in range(0, len(t), 3):
            for j in range(min(3, len(t) - i)): t[i + j] ^= m[j]
        return bytes(t)
    reverse_transform_43 = transform_43
    def transform_44(self, data):
        if not data: return b''
        return base64.b64encode(data)
    def reverse_transform_44(self, data):
        if not data: return b''
        try: return base64.b64decode(data, validate=False)
        except Exception as e: raise TransformError(f"b64-44 {e}")

    @staticmethod
    def _huffman_code_lengths(freq):
        heap = [(f, i, i) for i, f in enumerate(freq) if f > 0]
        if not heap: return [0] * len(freq)
        if len(heap) == 1:
            L = [0] * len(freq); L[heap[0][2]] = 1; return L
        heapq.heapify(heap); nid = len(freq)
        while len(heap) > 1:
            f1, _, n1 = heapq.heappop(heap); f2, _, n2 = heapq.heappop(heap)
            heapq.heappush(heap, (f1 + f2, nid, (n1, n2))); nid += 1
        L = [0] * len(freq)
        def trav(n, d):
            if isinstance(n, int): L[n] = d
            else: trav(n[0], d + 1); trav(n[1], d + 1)
        trav(heap[0][2], 0); return L
    @staticmethod
    def _huffman_canonical_codes(L):
        syms = sorted(range(len(L)), key=lambda s: (L[s], s))
        codes = {}; c = 0; pl = 0; first = True
        for s in syms:
            cl = L[s]
            if cl == 0: continue
            if first: pl = cl; first = False
            elif cl != pl: c <<= (cl - pl); pl = cl
            codes[s] = (c, cl); c += 1
        return codes

    def transform_45(self, data):
        if not data: return b''
        freq = [0] * 256
        for b in data: freq[b] += 1
        cl = self._huffman_code_lengths(freq); codes = self._huffman_canonical_codes(cl)
        hdr = bytearray(len(data).to_bytes(4, 'big')); hdr.extend(cl)
        bits = []
        for b in data:
            c, n = codes[b]
            for i in range(n - 1, -1, -1): bits.append((c >> i) & 1)
        pad = (8 - len(bits) % 8) % 8; bits.extend([0] * pad)
        out = bytearray()
        for i in range(0, len(bits), 8):
            v = 0
            for j in range(8): v = (v << 1) | bits[i + j]
            out.append(v)
        return bytes(hdr) + bytes(out)
    def reverse_transform_45(self, data):
        if not data: return b''
        if len(data) < 4 + 256: raise TransformError("Huff")
        ol = int.from_bytes(data[:4], 'big'); cl = list(data[4:260]); p = data[260:]
        if ol == 0: return b''
        if max(cl) > 32: raise TransformError("Huff l")
        code_to = {}
        syms = sorted(range(256), key=lambda s: (cl[s], s))
        c = 0; pl = 0; first = True
        for s in syms:
            L = cl[s]
            if L == 0: continue
            if first: pl = L; first = False
            elif L != pl: c <<= (L - pl); pl = L
            code_to[(L, c)] = s; c += 1
        bits = []
        for b in p:
            for i in range(7, -1, -1): bits.append((b >> i) & 1)
        pos = 0; nb = len(bits); out = bytearray()
        mx = max(cl) if any(cl) else 0
        while pos < nb and len(out) < ol:
            f = False
            for L in range(1, mx + 1):
                if pos + L > nb: break
                v = 0
                for j in range(L): v = (v << 1) | bits[pos + j]
                if (L, v) in code_to:
                    out.append(code_to[(L, v)]); pos += L; f = True; break
            if not f: raise TransformError(f"Huff p {pos}")
        if len(out) != ol: raise TransformError(f"Huff {len(out)}!={ol}")
        return bytes(out)

    def transform_46(self, data):
        if not data: return b''
        t = bytearray(data); m = self.mask_46
        for i in range(len(t)): t[i] ^= m[i % len(m)]
        return bytes(t)
    reverse_transform_46 = transform_46
    def transform_47(self, data):
        if not data: return b''
        t = bytearray(data); tl = len(self.mod_state_table)
        if tl == 0: return data
        for i in range(len(t)): t[i] ^= self.mod_state_table[i % tl][0]
        return bytes(t)
    reverse_transform_47 = transform_47

    def transform_57(self, data):
        if len(data) < 4:
            pad = 4 - len(data); k = 0
            return bytes([pad]) + k.to_bytes(4, 'little') + data + b'\x00' * pad
        n = len(data); pad = (4 - n % 4) % 4
        padded = data + b'\x00' * pad
        blocks = [padded[i:i + 4] for i in range(0, len(padded), 4)]
        mc, _ = Counter(blocks).most_common(1)[0]
        k = int.from_bytes(mc, 'little')
        out = bytearray()
        for blk in blocks:
            out.extend((int.from_bytes(blk, 'little') ^ k).to_bytes(4, 'little'))
        return bytes([pad]) + k.to_bytes(4, 'little') + bytes(out)
    def reverse_transform_57(self, data):
        if len(data) < 5: raise TransformError("T57")
        pad = data[0]; k = int.from_bytes(data[1:5], 'little')
        p = data[5:]
        if len(p) % 4 != 0: raise TransformError("T57 l")
        out = bytearray()
        for i in range(0, len(p), 4):
            out.extend((int.from_bytes(p[i:i + 4], 'little') ^ k).to_bytes(4, 'little'))
        if pad: out = out[:-pad]
        return bytes(out)

    def _dynamic(self, n):
        def tf(data):
            if not data: return b''
            sd = self.get_seed(n % len(self.seed_tables), len(data))
            return bytes(b ^ sd for b in data)
        return tf, tf

    def transform_256(self, d): return d
    reverse_transform_256 = transform_256

    def _build_transform_maps(self):
        self.fwd_transforms = {}
        self.rev_transforms = {}
        for i in range(1, 22):
            self.fwd_transforms[i] = getattr(self, f"transform_{i:02d}")
            self.rev_transforms[i] = getattr(self, f"reverse_transform_{i:02d}")
        self.fwd_transforms[22] = self.transform_22; self.rev_transforms[22] = self.reverse_transform_22
        self.fwd_transforms[23] = self.transform_23; self.rev_transforms[23] = self.reverse_transform_23
        self.fwd_transforms[24] = self.transform_24; self.rev_transforms[24] = self.reverse_transform_24
        self.fwd_transforms[25] = self.transform_25; self.rev_transforms[25] = self.reverse_transform_25
        self.fwd_transforms[26] = self.transform_26; self.rev_transforms[26] = self.reverse_transform_26
        self.fwd_transforms[27] = self.transform_27; self.rev_transforms[27] = self.reverse_transform_27
        self.fwd_transforms[28] = self.transform_28; self.rev_transforms[28] = self.reverse_transform_28
        self.fwd_transforms[29] = self.transform_29; self.rev_transforms[29] = self.reverse_transform_29
        self.fwd_transforms[30] = self.transform_30; self.rev_transforms[30] = self.reverse_transform_30
        self.fwd_transforms[31] = self.transform_31; self.rev_transforms[31] = self.reverse_transform_31
        self.fwd_transforms[32] = self.transform_32; self.rev_transforms[32] = self.reverse_transform_32
        self.fwd_transforms[33] = self._paqjp_t23; self.rev_transforms[33] = self._paqjp_r23
        self.fwd_transforms[34] = self._paqjp_t24; self.rev_transforms[34] = self._paqjp_r24
        self.fwd_transforms[35] = self._paqjp_t25; self.rev_transforms[35] = self._paqjp_r25
        self.fwd_transforms[36] = self._paqjp_t26; self.rev_transforms[36] = self._paqjp_r26
        self.fwd_transforms[37] = self._paqjp_t27; self.rev_transforms[37] = self._paqjp_r27
        self.fwd_transforms[38] = self._paqjp_t28; self.rev_transforms[38] = self._paqjp_r28
        self.fwd_transforms[39] = self._paqjp_t29; self.rev_transforms[39] = self._paqjp_r29
        self.fwd_transforms[40] = self._paqjp_t30; self.rev_transforms[40] = self._paqjp_r30
        self.fwd_transforms[41] = self.transform_41; self.rev_transforms[41] = self.reverse_transform_41
        self.fwd_transforms[42] = self.transform_42; self.rev_transforms[42] = self.reverse_transform_42
        self.fwd_transforms[43] = self.transform_43; self.rev_transforms[43] = self.reverse_transform_43
        self.fwd_transforms[44] = self.transform_44; self.rev_transforms[44] = self.reverse_transform_44
        self.fwd_transforms[45] = self.transform_45; self.rev_transforms[45] = self.reverse_transform_45
        self.fwd_transforms[46] = self.transform_46; self.rev_transforms[46] = self.reverse_transform_46
        self.fwd_transforms[47] = self.transform_47; self.rev_transforms[47] = self.reverse_transform_47
        for i in range(48, 57):
            f, r = self._dynamic(i); self.fwd_transforms[i] = f; self.rev_transforms[i] = r
        self.fwd_transforms[57] = self.transform_57; self.rev_transforms[57] = self.reverse_transform_57
        for i in range(58, 256):
            f, r = self._dynamic(i); self.fwd_transforms[i] = f; self.rev_transforms[i] = r
        self.fwd_transforms[256] = self.transform_256; self.rev_transforms[256] = self.reverse_transform_256

    def _precompute_quantum_transforms(self):
        if not USE_QUANTUM or not HAS_QISKIT: return
        q = self.QUANTUM_QUBITS
        if q > 49: q = 49
        size = 1 << q
        bs = size if q <= 12 else 1024
        for i in range(8):
            rng = random.Random(1000 + i)
            perm = list(range(size)); rng.shuffle(perm)
            if len(perm) > bs: perm = perm[:bs]
            inv = [0] * len(perm)
            for j, p in enumerate(perm): inv[p] = j
            def fwd(data, p=perm): return bytes(p[b] if b < len(p) else b for b in data)
            def rev(data, iv=inv): return bytes(iv[b] if b < len(iv) else b for b in data)
            self.fwd_transforms[256 + i + 1] = fwd
            self.rev_transforms[256 + i + 1] = rev

    # ---------------- Header ----------------
    def _encode_marker_single(self, t):
        if t <= 252: return bytes([t - 1])
        elif t <= 255: return bytes([254, t - 253])
        return bytes([255, (t - 256) // 256, (t - 256) % 256])
    def _encode_marker_raw(self): return bytes([252])
    def _decode_header(self, data):
        if len(data) < 1: return 0, ()
        f = data[0]
        if f < 252: return 1, (f + 1,)
        if f == 252: return 1, ()
        if f == 254:
            if len(data) < 2: return 0, ()
            x = data[1]
            return (2, (253 + x,)) if x <= 3 else (0, ())
        if f == 255:
            if len(data) < 3: return 0, ()
            return 3, (256 + data[1] * 256 + data[2],)
        return 0, ()

    # ---------------- Backends ----------------
    def _compress_backend(self, data):
        cands = [(0, data)]
        try:
            c = zstd_cctx.compress(data)
            if len(c) >= 4 and c[:4] == b'\x28\xb5\x2f\xfd': c = c[4:]
            cands.append((1, c))
        except Exception: pass
        if paq is not None:
            try:
                pd = paq.compress(data)
                if len(pd) >= 7 and pd[:4] == b'\x00\x63\x00\x00' and pd[-3:] == b'\xff\xff\xff':
                    cands.append((3, pd[4:-3]))
                else:
                    cands.append((2, pd))
            except Exception: pass
        if HAS_BROTLI:
            try: cands.append((4, brotli.compress(data, quality=11)))
            except Exception: pass
        bf, bd = min(cands, key=lambda x: len(x[1]))
        return bytes([bf]) + bd
    def _decompress_backend(self, data):
        if len(data) < 1: return None
        f = data[0]; p = data[1:]
        if f == 0: return p
        if f == 1:
            try: return zstd_dctx.decompress(b'\x28\xb5\x2f\xfd' + p)
            except Exception: return None
        if f == 2 and paq is not None:
            try: return paq.decompress(p)
            except Exception: return None
        if f == 3 and paq is not None:
            try: return paq.decompress(b'\x00\x63\x00\x00' + p + b'\xff\xff\xff')
            except Exception: return None
        if f == 4 and HAS_BROTLI:
            try: return brotli.decompress(p)
            except Exception: return None
        return None

    # ---------------- LZH ----------------
    def _lz77_tokenize(self, data):
        tokens = []; i = 0; n = len(data)
        while i < n:
            bl = 0; bd = 0
            sw = max(0, i - self.WINDOW_SIZE)
            for j in range(sw, i):
                if data[j] != data[i]: continue
                k = 0
                while i + k < n and j + k < i and data[j + k] == data[i + k]:
                    k += 1
                    if k >= self.MAX_MATCH: break
                if k >= self.MIN_MATCH and k > bl:
                    bl = k; bd = i - j
                    if bl == self.MAX_MATCH: break
            if bl >= self.MIN_MATCH:
                tokens.append(('M', bd, bl)); i += bl
            else:
                tokens.append(('L', data[i], None)); i += 1
        return tokens
    def _lz77_untokenize(self, tokens):
        out = bytearray()
        for t in tokens:
            if t[0] == 'L': out.append(t[1])
            else:
                d, l = t[1], t[2]
                st = len(out) - d
                for k in range(l): out.append(out[st + k])
        return bytes(out)
    def _encode_lzh(self, data):
        tokens = self._lz77_tokenize(data)
        lf = [0] * 256; df = [0] * (self.MAX_DIST + 1); nf = [0] * (self.MAX_MATCH + 1)
        for t in tokens:
            if t[0] == 'L': lf[t[1]] += 1
            else: df[t[1]] += 1; nf[t[2]] += 1
        lcl = self._huffman_code_lengths(lf)
        dcl = self._huffman_code_lengths(df)
        ncl = self._huffman_code_lengths(nf)
        lcs = self._huffman_canonical_codes(lcl)
        dcs = self._huffman_canonical_codes(dcl)
        ncs = self._huffman_canonical_codes(ncl)
        bits = []
        tc = len(tokens)
        for b in struct.pack('>I', tc):
            for i in range(8): bits.append((b >> (7 - i)) & 1)
        for t in tokens:
            if t[0] == 'L':
                bits.append(0)
                c, n = lcs[t[1]]
                for i in range(n - 1, -1, -1): bits.append((c >> i) & 1)
            else:
                bits.append(1)
                cd, nd = dcs[t[1]]
                for i in range(nd - 1, -1, -1): bits.append((cd >> i) & 1)
                cl, nl = ncs[t[2]]
                for i in range(nl - 1, -1, -1): bits.append((cl >> i) & 1)
        pad = (8 - len(bits) % 8) % 8; bits.extend([0] * pad)
        def pk(L): return b''.join(struct.pack('>H', x) for x in L)
        header = bytearray()
        header.extend(pk(lcl)); header.extend(pk(dcl)); header.extend(pk(ncl))
        out = bytearray(header)
        for i in range(0, len(bits), 8):
            b = 0
            for j in range(8): b = (b << 1) | bits[i + j]
            out.append(b)
        return bytes(out)
    def _decode_lzh(self, data):
        LL = 256 * 2; DL = 2049 * 2; NL = 2049 * 2
        if len(data) < LL + DL + NL: raise TransformError("LZH short")
        pos = 0
        lcl = [struct.unpack('>H', data[i:i + 2])[0] for i in range(pos, pos + LL, 2)]; pos += LL
        dcl = [struct.unpack('>H', data[i:i + 2])[0] for i in range(pos, pos + DL, 2)]; pos += DL
        ncl = [struct.unpack('>H', data[i:i + 2])[0] for i in range(pos, pos + NL, 2)]; pos += NL
        def bdt(L):
            syms = sorted(range(len(L)), key=lambda s: (L[s], s))
            d = {}; c = 0; pl = 0; first = True
            for s in syms:
                cl = L[s]
                if cl == 0: continue
                if first: pl = cl; first = False
                elif cl != pl: c <<= (cl - pl); pl = cl
                d[(cl, c)] = s; c += 1
            return d
        ld = bdt(lcl); dd = bdt(dcl); nd = bdt(ncl)
        mlb = max(lcl) if any(lcl) else 0
        mdb = max(dcl) if any(dcl) else 0
        mnb = max(ncl) if any(ncl) else 0
        p = data[pos:]
        if len(p) < 4: raise TransformError("LZH empty")
        tc = struct.unpack('>I', p[:4])[0]
        bits = []
        for byte in p[4:]:
            for i in range(7, -1, -1): bits.append((byte >> i) & 1)
        bpos = 0; tokens = []
        for _ in range(tc):
            if bpos >= len(bits): raise TransformError("LZH eof")
            flag = bits[bpos]; bpos += 1
            if flag == 0:
                found = False
                for cl in range(1, mlb + 1):
                    if bpos + cl > len(bits): break
                    v = 0
                    for j in range(cl): v = (v << 1) | bits[bpos + j]
                    if (cl, v) in ld:
                        tokens.append(('L', ld[(cl, v)], None)); bpos += cl
                        found = True; break
                if not found: raise TransformError("LZH lit")
            else:
                fd = False
                for cl in range(1, mdb + 1):
                    if bpos + cl > len(bits): break
                    v = 0
                    for j in range(cl): v = (v << 1) | bits[bpos + j]
                    if (cl, v) in dd:
                        dist = dd[(cl, v)]; bpos += cl; fd = True; break
                if not fd: raise TransformError("LZH dist")
                fn = False
                for cl in range(1, mnb + 1):
                    if bpos + cl > len(bits): break
                    v = 0
                    for j in range(cl): v = (v << 1) | bits[bpos + j]
                    if (cl, v) in nd:
                        length = nd[(cl, v)]; bpos += cl; fn = True; break
                if not fn: raise TransformError("LZH len")
                tokens.append(('M', dist, length))
        return self._lz77_untokenize(tokens)

    # ---------------- Pipelines ----------------
    def _raw_pipeline(self, data, time_limit=None):
        if time_limit is None: time_limit = self.ULTRA_TIME_LIMIT
        st = time.time()
        best = None; bl = float('inf')
        def try_c(h, t):
            nonlocal best, bl
            c = h + self._compress_backend(t)
            if len(c) < bl: best = c; bl = len(c)
        try_c(self._encode_marker_raw(), data)
        for t in range(1, 257):
            if time_limit and time.time() - st > time_limit: break
            try:
                tr = self.fwd_transforms[t](data)
                if not self._verify_lossless(data, tr, self.rev_transforms[t]): continue
                try_c(self._encode_marker_single(t), tr)
            except Exception: continue
        if best is None: best = self._encode_marker_raw() + self._compress_backend(data)
        d, _ = self._decompress_auto(best)
        if d == data: return best
        return self._encode_marker_raw() + self._compress_backend(data)

    def _lzh_pipeline(self, data, time_limit=None):
        if time_limit is None: time_limit = self.ULTRA_TIME_LIMIT
        st = time.time()
        best = None; bl = float('inf')
        def try_c(h, t):
            nonlocal best, bl
            lzh = self._encode_lzh(t)
            c = h + b'\xFF' + lzh
            if len(c) < bl: best = c; bl = len(c)
        try_c(self._encode_marker_raw(), data)
        for t in range(1, 257):
            if time_limit and time.time() - st > time_limit: break
            try:
                tr = self.fwd_transforms[t](data)
                if not self._verify_lossless(data, tr, self.rev_transforms[t]): continue
                try_c(self._encode_marker_single(t), tr)
            except Exception: continue
        if best is None: best = self._encode_marker_raw() + self._compress_backend(data)
        return best

    def _decompress_auto(self, data):
        off, seq = self._decode_header(data)
        if off == 0: raise DecompressionError("Bad header")
        p = data[off:]
        if not p: raise DecompressionError("Empty")
        r = self._decompress_backend(p)
        if r is None: raise DecompressionError("Backend failed")
        if not seq: return r, None
        return self._reverse_sequence(r, seq), seq

    def _decompress_lzh_pipeline(self, data):
        off, seq = self._decode_header(data)
        if off == 0: return None
        if len(data) <= off or data[off] != 0xFF: return None
        lzh_data = data[off + 1:]
        transformed = self._decode_lzh(lzh_data)
        if transformed is None: return None
        if not seq: return transformed
        return self._reverse_sequence(transformed, seq)

    def _reverse_sequence(self, data, seq):
        r = data
        for t in reversed(seq): r = self.rev_transforms[t](r)
        return r

    # ---------------- SHA-256 wrapper ----------------
    def _wrap_with_hash(self, payload, original):
        return MAGIC + hashlib.sha256(original).digest() + payload
    def _unwrap_and_check(self, blob):
        if not blob.startswith(MAGIC): raise IntegrityError("Not PJP4.")
        if len(blob) < HEADER_LEN: raise IntegrityError("Truncated PJP4.")
        return blob[MAGIC_LEN:HEADER_LEN], blob[HEADER_LEN:]

    # ---------------- File I/O ----------------
    def _atomic_write(self, path, data):
        d = os.path.dirname(path) or '.'
        fd, tmp = tempfile.mkstemp(prefix=os.path.basename(path) + '.tmp', dir=d)
        try: os.write(fd, data); os.fsync(fd)
        finally: os.close(fd)
        os.replace(tmp, path)

    def compress_file_dual(self, infile, time_limit=None):
        try:
            with open(infile, 'rb') as f: data = f.read()
        except Exception as e:
            print(f"Error reading: {e}"); return

        print(f"\nInput: {len(data)} bytes")
        print("=" * 62)
        print("Method A: 256 transforms + PAQ/Zstd/Brotli → .pjp2")
        try: payload_a = self._raw_pipeline(data, time_limit)
        except Exception as e: print(f"  A failed: {e}"); return
        try:
            check_a, _ = self._decompress_auto(payload_a)
        except Exception as e: print(f"  A verify failed: {e}"); return
        if check_a != data: print("  REFUSING A."); return
        print(f"  Size: {len(payload_a)} bytes")

        print("\nMethod B: 256 transforms + LZH + SHA-256 → .pjp3")
        try: payload_b = self._lzh_pipeline(data, time_limit)
        except Exception as e: print(f"  B failed: {e}"); return
        try: check_b = self._decompress_lzh_pipeline(payload_b)
        except Exception as e: print(f"  B verify failed: {e}"); return
        if check_b != data: print("  REFUSING B."); return
        wrapped_b = self._wrap_with_hash(payload_b, data)
        print(f"  Size: {len(wrapped_b)} bytes (with SHA-256)")

        out_a = infile + ".pjp2"
        out_b = infile + ".pjp3"
        try:
            self._atomic_write(out_a, payload_a)
            self._atomic_write(out_b, wrapped_b)
        except Exception as e:
            print(f"Error writing: {e}"); return

        print("\n" + "=" * 62)
        if len(payload_a) <= len(wrapped_b):
            try: os.remove(out_b)
            except Exception: pass
            winner, wsize, loser = out_a, len(payload_a), out_b
        else:
            try: os.remove(out_a)
            except Exception: pass
            winner, wsize, loser = out_b, len(wrapped_b), out_a
        ratio = (wsize / len(data) * 100) if data else 0.0
        print(f"WINNER: {winner}")
        print(f"  {wsize} bytes ({ratio:.2f}%)")
        print(f"DELETED: {loser}")

    def decompress_file(self, infile, outfile=""):
        try:
            with open(infile, 'rb') as f: blob = f.read()
        except Exception as e:
            print(f"Error reading: {e}"); return False

        if blob.startswith(MAGIC):
            print("Format: PJP4 (.pjp3)")
            try: expected_hash, payload = self._unwrap_and_check(blob)
            except IntegrityError as e: print(f"REFUSING: {e}"); return False
            original = None
            try: original = self._decompress_lzh_pipeline(payload)
            except Exception: original = None
            if original is None:
                try: original, _ = self._decompress_auto(payload)
                except Exception as e: print(f"Decompression failed: {e}"); return False
            actual_hash = hashlib.sha256(original).digest()
            if actual_hash != expected_hash:
                print("★★★ INTEGRITY FAILURE ★★★")
                print(f"  Expected: {expected_hash.hex()}")
                print(f"  Actual:   {actual_hash.hex()}")
                return False
            print(f"  SHA-256 verified: {actual_hash.hex()[:32]}…")
        else:
            print("Format: raw payload (.pjp2)")
            try:
                off, seq = self._decode_header(blob)
                if off == 0: print("Bad header"); return False
                if off < len(blob) and blob[off] == 0xFF:
                    original = self._decompress_lzh_pipeline(blob)
                else:
                    original, _ = self._decompress_auto(blob)
            except Exception as e:
                print(f"Decompression failed: {e}"); return False

        if original is None:
            print("Produced None"); return False
        if not outfile:
            base = os.path.basename(infile)
            outfile = re.sub(r'\.pjp[23]?$', '', base)
        try: self._atomic_write(outfile, original)
        except Exception as e:
            print(f"Write failed: {e}"); return False
        print(f"Decompressed → {outfile} ({len(original)} bytes)")
        return True

    def full_self_test(self):
        print("=" * 60); print("Self-Test"); print("=" * 60)
        test_bytes = [0x00, 0xFF, 0xAA, 0x55, 0x12, 0x34]
        all_ok = True
        for t in range(1, 257):
            if t % 50 == 0: print(f"  Testing {t}...")
            for tb in test_bytes:
                d = bytes([tb])
                try:
                    tr = self.fwd_transforms[t](d)
                    rs = self.rev_transforms[t](tr)
                    if rs != d: print(f"  FAIL t={t} b={tb:#04x}"); all_ok = False; break
                except TransformError: continue
                except Exception as e:
                    print(f"  EXC t={t} b={tb:#04x}: {e}"); all_ok = False; break
            if not all_ok: break
        if not all_ok: return False
        print("\n  All 256 transforms passed.")
        rng = random.Random(12345)
        d = bytes(rng.randint(0, 255) for _ in range(256))
        try:
            c = self._raw_pipeline(d, time_limit=60)
            dc, _ = self._decompress_auto(c)
            if dc != d: print("  FAIL raw pipeline"); return False
            print(f"  PASS raw pipeline ({len(d)} → {len(c)})")
        except Exception as e: print(f"  Fail raw: {e}"); return False
        try:
            c = self._lzh_pipeline(d, time_limit=60)
            dc = self._decompress_lzh_pipeline(c)
            if dc != d: print("  FAIL LZH"); return False
            print(f"  PASS LZH ({len(d)} → {len(c)})")
        except Exception as e: print(f"  Fail LZH: {e}"); return False
        print("\nHash wrapper test...")
        try:
            sample = b"hello world"
            wrapped = self._wrap_with_hash(b"PAYLOAD", sample)
            expected, payload = self._unwrap_and_check(wrapped)
            if payload != b"PAYLOAD": raise AssertionError("payload")
            if hashlib.sha256(sample).digest() != expected: raise AssertionError("hash")
            print("  PASS hash wrapper")
        except Exception as e: print(f"  FAIL: {e}"); return False
        print("\n[All checks passed]")
        return True

# ============================ MAIN ============================
def main():
    print(f"{PROGNAME}")
    print("Method A → input.pjp2 (256 transforms + PAQ/Zstd/Brotli)")
    print("Method B → input.pjp3 (256 transforms + LZH + SHA-256)")
    print("Option 1 tries BOTH, keeps SMALLER, deletes the other.\n")

    dl = input("Download 12 dictionaries from Google Drive? (y/n) [y]: ").strip().lower()
    try_download = (dl != 'n')

    c = UnifiedCompressor(try_download=try_download)

    while True:
        print("\nMenu:")
        print("1) Compress (try BOTH, keep smaller)")
        print("2) Decompress (auto-detect)")
        print("3) Full self-test")
        print("0) Exit")
        ch = input("> ").strip()
        if ch == "1":
            f = input("Input file: ").strip()
            c.compress_file_dual(f)
        elif ch == "2":
            while True:
                f = input("Compressed file (.pjp2/.pjp3) [Enter=cancel]: ").strip()
                if not f: break
                if not (f.lower().endswith('.pjp2') or f.lower().endswith('.pjp3')):
                    print("Only .pjp2 / .pjp3 supported."); continue
                o = input("Output file (blank=auto): ").strip()
                if c.decompress_file(f, o): break
                else: print("Try again or Enter to cancel.")
        elif ch == "3":
            c.full_self_test()
        elif ch == "0":
            break
        else:
            print("Invalid.")

if __name__ == "__main__":
    main()

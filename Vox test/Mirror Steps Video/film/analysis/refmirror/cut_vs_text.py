"""Do cuts land on clause starts? Usage: python3 -I cut_vs_text.py <data_dir> <name>
Clause start = first word after a word ending in . , ? ! ; or a VAD segment start. Reports share of cuts within
-0.35..+0.15 s of a clause start vs chance (uniform random times), and the median cut-minus-clause offset."""
import sys, json, numpy as np
d, name = sys.argv[1], sys.argv[2]
A = json.load(open(f"{d}/asr_{name}.json")); C = json.load(open(f"{d}/cuts30_{name}.json"))
cuts = np.array([c["t"] for c in C["cuts"]])
W = [w for s in A for w in s["words"]]
starts = [A[0]["words"][0][0]] if A and A[0]["words"] else []
for i in range(1, len(W)):
    if W[i - 1][1][-1:] in ".,?!;": starts.append(W[i][0])
for s in A:
    if s["words"]: starts.append(s["words"][0][0])
starts = np.unique(np.round(starts, 2))
def share(ts):
    return float(np.mean([np.any((ts_ - starts >= -0.35) & (ts_ - starts <= 0.15)) for ts_ in ts]))
rng = np.random.default_rng(0)
chance = np.mean([share(rng.uniform(0, C["duration"], len(cuts))) for _ in range(10)])
offs = []
for c in cuts:
    k = np.argmin(np.abs(starts - c)); offs.append(c - starts[k])
offs = np.array(offs)
print(name, "clause starts", len(starts), "(%.1f/min)" % (len(starts) / C["duration"] * 60), "| cuts on a clause start: %.2f (chance %.2f)" % (share(cuts), chance),
      "| offset cut - clause start, median of |off|<1s: %.2f s" % np.median(offs[np.abs(offs) < 1]))

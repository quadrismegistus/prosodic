"""Foot-parse a raw s/w scansion into a footed string — variable foot size AND
variable headedness within a line, no per-line k or head assumed.

Core idea: every foot owns exactly ONE strong (head), so #feet = #strongs. The
only freedom is how each run of weaks between two strongs splits — some trail the
left head, some lead the right head. A small cost (below) picks the split. Solved
exactly by DP over the strongs.
"""
LABELS = {"ws": "iamb", "sw": "trochee", "wws": "anapest", "sww": "dactyl",
          "wsw": "amphibrach", "sws": "cretic", "s": "(bare)", "wwws": "4th-paeon"}

SIZE_COST = {1: 10.0, 2: 0.0, 3: 1.0}  # degenerate awful, binary best, ternary ok


def foot_cost(lead, trail):
    size = lead + 1 + trail
    c = SIZE_COST.get(size, 5.0 + size)          # size>=4 expensive
    if lead > 0 and trail > 0:                    # head is medial (amphibrach/cretic)
        c += 2.0
    return c


def foot_parse(scansion):
    s = [c for c in scansion.lower() if c in "sw"]
    strongs = [i for i, c in enumerate(s) if c == "s"]
    if not strongs:
        return scansion, []
    m = len(strongs)
    # weak-run lengths: g[0]=before 1st strong, g[j]=between strong j-1,j, g[m]=after last
    g = [strongs[0]] + [strongs[j] - strongs[j - 1] - 1 for j in range(1, m)] + [len(s) - strongs[-1] - 1]

    # DP: state = lead_i (leading weaks of foot i). foot 0's lead is fixed = g[0].
    dp = {g[0]: (0.0, None)}
    back = []
    for i in range(m - 1):
        gi1, ndp, ch = g[i + 1], {}, {}
        for lead_next in range(gi1 + 1):
            trail_i = gi1 - lead_next                      # trailing weaks of foot i
            best, bp = float("inf"), None
            for lead_i, (cost, _) in dp.items():
                c = cost + foot_cost(lead_i, trail_i)
                if c < best:
                    best, bp = c, lead_i
            ndp[lead_next], ch[lead_next] = (best, bp), bp
        dp, _ = ndp, back.append(ch)

    # close the last foot (its trailing weaks = g[m])
    best, best_lead = float("inf"), None
    for lead_i, (cost, _) in dp.items():
        c = cost + foot_cost(lead_i, g[m])
        if c < best:
            best, best_lead = c, lead_i

    leads = [0] * m
    leads[m - 1] = best_lead
    for i in range(m - 2, -1, -1):
        leads[i] = back[i][leads[i + 1]]
    trails = [(g[i + 1] - leads[i + 1]) if i < m - 1 else g[m] for i in range(m)]

    feet, pos = [], 0
    for i in range(m):
        size = leads[i] + 1 + trails[i]
        feet.append("".join(s[pos:pos + size]))
        pos += size
    return "|".join(feet), feet


TESTS = [
    ("s w w s w s w s w s", "your example 1"),
    ("w s w w s w w s w s", "your example 2"),
    ("w s w s w s w s w s", "clean iambic"),
    ("s w s w s w s w s w", "clean trochaic"),
    ("w w s w w s w w s w w s", "clean anapestic"),
    ("s w w s w w s w w", "clean dactylic"),
]
print("raw scansion              ->  footed                    feet")
print("-" * 78)
for raw, note in TESTS:
    footed, feet = foot_parse(raw)
    labels = " ".join(LABELS.get(f, f) for f in feet)
    print(f"{raw:<25} ->  {footed:<24}  {labels}    ({note})")

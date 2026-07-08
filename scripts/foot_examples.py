"""One real Shakespeare line per foot type produced by the DP foot-parser.
Beats (strong syllables) are CAPITALISED; the example foot is in [brackets].
"""
import warnings; warnings.filterwarnings("ignore")
import prosodic

t = prosodic.Text(open("corpora/corppoetry_en/en.shakespeare.txt").read())
t.parse()


def foot_disp(ft):
    return "-".join(sl.unit.txt.upper() if sl.is_prom else sl.unit.txt.lower() for sl in ft.slots)


def line_disp(feet, hi):
    return " | ".join(f"[{foot_disp(ft)}]" if i == hi else foot_disp(ft) for i, ft in enumerate(feet))


# first line where each foot label appears (prefer a non-line-initial foot for
# variety where possible, but first occurrence is fine)
ex = {}
for line in t.lines:
    bp = line.best_parse
    if not bp or not bp.slots:
        continue
    feet = bp.metrical_feet
    for i, ft in enumerate(feet):
        ex.setdefault(ft.label, []).append((line.txt.strip(), i, feet))

ORDER = ["iamb", "trochee", "anapest", "dactyl", "amphibrach", "cretic",
         "spondee", "iamb-r", "trochee-r", "anapest-r", "dactyl-r", "amphibrach-r", "bare"]
for label in ORDER + [l for l in ex if l not in ORDER]:
    if label not in ex:
        continue
    text, i, feet = ex[label][0]
    ft = feet[i]
    print(f"{label.upper():<12} {ft.pattern:<5}  {ft.head:<9}  [{foot_disp(ft)}]")
    print(f"             {line_disp(feet, i)}")
    print(f"             \"{text}\"\n")

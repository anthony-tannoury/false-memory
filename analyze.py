"""Analyse des fichiers .xpd de l'expérience de faux souvenirs (false_memory.py et docs/index.html).

Usage :  python analyze.py <dossier_des_fichiers> <dossier_de_sortie>

Lit tous les fichiers .xpd du dossier d'entrée (un fichier = un participant ; les fichiers
incomplets ou d'une autre expérience sont ignorés, avec un message) et écrit dans le
dossier de sortie, pour chaque graphe, un fichier .csv avec les valeurs tracées et une image .png :

1. graphe1_reponses_oui : taux de « oui » pour les mots montrés, les mots clés des listes
   lues et les mots clés des listes non lues (moyenne, erreur type, chaque participant,
   valeurs de l'article).
2. graphe2_mots_cles : pour chaque participant, faux souvenirs des mots clés, listes lues
   contre listes non lues.
3. graphe3_temps_reponse : temps de réponse médian des « oui » aux mots montrés contre
   les « oui » aux mots clés des listes lues (participants sans faux souvenir exclus).

Valeurs de l'article : Roediger & McDermott (1995), expérience 2, tableau 2 (proportion de
« oui » ; la première valeur après rappel des listes, la seconde après calcul mental).
"""
import csv
import statistics
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")                      # write image files, no window
import matplotlib.pyplot as plt

KINDS = ["studied_word", "studied_lure", "unstudied_word", "unstudied_lure"]
N_TEST = 48
BLUE, ORANGE, GREY, INK = "#2a78d6", "#eb6834", "#888780", "#0b0b0b"
GRAPH1 = [  # (type de mot, étiquette, couleur, valeurs de l'article)
    ("studied_word", "Listes lues :\nmots montrés", BLUE, (0.65, 0.79)),
    ("studied_lure", "Listes lues :\nmots clés", ORANGE, (0.72, 0.81)),
    ("unstudied_lure", "Listes non lues :\nmots clés", ORANGE, (0.16, 0.16)),
]


def read_xpd(path):
    """Test rows and language of one .xpd file, or None if it is not a complete false-memory run."""
    lines = path.read_text("utf-8").splitlines()
    language = next((l.split(":")[1].strip() for l in lines if l.startswith("#e language:")), "?")
    rows = list(csv.DictReader(l for l in lines if not l.startswith("#")))
    test = [r for r in rows if r.get("phase") == "test"]
    if len(test) != N_TEST:
        return None
    source = "web" if any(l.startswith("#e source: web") for l in lines) else "python"
    return {"participant": path.stem, "language": language, "source": source, "test": test}


def summarise(p):
    """Per-participant rates of "yes" by kind of word, and median times of the "yes" answers."""
    out = {k: v for k, v in p.items() if k != "test"}
    for kind in KINDS:
        said = [r["said_old"] == "True" for r in p["test"] if r["kind"] == kind]
        out[kind] = sum(said) / len(said)
    for name, kind in (("rt_vrais_positifs", "studied_word"), ("rt_faux_souvenirs", "studied_lure")):
        rts = [int(r["rt"]) for r in p["test"] if r["kind"] == kind and r["said_old"] == "True"]
        out[name] = statistics.median(rts) if rts else None
    return out


def n_label(n):
    return f"{n} participant" + ("s" if n > 1 else "")


def sem(values):
    return statistics.stdev(values) / len(values) ** 0.5 if len(values) > 1 else 0.0


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


_example = {"participant": "x", "language": "fr", "source": "web", "test": [
    {"kind": k, "said_old": s, "rt": "800"} for k, s in
    [("studied_word", "True"), ("studied_word", "False"), ("studied_lure", "True"),
     ("unstudied_word", "False"), ("unstudied_lure", "False")]]}
assert summarise(_example)["studied_word"] == 0.5 and summarise(_example)["studied_lure"] == 1
assert summarise(_example)["rt_faux_souvenirs"] == 800

if len(sys.argv) != 3:
    sys.exit(__doc__)
source_dir, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
out_dir.mkdir(parents=True, exist_ok=True)

people = []
for path in sorted(source_dir.glob("*.xpd")):
    run = read_xpd(path)
    if run is None:
        print(f"ignoré (pas un test complet de faux souvenirs) : {path.name}")
    else:
        people.append(summarise(run))
if not people:
    sys.exit(f"aucun fichier complet dans {source_dir}")
print(f"{len(people)} participant(s) : "
      + ", ".join(f"{lang} {sum(p['language'] == lang for p in people)}"
                  for lang in sorted({p['language'] for p in people})))

# 1. Taux de « oui » par type de mot
rows = []
for kind, label, _, (paper_min, paper_max) in GRAPH1:
    values = [p[kind] for p in people]
    rows.append([label.replace("\n", " "), round(statistics.mean(values), 3), round(sem(values), 3),
                 len(values), paper_min, paper_max] + [round(v, 3) for v in values])
write_csv(out_dir / "graphe1_reponses_oui.csv",
          ["type_de_mot", "moyenne", "erreur_type", "n_participants", "article_min", "article_max"]
          + [p["participant"] for p in people], rows)
other = statistics.mean(p["unstudied_word"] for p in people)
print(f"« oui » aux autres mots des listes non lues : {other:.0%} en moyenne")

fig, ax = plt.subplots(figsize=(7, 4.5))
for x, (kind, label, color, (paper_min, paper_max)) in enumerate(GRAPH1):
    values = [p[kind] for p in people]
    ax.bar(x, statistics.mean(values), width=0.5, color=color, yerr=sem(values) if len(values) > 1 else None,
           error_kw={"ecolor": INK, "capsize": 4, "lw": 1})
    jitter = [x - 0.12 + 0.24 * i / (len(values) - 1) for i in range(len(values))] if len(values) > 1 else [x]
    ax.scatter(jitter, values, s=18, color=GREY, edgecolor="white", linewidth=0.8, zorder=3)
    ax.plot([x + 0.29, x + 0.37], [paper_min] * 2, color=INK, lw=2)    # article: one value, or a range
    if paper_max != paper_min:
        ax.plot([x + 0.33] * 2, [paper_min, paper_max], color=INK, lw=2)
        ax.plot([x + 0.29, x + 0.37], [paper_max] * 2, color=INK, lw=2)
    ax.text(x + 0.33, paper_max + 0.025, "article", ha="center", fontsize=8)
means = [statistics.mean(p[g[0]] for p in people) for g in GRAPH1]
ax.set_xticks(range(len(GRAPH1)), [f"{g[1]}\nmoyenne : {m:.0%}" for g, m in zip(GRAPH1, means)])
ax.set_ylim(0, 1.08)
ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1))
ax.set_ylabel("Réponses « oui » (était dans les listes)")
ax.set_title(f"Réponses « oui » selon le type de mot ({n_label(len(people))})", fontsize=11)
ax.plot([], [], color=INK, lw=2, label="Article (Roediger & McDermott, 1995)")
ax.scatter([], [], s=18, color=GREY, label="Un participant")
ax.plot([], [], color=INK, lw=1, label="Erreur type de la moyenne (trait fin)")
ax.legend(frameon=False, fontsize=9, loc="upper right")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(out_dir / "graphe1_reponses_oui.png", dpi=200)

# 2 et 3. Une ligne par participant
def slope(name, key_a, key_b, label_a, label_b, ylabel, title, color, percent):
    pairs = [(p["participant"], p[key_a], p[key_b]) for p in people
             if p[key_a] is not None and p[key_b] is not None]
    write_csv(out_dir / f"{name}.csv", ["participant", label_a.replace("\n", " "), label_b.replace("\n", " ")],
              [(who, round(a, 3), round(b, 3)) for who, a, b in pairs])
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    for _, a, b in pairs:
        ax.plot([0, 1], [a, b], color=GREY, alpha=0.6, lw=1.2, marker="o", markersize=4)
    if pairs:
        mean_a, mean_b = statistics.mean(a for _, a, _ in pairs), statistics.mean(b for _, _, b in pairs)
        ax.plot([0, 1], [mean_a, mean_b], color=color, lw=2.5, marker="o", markersize=7, label="Moyenne")
        fmt = (lambda v: f"{v:.0%}") if percent else (lambda v: f"{v:.0f} ms")
        ax.text(-0.06, mean_a, fmt(mean_a), ha="right", va="center", fontsize=10)
        ax.text(1.06, mean_b, fmt(mean_b), ha="left", va="center", fontsize=10)
    ax.plot([], [], color=GREY, lw=1.2, label="Un participant")
    ax.set_xticks([0, 1], [label_a, label_b])
    ax.set_xlim(-0.4, 1.4)
    if percent:
        ax.set_ylim(-0.03, 1.03)
        ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1))
    ax.set_ylabel(ylabel)
    ax.set_title(f"{title} ({n_label(len(pairs))})", fontsize=11)
    ax.legend(frameon=False, fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(out_dir / f"{name}.png", dpi=200)


slope("graphe2_mots_cles", "studied_lure", "unstudied_lure", "Listes lues", "Listes non lues",
      "Mots clés « reconnus » (jamais montrés)", "Faux souvenirs des mots clés", ORANGE, True)
slope("graphe3_temps_reponse", "rt_vrais_positifs", "rt_faux_souvenirs",
      "Vrais positifs\n(mots montrés)", "Faux souvenirs\n(mots clés)",
      "Temps de réponse médian des « oui » (ms)", "Temps de réponse", BLUE, False)
print(f"résultats écrits dans {out_dir}")

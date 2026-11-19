"""False memory for words that were never shown (DRM paradigm).

After Roediger & McDermott (1995), J. Exp. Psychol.: Learning, Memory, and
Cognition 21:803-814, Experiment 2. Each list contains 15 words that are all
associates of one word that is NOT in the list (bed, rest, awake... for
"sleep"). The participant studies half of the lists, then takes a recognition
test. Paper result (Table 2): the missing word of a studied list is called
"old" as often as words that were really shown (.72 to .81 against .65 to
.79), and far more often than the missing word of a non-studied list (.16).

Run:  python false_memory.py        (add --dev for a windowed test run)
The first screen asks for the language: French, or English (the paper's lists).

The word lists, the texts and the durations are in docs/material.json.
The web page docs/index.html reads the same file and follows the
same steps, so both versions show the same thing.

From the paper: 15 words per list in the appendix order, about 1.5 s per word;
the test takes the words at positions 1, 8 and 10 of every list plus its
missing word, for studied and non-studied lists. The English lists are 12 of
the 24 lists of the paper's appendix, checked word by word against it.

NOT from the paper (check before collecting data):
- THE FRENCH LISTS ARE MY TRANSLATION of the appendix lists. They are not
  published French norms, so the strength of the effect in French is not
  known in advance. Two English lists (rough, sweet) are replaced by two other
  appendix lists (spider, slow) in French, because their translation fails
  ("sucre" would be studied and "sucré" tested; "rough riders" has no
  equivalent). Words that are idioms in English (molehill, haystack) lose
  their link in French.
- The paper played the words on a tape recorder; here they are shown on screen.
- The paper used 24 lists (16 studied) and 2 min of recall or arithmetic after
  each list; here 12 lists (6 studied) and no task between lists.
- The paper's test also asked for remember / know judgements; here old / new only.
"""
import json
import random
import sys
from pathlib import Path

from expyriment import control, design, misc, stimuli

M = json.loads((Path(__file__).parent / "docs/material.json").read_text("utf-8"))
OLD, NEW = misc.constants.K_f, misc.constants.K_j
LANGUAGE_KEYS = {misc.constants.K_f: "fr", misc.constants.K_e: "en"}


def make_test(lists, studied):
    """Test items: (word, list, kind) for every list, in random order."""
    items = []
    for lure, words in lists.items():
        group = "studied" if lure in studied else "unstudied"
        items += [(words[p - 1], lure, f"{group}_word") for p in M["test_positions"]]
        items.append((lure, lure, f"{group}_lure"))
    random.shuffle(items)
    return items


def results(answers):
    """Values for the end screen, from the test answers (word, list, kind, said_old)."""
    values = {}
    for name, kinds in (("hits", {"studied_word"}), ("lures", {"studied_lure"}),
                        ("fa", {"unstudied_word", "unstudied_lure"})):
        said = [a[3] for a in answers if a[2] in kinds]
        values[name], values["n_" + name] = sum(said), len(said)
        values["p_" + name] = int(100 * sum(said) / len(said) + 0.5)   # same rounding as JS
    words = [a[0] for a in answers if a[2] == "studied_lure" and a[3]]
    values["lure_words"] = f"({', '.join(words)})" if words else ""
    return values


assert results([("bed", "sleep", "studied_word", True), ("rest", "sleep", "studied_word", False),
                ("sleep", "sleep", "studied_lure", True), ("hot", "cold", "unstudied_word", False),
                ("cold", "cold", "unstudied_lure", True)]) == {
    "hits": 1, "n_hits": 2, "p_hits": 50, "lures": 1, "n_lures": 1, "p_lures": 100,
    "fa": 1, "n_fa": 2, "p_fa": 50, "lure_words": "(sleep)"}

for _lang in ("en", "fr"):
    _lists = {lure: words.split() for lure, words in M[_lang]["lists"].items()}
    _words = [w for lure, words in _lists.items() for w in words + [lure]]
    assert len(_lists) == 12 and all(len(words) == 15 for words in _lists.values())
    assert len(_words) == len(set(_words)), "a word appears twice"
    _test = make_test(_lists, set(list(_lists)[:6]))
    assert len(_test) == 48 and sum(kind == "studied_lure" for _, _, kind in _test) == 6

control.set_develop_mode("--dev" in sys.argv)
exp = design.Experiment("false_memory")
control.initialize(exp)
exp.add_data_variable_names(["phase", "word", "list", "kind", "said_old", "rt"])
control.start(skip_ready_screen=True)
# Expyriment sizes text in pixels (20 by default): make it follow the screen height instead.
TEXT_SIZE = max(20, exp.screen.size[1] // 40)
WORD_SIZE = exp.screen.size[1] // 12
stimuli.defaults.textline_text_size = stimuli.defaults.textscreen_text_size = TEXT_SIZE
stimuli.defaults.textscreen_heading_size = round(TEXT_SIZE * 1.3)
blank = stimuli.BlankScreen()


def wait(ms):
    exp.clock.wait(ms, process_control_events=True)    # ESC can quit


stimuli.TextScreen("", M["choose"]).present()
key, _ = exp.keyboard.wait(list(LANGUAGE_KEYS))
language = LANGUAGE_KEYS[key]
exp.data.add_experiment_info(f"language: {language}")
TEXT = M[language]
LISTS = {lure: words.split() for lure, words in TEXT["lists"].items()}

stimuli.TextScreen(*TEXT["study"]).present()
exp.keyboard.wait()

studied = random.sample(list(LISTS), len(LISTS) // 2)
for number, lure in enumerate(studied, 1):
    stimuli.TextLine(TEXT["list"].format(number, len(studied))).present()
    wait(M["list_pause_ms"])
    for word in LISTS[lure]:
        stimuli.TextLine(word, text_size=WORD_SIZE).present()
        wait(M["word_ms"])
        blank.present()
        wait(M["gap_ms"])
        exp.data.add(["study", word, lure, "studied_word", "", ""])

stimuli.TextScreen(*TEXT["test"]).present()
exp.keyboard.wait()

answers = []
for word, lure, kind in make_test(LISTS, set(studied)):
    blank.present()
    wait(M["test_blank_ms"])
    stimuli.TextLine(word, text_size=WORD_SIZE).present()
    key, rt = exp.keyboard.wait([OLD, NEW])
    exp.data.add(["test", word, lure, kind, key == OLD, rt])
    answers.append((word, lure, kind, key == OLD))
exp.data.save()

stimuli.TextScreen(TEXT["results"][0], TEXT["results"][1].format(**results(answers))).present()
exp.keyboard.wait()

control.end(goodbye_text=TEXT["end"])

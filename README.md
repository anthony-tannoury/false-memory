# False memory (DRM paradigm)

People remember a word that was never shown, because all the words they saw
were associated with it (*bed, rest, awake, dream…* → "sleep").

Based on Roediger & McDermott (1995), *Creating false memories: Remembering
words not presented in lists*, J. Exp. Psychol. LMC 21:803-814, Experiment 2.

## Run it

- **In a browser** (computer with a keyboard): https://anthony-tannoury.github.io/false-memory/
- **With Python**:

  ```
  pip install -r requirements.txt
  python false_memory.py
  ```

The experiment takes about 2½ minutes, in French or English.

The English lists are from the paper's appendix. The French lists are a
translation of them, not published French norms.

## Analyse

```
python analyze.py <dossier des fichiers .xpd> <dossier de sortie>
```

Writes, for each graph, a `.csv` with the plotted values and a `.png` image.

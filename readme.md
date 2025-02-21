
## Adding tabular accounting support to a non-monospaced font

Experiment to get a font without monospacing to behave nicely in tabular contexts.

Goals:
1. `0-9`, `,` and `.` and `$` should all have the same width
2. `(` and `)` should take up no width and be nicely visually aligned

Currently testing specifically on General Sans Variable.


## Approach 1: A new font with different fixed widths for relevant glyphs

`python fix_tabular_figures.py`

Seems to work!

Pros:
- Should work in any browser

Cons:
- Have to load a second font into the browser

```
@font-face {
  font-family: "General Sans Tabular";
  src: url("GeneralSans-Variable-Tabular.ttf");
  font-style: italic;
  font-weight: 100 1000;
}

.tnum {
  font-family: "General Sans Tabular";
  text-align: right;
  width: 100%;
  display: block;
}
```

## Approach 2: A new font with the tnum font feature

`python extend_tnum.py`

Available since January 2020; possibility we have customers that don't have it supported?

https://caniuse.com/?search=tabular-nums

Pros:
- A single font that works for both contexts

Cons:
- The first version works for goal (1) but has not achieved goal (2) yet

```
@font-face {
  font-family: "General Sans Extended";
  src: url("GeneralSans-Variable-Extended.ttf");
  font-style: normal;
  font-weight: 100 1000;
}

.tnum {
  font-family: "General Sans Extended";
  text-align: right;
  width: 100%;
  display: block;
  font-feature-settings: "tnum" on;
}
```

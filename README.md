The Tampio Programming Language
===============================

Tampio is a programming language that looks like a natural language – Finnish.
It is named after a famous Finnish programmer.

This branch currently contains a new iteration of the language that is not functional. The functional language is in the `functional` branch.

## Dependencies

* Python 3
* Libvoikko (package `libvoikko` in Ubuntu and Fedora)
* Finnish morphological dictionary (Eg. [this](http://www.puimula.org/htp/testing/voikko-snapshot/dict-morpho.zip) or [this](https://www.puimula.org/htp/testing/voikko-snapshot-v5/dict-morpho.zip). The latter may work better with newer versions of libvoikko, but the former is confirmed to work with libvoikko 3.8.)

The morphological dictionary must be unzipped to `~/.voikko/`.

## Usage

To open an interactive prompt:

    python3 tampio.py

To evaluate a file (TODO):

    python3 tampio.py file.itp

## Introduction

TODO

## Finnish declension

In Finnish nouns are inflected in [cases][wp-case]. There are a few of them, listed below. The exact meanings of the cases are not important to understand the programming language.

|Case       |Suffix|Example     |Notes      |
|-----------|------|------------|-----------|
|Nominative |-     |kissa       |           |
|Genitive   |-n    |kissa*n*    |           |
|Partitive  |-A    |kissa*a*    |           |
|Essive     |-nA   |kissa*na*   |           |
|Translative|-ksi  |kissa*ksi*  |           |
|Allative   |-lle  |kissa*lle*  |           |
|Adessive   |-llA  |kissa*lla*  |           |
|Ablative   |-lta  |kissa*lta*  |           |
|Illative   |-Vn   |kissa*an*   |           |
|Inessive   |-ssA  |kissa*ssa*  |           |
|Elative    |-stA  |kissa*sta*  |           |
|Abessive   |-ttA  |kissa*tta*  |           |
|Instructive|-in   |kisso*in*   |Plural only|
|Comitative |-ine- |kisso*ine*ni|Plural only, possessive suffix required|

The inflection of nouns is a pretty complicated process. The exact suffix depends on vowel harmony ("A" is either "a" or "ä") and the stem of the word can change due to consonant gradation. It is outside the scope of this document to describe declension further. Inflected forms of different words can be checked from [Wiktionary] if needed.

[wp-case]: https://en.wikipedia.org/wiki/Finnish_noun_cases
[Wiktionary]: https://en.wiktionary.org/wiki/kissa

## License

The interpreter is licensed under the GNU General Public License, version 3 or later.
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.
See the LICENSE file for details.

The Tampio Programming Language
===============================

Tampio is a homoiconic lazy purely functional programming language that looks like a natural language – Finnish.
It is named after a famous Finnish programmer.

## Introduction

Tampio is a purely functional programming language designed to resemble written Finnish. Each program is a list of transformations that are applied to the evaluated code. Tampio is homoiconic, meaning that the code and data are represented using the same data type.

A transformation definition consists of _pattern_ and _body_, separated by the `on` keyword. For example:

    kissan nimi on maija
    tulos on kissan nimi

The above program declares that `kissan nimi` is transformed to `maija` and `tulos` is transformed to `kissan nimi`. Using these rules, `tulos` evaluates to `maija`.

The patterns can contain variables, that match to all expressions.

    x:n nimi on maija
    tulos on koiran nimi

Here, `koiran nimi` matches `x:n nimi` and evaluates to `maija`.

## Syntax

Every pattern and body of a transformation is an expression. All expressions can be inflected in different cases.

Tampio supports two kinds of expressions: _words_ and _function calls_. A word is simply a word in the source code.

There are three types of function calls: genetive calls, essive calls, binary operators. Each function call has a unique syntax.

Genetive calls have form `argumentin funktio`, where `argumentti` is the argument and `funktio` is the name of the function. The argument must be in the genetive case. These calls can only have one argument and have the highest precedence. When the expression is inflected, it is the name of the function that is inflected.

Essive calls can have either one or two arguments. They have form `argumentti funktiona [argumentilla]` where the optional last argument must be inflected in a case that is not nominative, genetive or essive. Essive calls are right-associative, meaning that eg. `a f:nä b:llä g:nä` means `f(a,g(b))` in pseudocode.

There are two binary operators in addition to conjunctions in the language: `plus` and `miinus`. Their first operand must be in the nominative case and the second is inflected in the case of the expression.

The conjunctions `ja`, `tai` and `sekä` have usually the same precedence as other binary operators. They require that the first operand is in the same case as the second is. This can lead to situations where the conjunctions actually have a very high precedence:

    a f:nä b:llä ja c     = ja(f(a,b),c)
    a f:nä b:llä ja c:llä = f(a,ja(b,c))

## Syntax cheat sheet

|Precedence   |Name                   |Syntax        |Pseudocode |Inflected word|Notes|
|-------------|-----------------------|--------------|-----------|--------------|-----|
|1            |Genetive               |`a:n f`       |`f(a)`     |`f`           |     |
|2            |Essive                 |`a f:nä b:llä`|`f(a,b)`   |`a`           |The case of `b` may vary, but must not be nominative, genetive or essive|
|3            |Binary operator        |`a plus b`    |`plus(a,b)`|`b`           |Available operators: `plus`, `miinus`|
|3<sup>a</sup>|Conjunction<sup>b</sup>|`a ja b`      |`ja(a,b)`  |`a` and `b`   |Available conjunctions: `ja`, `sekä`, `tai`|

<sup>a</sup>The precedence level of a conjunction depends on the cases of the operands, as both operands must share the same case.

<sup>b</sup>Conjunctions are a special type of binary operator that require that the operands always are in the same case. Other binary operators require that the first operand is in the nominative case.

## Finnish declension

In Finnish nouns are inflected in [cases][wp-case]. There are a few of them, listed below. The exact meanings of the cases are not important to understand the programming language.

|Case       |Suffix|Example     |Notes      |
|-----------|------|------------|-----------|
|Nominative |-     |kissa       |           |
|Genetive   |-n    |kissa*n*    |           |
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

The inflection of nouns is a pretty complicated process. The exact suffix depends on vowel harmony ("A" is either "a" or "ä") and the stem of the word can change due to consonant gradation. It is outside the scope of this document to describe declension further, so it is recommended to check the exact inflected form using from eg. [Wiktionary].

[wp-case]: https://en.wikipedia.org/wiki/Finnish_noun_cases
[Wiktionary]: https://en.wiktionary.org/wiki/kissa

## License

The interpreter is licensed under the GNU General Public License, version 3 or later.
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.
See the LICENSE file for details.

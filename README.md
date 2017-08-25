The Tampio Programming Language
===============================

Tampio is a homoiconic lazy purely functional programming language that looks like a natural language – Finnish.
It is named after a famous Finnish programmer.

## Dependencies

* Python 3
* Libvoikko (package `libvoikko` in Ubuntu and Fedora)
* Finnish morphological dictionary (eg. [this](http://www.puimula.org/htp/testing/voikko-snapshot/dict-morpho.zip))

The morphological dictionary must be unzipped to `~/.voikko/`.

## Usage

To open an interactive prompt:

    python3 suomi.py

To evaluate a file:

    python3 suomi.py file.suomi

The output will be the value of `tulos`.

## Introduction

Tampio is a purely functional programming language designed to resemble written Finnish. Each program is a list of transformations that are applied to the evaluated code. Tampio is homoiconic, meaning that the code and data are represented using the same data type.

A transformation definition consists of _pattern_ and _body_, separated by the `on` keyword. For example:

    >>> kissan nimi on maija
    >>> tulos on kissan nimi
    >>> tulos
    maija

The above program declares that `kissan nimi` is transformed to `maija` and `tulos` is transformed to `kissan nimi`. Using these rules, `tulos` evaluates to `maija`.

The patterns can contain variables, which match to all expressions.

    >>> x:n nimi on maija
    >>> koiran nimi
    maija

Here, `koiran nimi` matches `x:n nimi` and evaluates to `maija`.

## Syntax

Every pattern and body of a transformation is an expression.

    <pattern> on <expression> [, missä <var> on <expression>]

All expressions can be inflected in different cases. Both `<pattern>` and `<expression>` must be in the nominative case.

Every transformation can have an optional `missä` clause, which is substituted to the pattern and the body. For example,

    nolla plus luku on luku, missä luku on x:n seuraaja

is equivalent to

    nolla plus x:n seuraaja on x:n seuraaja

Tampio supports two kinds of expressions: _words_ and _function calls_. A word is simply a word in the source code.

There are three types of function calls: genitive calls, essive calls, binary operators. Each function call has a unique syntax.

Genitive calls have form `argumentin funktio`, where `argumentti` is the argument and `funktio` is the name of the function. The argument must be in the genitive case. These calls can only have one argument and have the highest precedence. When the expression is inflected, it is the name of the function that is inflected.

Essive calls can have either one or two arguments. They have form `argumentti funktiona [argumentilla]` where the optional last argument must be inflected in a case that is not nominative, genitive or essive. Essive calls are right-associative, meaning that eg. `a f:nä b:llä g:nä` means `f(a,g(b))` in pseudocode. It is also possible to place the last argument before the essive word (eg. `argumentti argumentilla funktiona`) so it is possible to write `a b:llä f:nä g:nä`, which means `g(f(a,b))`.

There are four binary operators in addition to conjunctions: `plus`, `ynnä`, `miinus` and `modulo`. Their first operand must be in the nominative case and the second is inflected in the case of the expression.

The conjunctions `ja`, `tai` and `sekä` have usually the same precedence as other binary operators. They require that the first operand is in the same case as the second is. This can lead to situations where the conjunctions actually have a very high precedence:

    a f:nä b:llä ja c     = ja(f(a,b),c)
    a f:nä b:llä ja c:llä = f(a,ja(b,c))

### Syntax cheat sheet

|Precedence   |Name                   |Syntax                          |Pseudocode |Inflected word|Notes|
|-------------|-----------------------|--------------------------------|-----------|--------------|-----|
|1            |Genitive               |`a:n f`                         |`f(a)`     |`f`           |     |
|1            |Essive                 |`a f:nä b:llä` or `a b:llä f:nä`|`f(a,b)`   |`a`           |The case of `b` may vary, but must not be nominative, genitive or essive|
|2            |Binary operator        |`a plus b`                      |`plus(a,b)`|`b`           |Available operators: `plus`, `ynnä`, `miinus`, `modulo`|
|2<sup>a</sup>|Conjunction<sup>b</sup>|`a ja b`                        |`ja(a,b)`  |`a` and `b`   |Available conjunctions: `ja`, `sekä`, `tai`|

<sup>a</sup>The precedence level of a conjunction depends on the cases of the operands, as both operands must share the same case.

<sup>b</sup>Conjunctions are a special type of binary operator that require that the operands always are in the same case. Other binary operators require that the first operand is in the nominative case.

## Evaluation

An expression is evaluated in the following steps:

1. The expression is matches against every pattern in the current file, from up to down. The expression is substituted with the first matching expression.
2. If no expression matches, apply steps 1 and 2 (but not step 3) to each nested expression.
3. Repeat steps 1 and 2 until the expression and nested expressions do not match any pattern.

For example, given the following definitions, `nollan seuraaja plus nollan seuraaja` is evaluated as shown.

    nolla plus x on x                          # def 1
    x:n seuraaja plus y on x plus y:n seuraaja # def 2
    
    nollan seuraaja plus nollan seuraaja
    # (step 1) matches def 2 (x:n seuraaja plus y)
    #          substitute with x plus y:n seuraaja
    #          where x = nolla, y = nollan seuraaja
    # (step 3) repeat
    nolla plus nollan seuraajan seuraaja
    # (step 1) matches def 1 (nolla plus x)
    #          substitute with x
    #          where x = nollan seuraajan seuraaja
    # (step 3) repeat
    nollan seuraajan seuraaja
    # (step 1) does not match
    # (step 2) no nested expression matches
    # (step 3) no need to repeat, stop evaluation

### Impure optimizations

The interpreter supports _impure optimizations_, which – while increasing evaluation speed – do unfortunately make the language impure.

For example, we can make an impure version of Fibonacci number list using the `epäpuhtaasti` keyword.

    luvut ovat epäpuhtaasti 1 lisättynä 1:een lisättynä yhteenlaskuun sovellettuna lukujen jäseniin ja lukujen hännän jäseniin

Now, after the next Fibonacci number after 1 and 1 is calculated, the `luvut` list is updated to include it.

    luvut ovat epäpuhtaasti 1 lisättynä 1:een lisättynä 2:een lisättynä yhteenlaskuun sovellettuna lukujen jäseniin ja lukujen hännän jäseniin

This reduces the complexity from O(2^n) to O(n). However, the impurity can leak to other parts of the program and cause it to behave in unintended ways.

## Examples

### Lazy infinite lists
    
    # Ones [1, 1, 1, ...]
    yhdet ovat yksi lisättynä yksiin
    
    # Natural numbers [1, 2, 3, 4, ...]
    luvut ovat yhteenlasku sovellettuna yksien jäseniin ja nollan lisättynä lukuihin jäseniin
    
    # Fibonacci sequence [1, 1, 2, 3, 5, 8, ...]
    luvut ovat 1 lisättynä 1:een lisättynä yhteenlaskuun sovellettuna lukujen jäseniin ja lukujen hännän jäseniin

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

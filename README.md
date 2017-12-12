The Tampio Programming Language
===============================

Tampio is an object-oriented programming language that looks like a natural language – Finnish.
It is named after a famous Finnish programmer.

This branch currently contains a new iteration of the language that is not functional. The functional language is in the [`functional`](https://github.com/fergusq/tampio/tree/functional) branch.

## Dependencies

* Python 3
* Libvoikko (package `libvoikko` in Ubuntu and Fedora)
* Finnish morphological dictionary (Eg. [this](http://www.puimula.org/htp/testing/voikko-snapshot/dict-morpho.zip) or [this](https://www.puimula.org/htp/testing/voikko-snapshot-v5/dict-morpho.zip). The latter may work better with newer versions of libvoikko, but the former is confirmed to work with libvoikko 3.8.)

The morphological dictionary must be unzipped to `~/.voikko/`.

## Usage

To open an interactive prompt:

    python3 tampio.py

To compile a file to JavaScript:

    python3 tampio.py file.itp

To print HTML code that contains the syntax highlighting data of the file:

    python3 tampio.py -s file.itp

To print a HTML page that contains both JavaScript and the syntax highlighted code:

    python3 tampio.py -p file.itp

## Introduction

Tampio is an object-oriented language that compiles to JavaScript.
Its syntax is directly inspired by the Finnish language and is therefore based on inflecting words.

A Tampio file is a list of definitions, each which defines either a class, a function, a method or a global variable.
For example, here is a simple program that calculates the factorial of a given number.

    Pienen luvun kertoma on
    	riippuen siitä, onko pieni luku pienempi tai yhtä suuri kuin yksi,
    	joko pieni luku
    	tai pieni luku kerrottuna pienen luvun edeltäjän kertomalla.
    
    Luonnollisen luvun edeltäjä on luonnollinen luku vähennettynä yhdellä.
    
    Olkoon pieni muuttuja uusi muuttuja, jonka arvo on nolla.
    
    Kun nykyinen sivu avautuu,
    	pieneen muuttujaan luetaan luku
    	ja nykyinen sivu näyttää pienen muuttujan arvon kertoman.

It contains two functions definitions, one variable definition and one method definition.
Let's iterate these line by line.

    Pienen luvun kertoma on

This is the signature of the `kertoma` function, which has one parameter `pieni luku`.
As you can see, the name of the parameter comes before the name of the function and is in the genitive case.
The last word, `on`, is a keyword that separates the signature of the function and its body.

    riippuen siitä, onko pieni luku pienempi tai yhtä suuri kuin yksi,

This is a conditional expression.
It tests if `pieni luku` is less than or equal to (`pienempi tai yhtä suuri kuin`) one (`yksi`).

    joko pieni luku

If the condition is true, the function returns the value of its argument, `pieni luku`.
`joko` is a keyword that comes after the condition of `riippuen siitä` expression.

    tai pieni luku kerrottuna pienen luvun edeltäjän kertomalla.

If the condition is false (`pieni luku` is greater than one), the function returns the value of this expression.
It is a product (`kerrottuna` is the multiplication operation) of `pieni luku` and `pienen luvun edeltäjän kertoma`.
The right operand of `kerrottuna` consists of two function calls (which are similar to the signature of the function).
First, the predecessor (`edeltäjä`) of `pieni luku` is calculated, and then its factorial (`kertoma`).
The arguments of functions are in the genitive case.

    Luonnollisen luvun edeltäjä on luonnollinen luku vähennettynä yhdellä.

This is a helper function that calculates the predecessor of a natural number.
It simply consists of a `vähennettynä` operator that operands `luonnollinen luku` (the parameter) and `yksi` (one).

    Olkoon pieni muuttuja uusi muuttuja, jonka arvo on nolla.

`Olkoon` is a keyword that is used to define global variables.
The name of the variable is `pieni muuttuja` and its value is a new object.
The object is created using the `uusi` keyword and its type is the `muuttuja` class.
`jonka` keyword is used to set the initial values of the fields of the object.
In this case, the `arvo` field is initialized to `nolla` (zero).

    Kun nykyinen sivu avautuu,

This line declares a new method for the `sivu` class. (`sivu` is an alias to the `HTMLDocument` JavaScript class.)
It begins with the `Kun` keyword.
The name of the method is `avautuu` and the name of the "self" object is `nykyinen sivu`.
(As in Python, the "self" object must be named in the signature of a method.)

    pieneen muuttujaan luetaan luku

Here we call the `luetaan luku` method of `pieni muuttuja`.
The method will prompt a number from the used and store it to the `arvo` field of `pieni muuttuja`.
`pieni muuttuja` is in the illative case, because the `luetaan luku` method requires that case.

    ja nykyinen sivu näyttää pienen muuttujan arvon kertoman.

`ja` keyword is used to specify that this is the last statement in the body of the method.
It is another method call, calling the `näyttää` method of `nykyinen sivu`. (An alias to `HTMLDocument.write`.)
The argument of the method is a function call and the argument of `kertoma` is `pienen muuttujan arvo` (note the genitive case of both arguments).
The field access syntax is identical to the function call syntax.

## Lists

List syntax is used always when there is a block containing multiple items.
The block can be a body of a class, function, if statement or an array.

In many programming languages blocks are created with keywords or symbols
that mark the beginning and the end of the block, for example `begin`/`end` or `{`/`}`.
In Tampio, as in natural languages, the block (called a list) is instead defined by using special separators
that mark either continuation or ending of the list.

After each item in the lsit except the last, there must be a separator token.
A comma (`,`) is used when the list continues after the following item,
and `ja` is used when the list ends after the following item.

    [first item], [second item], ..., [second-last item] ja [last item]

There is a special syntax that must be used when there is only one item in the list:

    [only item] eikä muuta

However, if the current definition would end immediately after the list (ie. there is a period),
it is allowed to leave `eikä muuta` out.

## Classes

As Tampio is an object-oriented language, classes are a crucial feature.
Each class is defined using a set of fields and number of methods.
The fields must be definde together with the class, but methods can be added afterwards.

A class declaration consists of the name of the class in the adessive case and the `on` keyword.

    [name/adessive] on [field list/nominative].

For example:

    Vektorilla on komponentit.

This very simple class, `vektori`, has one field: `komponentit`. As the name of the field is plural, it is an array.

## Functions

In Tampio, a function is always defined for one class and is polymorphic to that class.
This means that it is possible to define the same function differently for multiple classes.

A function always has one parameter and one expression that is the return value.

    [parameter/genitive] [function name] on [expression/nominative].
    [parameter/nominative] [function name/essive] on [expression/nominative]

The name of the parameter must have two words: an adjective and the name of the class.
For example, to define a function called `dimensio` for the `vektori` class,
we must use parameter name that ends in `vektori`:

    Lyhyen vektorin dimensio on lyhyen vektorin komponenttien määrä.

This function will return the dimension of a vector, that is, the number of its components.
The name of the function is `dimensio` and its parameter is `lyhyt vektori`.
`määrä` is a function that return the size of a list.

Here's another function that return the "tail" of a vector:

    Lyhyen vektorin häntä on uusi vektori, jonka komponentit ovat lyhyen vektorin komponentit toisesta alkaen.

Again, its parameter is `lyhyt vektori`.
The function returns a new vector (using the `uusi` keyword) thats components are formed using the slice syntax.

It is possible to not name the parameter, in which case only the class name appears in the signature.
In the body, the word `se` can be used to refer to the unnamed parameter.

    Vektorin dimensio on sen komponenttien määrä.

## Methods

A method is a procedure that can take multiple argumets.

    Kun [self parameter] [verb] [parameters], [statement list].

Each parameter must be in a different case.
The case of the self parameter is restricted by the verb form chosen.
If the verb is expressed in active voice, the self parameter must be in the nominative case.
The passive voice does not restrict cases.

The following method iterates the components of a vector and prints them:

    Kun lyhyt vektori painetaan nykyiselle sivulle,
    	jos lyhyen vektorin dimensio ei ole nolla,
    		nykyinen sivu näyttää lyhyen vektorin ensimmäisen komponentin
    		ja lyhyen vektorin häntä painetaan nykyiselle sivulle.

## Statements

The body of a method is a list of statements.

### Method calls

A method call is written in same way as the signature of the method called.

    [object] [verb] [arguments]

For example, to call the `painetaan` method of `vektori` (defined above) when
the object is in variable `villi vektori`:

    villi vektori painetaan nykyiselle sivulle

If the method returns a value, it can be stored using the `tuloksena` keyword.
If the verb is expressed in active voice, the keyword must have the `-an` possessive suffix.

    [object] [verb/active] [arguments] tuloksenaan [variable]
    [object] [verb/passive] [arguments] tuloksena [variable]

A method call there may be a `missä` modifier, which is used to introduce temporary variables.
They can be referenced in the call immediately before, and in all calls after the modifier.
There must be a comma before `missä`.

    , missä [assignment list]

Each assignment has a variable name and a value:

    [variable name/nominative] on [expression/nominative]

For example, to call `painetaan` with a new vector, we could write

    uusi vektori, jonka komponentteja ovat yksi, kaksi ja kolme eikä muuta,
    	painetaan nykyiselle sivulle

However, it is may be clearer to use a `missä` clause to create a temporary variable,

    väliaikainen vektori painetaan nykyiselle sivulle,
    	missä väliaikainen vektori on uusi vektori, jonka komponentteja ovat yksi, kaksi ja kolme eikä muuta

### Return statements

A method can return a value using the return statement.

    [expression/nominative] palautetaan

For example, to return a zero:

    nolla palautetaan

### If statements

If statements are used to execute other statements conditionally.
An if statement consists of a condition and a list of substatements.
There should be a comma before `jos`.
The `niin` keyword can be used in place of `eikä muuta`, when there is only one condition.

    , jos [condition], niin [statement list]
    , jos [condition list], [statement list]

For example, to iterate an array, one must write a recursive method.
An if statement is used to end the recursion when the array is empty.
Below is a pseudocode of such iteration method.

    Kun pitkää listaa iteroidaan,
    	jos pitkän listan alkioiden määrä ei ole nolla,
    	niin
    		pitkän listan ensimmäinen alkio käsitellään
    	ja	pitkän listan häntää iteroidaan.

An real example would be the `painetaan` method described in the Methods chapter.

A condition consists of two operands and a comparison operator.

    [expression] on [operator] [expression]
    [expression] ei ole [operator] [expression]

The `ei` keyword is used to negate the condition.
Below is a table of available comparison operators.

|Operator                      |JavaScript equivalent|
|:-----------------------------|:--------------------|
|(empty)                       |`==`                 |
|`yhtä kuin`                   |`==`                 |
|`yhtä suuri kuin`             |`==`                 |
|`erisuuri kuin`               |`!=`                 |
|`pienempi kuin`               |`<`                  |
|`suurempi kuin`               |`>`                  |
|`pienempi tai yhtä suuri kuin`|`<=`                 |
|`suurempi tai yhtä suuri kuin`|`>=`                 |

### Assignments

There are three ways to create variables in Tampio: `missä` clauses, return value assignments and assignment statements.
Return value assignments are covered in the method call chapter.
Assignment statements consist of the name of the variable or field in the translative case and an expression.

    [lval/translative] asetetaan [expression/nominative]

For example:

    kivan kaverin kuvaukseksi asetetaan teksti "Hän on kiva"

There is also a special syntax to add a new item to a list, implemented as a method of the array class.
It is similar to the assignment syntax, but the verb is `lisätään` instead of `asetetaan`.

    [list/translative singular] lisätään [expression/nominative]

For example:

    kivan kaverin ystäväksi lisätään mukava kaveri

## Expressions

### Function calls

There are two kinds of function calls in Tampio: genitive calls and essive calls.

In genitive calls, the argument is in the genitive case:

    [argument/genitive] [function name]

For example:

    viiden kertoma      # factorial(5)
    neljän neliöjuuri   # sqrt(4)

The essive calls are typically used to convert a value to another type.
The function name is in the essive case and can appear either before or after the argument.

    [argument] [function name/essive]
    [function name/essive] [argument]

For example:

    viisi merkkijonona  # toString(5)

### Object initialization

The `uusi` keyword is used to create new object.
It is possible to optionally specify the initial values of the fields of the object.

    uusi [type]
    uusi [type], jonka [field assignment list],

Each field assignment has a field name and a value.
The `on` keyword is used when the field name is singular and `ovat` when it is plural.
If the field is an array, it is possible to initialize it using multiple values.
In this case, the field name must be in plural partitive case.

    [field name/nominative] on [value]
    [field name/partitive] ovat [value list]

Examples:

    uusi vektori
    uusi vektori, jonka komponentit ovat villin vektorin komponentit eikä muuta
    uusi vektori, jonka komponentteja ovat pieni luku, suuri luku ja nolla eikä muuta

### Array subscript

If the array is in a field inside an object or a return value of a function, the following syntax is used.

    [object/genitive] [ordinal] [field name/function name]

If the array is instead a variable, the following is used.

    [ordinal] [array object]

For example:

    villin vektorin neljäs komponentti  # villi_vektori.komponentti[4]
    nätin luvun toinen potenssi         # nätti_luku.potenssi[2] = nätti_luku^2
    viides luku                         # luku[5]

The available ordinals are listed below.

|Ordinal      |Corresponding index|
|:------------|:------------------|
|`ensimmäinen`|1                  |
|`toinen`     |2                  |
|`kolmas`     |3                  |
|`neljäs`     |4                  |
|`viides`     |5                  |
|`kuudes`     |6                  |
|`seitsemäs`  |7                  |
|`kahdeksas`  |8                  |
|`yhdeksäs`   |9                  |
|`kymmenes`   |10                 |

The ordinal is a literal.
There is currently no way to retrieve the index from a variable.

### Array slice

The slice syntax is used to retrieve a subarray that contains only the elements that are in a specific range.

    [array object] [ordinal/elative] alkaen
    [array object] [ordinal/illative] päättyen
    [array object] [ordinal/elative] alkaen [ordinal/illative] päättyen

The ordinal before `alkaen` is the start index and the ordinal before `päättyen` is the end index.

### Conditional expression

A conditional expression contains two subexpressions and evaluates one of them depending on the truth value of the condition.

    riippuen siitä, [condition], joko [expression] tai [expression]
    riippuen siitä, [condition list], [expression] tai [expression]

`joko` is a keyword that can be used in place of `eikä muuta` when there is only one condition.

Conditions must be in one of these forms:

    onko [expression] [operator] [expression]
    eikö [expression] ole [operator] [expression]

The operators are as in if statements, see the table in the If statements chapter.

## Standard library

### Array class

The array class does not have a name in Tampio, and is the JavaScript class `Array`.

Pseudodeclaration:

    "Arrayn" määrä on ...
    Kun kivaksi "arrayksi" lisätään kiva arvo, ...

|Member name |Type    |Description|
|:-----------|:------:|:----------|
|`määrä`     |Function|The length of this array (`this.length`).
|`lisätään`  |Method  |Appends the given value to this array (`this.push(arg)`).

### `ajankohta` class

`Ajankohta` is an alias to the JavaScript class `Date`.

Pseudodeclaration:

    Ajankohdalla on vuosi, kuukausi, päivä, tunti, minuutti, sekunti.
    Ajankohta millisekunteina on ...
    Ajankohta merkkijonona on ...
    Ajankohta päivämäärämerkkijonona on ...
    Ajankohta kellonaikamerkkijonona on ...

|Member name |Type    |Description|
|:-----------|:------:|:----------|
|`vuosi`     |Field   |The year (`this.getFullYear()`).
|`kuukausi`  |Field   |The month (0-11, `this.getMonth()`).
|`päivä`     |Field   |The day (`this.getHours()`).
|`tunti`     |Field   |The hour (0-23, `this.getHours()`).
|`minuutti`  |Field   |The hour (0-59, `this.getMinutes()`).
|`sekunti`   |Field   |The second (0-59, `this.getMinutes()`).
|`millisekunteina`|Function|Milliseconds since 1970-01-01 00:00:00 UTC (`this.getTime()`).
|`merkkijonona`|Function|String representation (`this.toLocaleString()`).
|`päivämäärämerkkijonona`|Function|String representation (`this.toLocaleDateString()`).
|`kellonaikamerkkijonona`|Function|String representation (`this.toLocaleTimeString()`).

### `luku` class

`luku` is an alias to the JavaScript class `Number`.

Pseudodeclaration:

    Luvun neliöjuuri on ...
    Luvun vastaluku on ...
    Luvun potenssit ovat ...

|Member name |Type    |Description|
|:-----------|:------:|:----------|
|`neliöjuuri`|Function|The square root of this number (`sqrt(this)`).
|`vastaluku` |Function|The opposite of this number (`-this`).
|`potenssit` |Function|An infinite array of the powers of this number.

### `merkkijono` class

`merkkijono` is an alias to the JavaScript class `String`.

Pseudodeclaration:

    Merkkijonon pituus on ...

|Member name |Type    |Description|
|:-----------|:------:|:----------|
|`pituus`    |Function|The length of this string (`this.length`).

### `muuttuja` class

    Muuttujalla on arvo.
    Kun mukavaan muuttujaan luetaan luku, ...

|Member name |Type    |Description|
|:-----------|:------:|:----------|
|`luetaan`   |Method  |Prompts a number and stores it in this variable.

### `sivu` class

`sivu` is an alias to the JavaScript class `HTMLDocument`.

Pseudodeclaration:

    Kun nykyinen sivu näyttää mielenkiintoisen tekstin, ...

|Member name |Type    |Description|
|:-----------|:------:|:----------|
|`näyttää`   |Method  |Writes the given HTML code to the document (`this.write(arg)`)

## Finnish-English mini dictionary

|Finnish                         |English                                |Example
|--------------------------------|---------------------------------------|-------
|alkaen                          |starting from                          |lyhyen vektorin komponentit toisesta **alkaen**<br/>_the components of the short vector **starting from** the second._
|ei ole                          |is not                                 |pieni luku **ei ole** pienempi kuin kaksi<br/>_the small number **is not** less than two_
|ja                              |and                                    |yksi, kaksi **ja** kolme<br/>_one, two **and** three_
|jos .. niin                     |if .. then                             |**jos** pieni luku ei ole nolla, **niin** pieni luku lisätään pitkään vektoriin<br/>_**if** the small number is not zero **then** the small number is appended to the long vector_
|kun                             |when                                   |**Kun** nykyinen sivu avautuu<br/>_**When** the current page opens_
|lisättynä                       |added to                               |yksi **lisättynä** kahteen<br/>_one **added to** two_
|luku                            |number (type)                          |pieni **luku**<br/>_the small **number**_
|missä                           |where                                  |iso luku, **missä** iso luku on monimutkaisen laskutoimituksen tulos<br/>_the small number, **where** the small number is a result of a complicated calculation_
|määrä                           |number (of items)                      |komponenttien **määrä**<br/>_the **number** of components_
|olkoon                          |let .. be                              |**Olkoon** pieni luku kaksi.<br/>_**Let** the small number **be** two._
|on                              |is, has                                |pieni luku **on** pienempi kuin kaksi<br/>_the small number **is** less than two_<br/>Vektorilla **on** komponentit.<br/>_A vector **has** components._
|ovat                            |are                                    |uusi vektori, jonka komponentit **ovat** yksi, kaksi ja kolme.<br/>_A new vector thats components **are** one, two and three._
|päättyen                        |ending to                              |neljänteen **päättyen**<br/>_**ending to** the fourth_
|riippuen siitä .. joko .. tai ..|depending on whether .. either .. or ..|Olkoon pieni luku **riippuen siitä**, onko kiva luku nolla, **joko** yksi **tai** kaksi.<br/>_Let the small number be, **depending on whether** the nice number is zero, **either** one **or** two._
|se                              |it                                     |**sen** nimi<br/>_**its** name_
|sivu                            |page                                   |nykyinen **sivu**<br/>_the current **page**_

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

## Finnish conjugation

[Finnish verb conjugation] is very complicated. In Tampio, only some of the forms are used.

In the table below, the verbs *lisätä* (to add) and *tulostaa* (to print) are conjugated in the relevant forms.

|Form      |Tense  |Voice  |Person|Number  |Suffix|lisä*tä*   |tulost*aa*    | 
|:---------|:------|:------|:----:|:-------|:----:|:---------:|:------------:|
|Imperative|Present|Active |2     |singular|-A    |lisä*ä*    |tulost*a*     |
|Indicative|Present|Active |3     |singular|-AA   |lis*ää*    |tulost*aa*    |
|Indicative|Present|Active |3     |plural  |-AvAt |lisä*ävät* |tulost*avat*  |
|Indicative|Present|Passive|      |        |-tAAn |lisä*tään* |tulost*etaan* |
|Participle|Present|Active |      |        |-AvA  |lisä*ävä*  |tulost*ava*   |
|Participle|Present|Passive|      |        |-ttAvA|lisä*ttävä*|tulost*ettava*|
|Participle|Past   |Active |      |        |-nUt  |lisä*nnyt* |tulost*anut*  |
|Participle|Past   |Passive|      |        |-ttU  |lisä*tty*  |tulost*ettu*  |

[Finnish verb conjugation]: https://en.wikipedia.org/wiki/Finnish_verb_conjugation

## License

The interpreter is licensed under the GNU General Public License, version 3 or later.
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.
See the LICENSE file for details.

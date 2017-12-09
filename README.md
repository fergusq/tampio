The Tampio Programming Language
===============================

Tampio is an object-oriented programming language that looks like a natural language – Finnish.
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

Tampio is an object-oriented language that compiles to JavaScript.
Its syntax is directly inspired by the Finnish language and is therefore based on inflecting words.

A Tampio file is a list of declarations. Each declaration defines either a class, a function, a method or a global variable.
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

It contains two functions declarations, one variable declaration and one method declaration.
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
The name of the method is `avautuu` and the name of the this object is `nykyinen sivu`.
(As in Python, the this object must be named in the signature of a method.)

    pieneen muuttujaan luetaan luku

Here we call the `luetaan luku` method of `pieni muuttuja`.
The method will prompt a number from the used and store it to the `arvo` field of `pieni muuttuja`.
`pieni muuttuja` is in the illative case, because the `luetaan luku` method requires that case.

    ja nykyinen sivu näyttää pienen muuttujan arvon kertoman.

`ja` keyword is used to specify that this is the last statement in the body of the method.
It is another method call, calling the `näyttää` method of `nykyinen sivu`. (An alias to `HTMLDocument.write`.)
The argument of the method is a function call and the argument of `kertoma` is `pienen muuttujan arvo` (note the genitive case of both arguments).
The field access syntax is identical to the function call syntax.

## Classes

As Tampio is an object-oriented language, classes are a crucial feature.
Each class is defined using a set of fields and number of methods.
The fields must be definde together with the class, but methods can be added afterwards.

A class declaration consists of the name of the class in the adessive case and the `on` keyword.

    Vektorilla on komponentit.

This very simple class, `vektori`, has one field: `komponentit`. As the name of the field is plural, it is a list.

We can now define a function using that class:

    Lyhyen vektorin dimensio on lyhyen vektorin komponenttien määrä.

This function will return the dimension of a vector, that is, the number of its components.
The name of the function is `dimensio` and it has one parameter, `lyhyt vektori`.
`määrä` is a function that return the size of a list.

    Lyhyen vektorin häntä on uusi vektori, jonka komponentit ovat lyhyen vektorin komponentit toisesta alkaen.

The following method iterates the components of a vector and prints them:

    Kun lyhyt vektori painetaan nykyiselle sivulle,
    	jos lyhyen vektorin dimensio ei ole nolla,
    		nykyinen sivu näyttää lyhyen vektorin ensimmäisen komponentin
    		ja lyhyen vektorin häntä painetaan nykyiselle sivulle.

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

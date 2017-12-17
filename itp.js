// Object
Object.prototype.prepend = function(x) { return [this].concat(x); };

// Array
Array.prototype.lisätä_P_N_T = function(kiva_arvo) { this.push(kiva_arvo); };
Array.prototype.f_määrä = function() { return this.length; };

// Lista
function lista(vals) {
 this.alkio = ("alkio" in vals) ? vals["alkio"] : [];
};
lista.prototype.assign = function(n, v) { this[n] = v; };
lista.prototype.f_alkio = function() { return this.alkio; };
lista.prototype.f_koko = function() { return this.alkio.length; };
lista.prototype.f_häntä = function() { return new lista({"alkio": this.alkio.slice(1)}); };
lista.prototype.etsiä_indeksin_A_Ut_N = function(item) { return this.alkio.indexOf(item); };
const tyhjä_lista = new lista({});

// Function
Function.prototype.suorittaa_P__N = function() { this(); }

// Number/luku
const power_handler = {get: (a, b) => Math.pow(a, Number.parseInt(b)+1)};
Number.prototype.f_potenssi = function() { return new Proxy(this, power_handler); };
Number.prototype.f_neliöjuuri = function() { return Math.sqrt(this); };
Number.prototype.f_vastaluku = function() { return -this; };
Number.prototype.f_käänteisluku = function() { return 1/this; };
Number.prototype.f_seuraaja = function() { return this+1; };
Number.prototype.f_edeltäjä = function() { return this-1; };
Number.prototype.f_merkkijono_E = Number.prototype.toString;

// String/merkkijono
String.prototype.f_pituus = function() { return this.length; };
String.prototype.näyttää_käyttäjälle_P__N = function() { alert(this); };
String.prototype.jakaa_P_SeT_N = function(sep, list) { for (var s of this.split(sep)) list.push(s); };

// HTMLDocument/sivu
HTMLDocument.prototype.näyttää_A_G_N = HTMLDocument.prototype.write;
HTMLDocument.prototype.etsiä_elementin_A_StUo_N = function(muuttuja, id) {
 muuttuja.arvo = this.getElementById(id);
};
HTMLDocument.prototype.etsiä_elementin_A_Uo_N = HTMLDocument.prototype.getElementById;

// HTMLElement/elementti
HTMLElement.prototype.assign = function(n, v) {
 switch (n) {
  case "painaa_P__P":
   this.addEventListener("click", v);
   break;
 }
 this[n] = v;
};
HTMLElement.prototype.kirjoittaa_P_N_Ut = function(text) { this.innerHTML += text; };
HTMLElement.prototype.kirjoittaa_P_N_St = function(text) { this.innerHTML += text; };
HTMLElement.prototype.pyyhkiä_P__N = function() { this.innerHTML = ""; };

// Date/aika
Date.prototype.f_päivämäärämerkkijono_E = function() { return this.getLocaleDateString(); };
Date.prototype.f_kellonaikamerkkijono_E = function() { return this.getLocaleTimeString(); };
Date.prototype.f_merkkijono_E = function() { return this.getLocaleString(); };
Date.prototype.f_millisekunti_E = function() { return this.getTime(); };
Date.prototype.f_vuosi = function() { return this.getFullYear(); };
Date.prototype.f_kuukausi = function() { return this.getMonth(); };
Date.prototype.f_päivä = function() { return this.getDay(); };
Date.prototype.f_tunti = function() { return this.getHours(); };
Date.prototype.f_minuutti = function() { return this.getMinutes(); };
Date.prototype.f_sekunti = function() { return this.getSeconds(); };
var nykyinen_aika = new Date();

// muuttuja
function muuttuja(vals) {
 this.arvo = ("arvo" in vals) ? vals["arvo"] : undefined;
};
muuttuja.prototype.assign = function(n, v) { this[n] = v; };
muuttuja.prototype.f_arvo = function() { return this.arvo; };
muuttuja.prototype.lukea_luku_P__St = function() { this.arvo = Number.parseInt(prompt("Syötä luku")); };
muuttuja.prototype.lukea_luku_P_Uo_St = function(p) { this.arvo = Number.parseInt(prompt(p)); };

// toistetaan
function toistaa_KertaaN(n, tehokas_toiminto) { for (var i = 0; i < n; i++) tehokas_toiminto(); };

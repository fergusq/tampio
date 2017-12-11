// Array
Array.prototype.lisätä_P_N_T = function(kiva_arvo) { this.push(kiva_arvo); };
Array.prototype.f_määrä = function() { return this.length; };

// Number/luku
var power_handler = {get: (a, b) => Math.pow(a, Number.parseInt(b)+1)};
Number.prototype.f_potenssi = function() { return new Proxy(this, power_handler); };
Number.prototype.f_neliöjuuri = function() { return Math.sqrt(this); };
Number.prototype.f_vastaluku = function() { return -this; };
Number.prototype.f_merkkijono_E = Number.prototype.toString;

// String/merkkijono
String.prototype.f_pituus = function() { return this.length; };

// HTMLDocument/sivu
HTMLDocument.prototype.näyttää_A_G_N = HTMLDocument.prototype.write;

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
muuttuja.prototype.f_arvo = function() { return this.arvo; };
muuttuja.prototype.lukea_luku_P__St = function() { this.arvo = Number.parseInt(prompt("Syötä luku")); };

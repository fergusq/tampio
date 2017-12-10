// Array
Array.prototype.lisätä_N_T = function(kiva_arvo) { this.push(kiva_arvo); };
Array.prototype.f_määrä = function() { return this.length; };

// Number/luku
var power_handler = {get: (a, b) => Math.pow(a, Number.parseInt(b)+1)};
Number.prototype.f_potenssi = function() { return new Proxy(this, power_handler); };
Number.prototype.f_neliöjuuri = function() { return Math.sqrt(this); };

// HTMLDocument/sivu
HTMLDocument.prototype.näyttää_G_N = function(x) { this.write(x+"\n"); };

// muuttuja
function muuttuja(vals) {
 this.arvo = ("arvo" in vals) ? vals["arvo"] : undefined;
};
muuttuja.prototype.f_arvo = function() { return this.arvo; };
muuttuja.prototype.lukea_luku__St = function() { this.arvo = Number.parseInt(prompt("Syötä luku")); };

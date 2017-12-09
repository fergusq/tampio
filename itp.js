Array.prototype.työntää_N_St = function(kiva_arvo) { this.push(kiva_arvo); }
Array.prototype.f_pituus = function() { return this.length; };
HTMLDocument.prototype.näyttää_G_N = HTMLDocument.prototype.write;

function muuttuja(vals) { this.arvo = ("arvo" in vals) ? vals["arvo"] : undefined; }; muuttuja.prototype.f_arvo = function() { return this.arvo; };
muuttuja.prototype.lukea_luku__St = function() { this.arvo = Number.parseInt(prompt("Syötä luku")); };

function työntää_NSt(kiva_arvo, tyhjä_lista) { tyhjä_lista.push(kiva_arvo); };
Array.prototype.f_pituus = function() { return this.length; };
HTMLDocument.prototype.näyttää_G = HTMLDocument.prototype.write;
HTMLDocument.prototype.lukea_St = function(pieni_muuttuja) { pieni_muuttuja.arvo = Number.parseInt(prompt("Syötä luku")); }

function muuttuja(vals) { this.arvo = ("arvo" in vals) ? vals["arvo"] : undefined; }; muuttuja.prototype.f_arvo = function() { return this.arvo; };

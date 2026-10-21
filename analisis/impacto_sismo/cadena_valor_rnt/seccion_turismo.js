/* Sección 5 del informe ejecutivo, sobre el cruce municipal con el RNT.
   Se mantiene aparte para no volver a tocar el resto del generador cuando
   cambie la definición del universo turístico. */
module.exports = function (H, T) {
  const {P, Rich, tabla, Fu, img, Cap, n, pc, num} = H;
  const TU = T.turismo, TD = T.todos, RNT = T.rnt;
  const MU = T.municipios, mu = k => MU.find(m => m.municipio === k);
  const b = [];
  b.push(P("El turismo se analiza aparte porque es el único sector con un registro "
    + "propio —el Registro Nacional de Turismo— contra el cual contrastar la "
    + "afectación declarada."));
  b.push(tabla(["Indicador", "Cadena turística", "Toda la economía", "Diferencia"], [
    ["Establecimientos afectados", n(TU.n), n(TD.n),
     pc(100 * TU.n / TD.n) + " del censo"],
    ["En nivel crítico o grave", pc(TU.pct_sev), pc(TD.pct_sev),
     "+" + num((TU.pct_sev - TD.pct_sev).toFixed(1)) + " pp"],
    ["No puede operar", pc(TU.pct_no_opera), pc(TD.pct_no_opera),
     "+" + num((TU.pct_no_opera - TD.pct_no_opera).toFixed(1)) + " pp"],
    ["Con algún empleo en riesgo", pc(TU.pct_empl), pc(TD.pct_empl),
     "+" + num((TU.pct_empl - TD.pct_empl).toFixed(1)) + " pp"],
    ["Negocios con empleo en riesgo",
     n(TU.empl_t1 + TU.empl_t2 + TU.empl_t3) + " de " + n(TU.base_empl),
     n(TD.empl_t1 + TD.empl_t2 + TD.empl_t3) + " de " + n(TD.base_empl),
     "+" + num((TU.pct_empl - TD.pct_empl).toFixed(1)) + " pp"],
    ["Pérdidas declaradas, piso", "$" + n(TU.perd_min) + " M",
     "$" + n(TD.perd_min) + " M", pc(100 * TU.perd_min / TD.perd_min) + " del total"],
  ], [3000, 2100, 2100, 2160], {numDesde: 1, textoFinal: true}));
  b.push(Fu("Cadena de valor: los sectores de alojamiento y servicios de comida y de "
    + "transporte y almacenamiento, el mismo criterio del censo ya socializado. "
    + "El empleo se cuenta en negocios y no en puestos: la encuesta pregunta por "
    + "rangos, así que el número de empleos solo puede acotarse en un intervalo "
    + "(" + n(TU.empl_lo) + " a " + n(TU.empl_hi) + " en el turismo). El sector queda "
    + "peor que el promedio en los cuatro indicadores."));

  b.push(Rich([["El contraste con el RNT se hace por municipio, no establecimiento "
    + "por establecimiento. ", "b"],
    ["Las dos bases no comparten identificador —el RNT no trae NIT— y emparejar por "
     + "razón social solo lograba 174 coincidencias sobre " + n(TU.n) + " reportes: "
     + "insuficiente para decir nada de un municipio. Comparar agregados no depende "
     + "de emparejar nada.", ""]]));

  b.push(img("mt2_intensidad.png", 400, 421));
  b.push(Cap("Figura 4. Reportes turísticos por cada 100 prestadores con RNT vigente."));
  b.push(Fu("No es el porcentaje del RNT afectado: el censo incluye negocios sin RNT y "
    + "el registro incluye viviendas turísticas —" + pc(100 * RNT.categorias["VIVIENDAS TURÍSTICAS"] / RNT.vigentes)
    + " del total— que casi nunca reportan. Sirve para comparar municipios entre sí."));

  b.push(Rich([["El corredor norte reporta mucho más daño del que su registro haría "
    + "esperar. ", "b"],
    ["El Dovio (" + Math.round(mu("EL DOVIO").reportes_x100_rnt) + "), El Águila ("
     + Math.round(mu("EL AGUILA").reportes_x100_rnt) + "), El Cairo ("
     + Math.round(mu("EL CAIRO").reportes_x100_rnt) + "), Argelia ("
     + Math.round(mu("ARGELIA").reportes_x100_rnt) + ") y Versalles ("
     + Math.round(mu("VERSALLES").reportes_x100_rnt) + ") están muy por encima de los "
     + num(T.intensidad_dpto) + " reportes por cada 100 inscritos del departamento. "
     + "Cali y Palmira, que concentran la oferta formal, están en "
     + Math.round(mu("CALI").reportes_x100_rnt) + " y "
     + Math.round(mu("PALMIRA").reportes_x100_rnt) + ". Son municipios pequeños con "
     + "turismo mayoritariamente informal, y un ranking por totales los esconde.", ""]]));

  b.push(Rich([["El turismo invierte el orden de la necesidad. ", "b"],
    ["En el conjunto de la economía manda el capital de trabajo; en el turismo manda "
     + "reparar instalaciones (" + pc(100 * TU.nec["Reparar instalaciones o equipos"] / TU.base_nec)
     + " frente a " + pc(100 * TU.nec["Capital de trabajo o insumos"] / TU.base_nec)
     + "). Un hotel o un restaurante no puede vender con el local dañado, y esa es "
     + "una diferencia de diseño del instrumento, no de matiz.", ""]]));

  b.push(P("En el extremo opuesto, Florida, Candelaria y Pradera suman "
    + n(mu("FLORIDA").n + mu("CANDELARIA").n + mu("PRADERA").n) + " reportes turísticos "
    + "entre los tres. Antes de concluir que allí no hubo afectación conviene "
    + "verificar cómo se difundió el formulario."));
  return b;
};

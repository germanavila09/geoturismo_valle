/* Deck de 12 láminas sobre la afectación de la cadena de valor del turismo.
   Reutiliza la franja fotográfica, el crema y los logos del PPT GENERAL de la
   Gobernación para que se lea como continuación del mismo material.

   El cruce con el RNT es SOLO por municipio. Emparejar razones sociales una a
   una solo logra 95 coincidencias sobre 1.839 reportes (5,2 %), porque el RNT
   no trae NIT y mas de la mitad del registro son viviendas turisticas sin
   nombre comercial. El cruce municipal, en cambio, cubre 41 de los 42
   municipios y el 99,9 % de los negocios afectados: por eso es el que sostiene
   las cifras de este deck. El listado nominal va aparte, en el Excel de base
   cruzada.                                                                   */
const fs = require('fs');
const pptxgen = require('pptxgenjs');

const R = JSON.parse(fs.readFileSync('turismo_mun_0903.json', 'utf8'));
const CR = JSON.parse(fs.readFileSync('cruce_0903.json', 'utf8'));
// Perfil con la estructura del informe de la Secretaría de Desarrollo
// Económico (Consejo de Gobierno, 15 de septiembre).
const PF = JSON.parse(fs.readFileSync('perfil_turismo.json', 'utf8'));
const PT = PF.turismo, PD = PF.todos, SEC = PF.secretaria;
const pd = (o, k) => 100 * o.dano[k] / o.base_dano;
const TUR = R.turismo, TOD = R.todos, RNT = R.rnt, MU = R.municipios;
const mu = k => MU.find(m => m.municipio === k);
// Negocios con al menos un empleo comprometido: conteo exacto, sin cotas.
const CON_EMPLEO = TUR.empl_t1 + TUR.empl_t2 + TUR.empl_t3;
// Nombre propio del municipio a partir de la clave en mayúsculas de la base.
const MIN = { DE: 1, DEL: 1, LA: 1, EL: 1, LOS: 1, LAS: 1, Y: 1 };
const TILDE = { ALCALA: 'Alcalá', 'EL AGUILA': 'El Águila', JAMUNDI: 'Jamundí',
  TULUA: 'Tuluá', 'LA UNION': 'La Unión', RIOFRIO: 'Riofrío',
  'GUADALAJARA DE BUGA': 'Buga', BUGA: 'Buga', CALIMA: 'Calima' };
const nm = k => TILDE[k] || k.split(' ').map((w, i) => {
  const b = w.charAt(0) + w.slice(1).toLowerCase();
  return i && MIN[w] ? b.toLowerCase() : b;
}).join(' ');
// Rankings que antes iban escritos a mano.
const SUR = ['FLORIDA', 'CANDELARIA', 'PRADERA'].reduce((a, k) => a + mu(k).n, 0);
// Los tipos vienen sin tildes desde el script de perfil (las claves de
// búsqueda se escriben sin acento); se reponen aquí para la lámina.
const TILDE_TIPO = { 'Cafes, panaderias y heladerias': 'Cafés, panaderías y heladerías',
  'Agencias y operadores turisticos': 'Agencias y operadores turísticos',
  'Atractivos y recreacion': 'Atractivos y recreación' };
const nm2 = t => TILDE_TIPO[t] || t;
const TOP_SEV = [...MU].filter(m => m.n >= 15)
  .sort((a, b) => b.pct_sev - a.pct_sev).slice(0, 4);
const CORREDOR = [...MU].filter(m => m.rnt_vigentes >= 5 && m.reportes_x100_rnt >= 150)
  .sort((a, b) => b.reportes_x100_rnt - a.reportes_x100_rnt);

const CREMA = "FFF9E9", AZUL = "1F3864", ROJO = "B3261E", NARA = "C2410C",
      MORA = "6D28A8", VERD = "2D6A4F", GRIS = "5A5A5A", TENUE = "8A8A8A";
const FR_AGUA = "franja_agua.jpg", FR_SOMB = "franja_sombrero.jpg",
      FR_MUJ = "franja_mujer.jpg", LOGOS = "logos_gob.png";
const FRANJA = 3.21;              // ancho de la franja fotográfica, en pulgadas
const X0 = 3.65, ANCHO = 9.2;     // área de contenido

const n = x => Number(x).toLocaleString('es-CO');
const c1 = x => Number(x).toFixed(1).replace('.', ',');
const c0 = x => Math.round(Number(x));

const pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE';      // 13.33 × 7.5
pres.author = 'Observatorio de Turismo · Valle del Cauca';
pres.title = 'Afectación de la cadena de valor del turismo';

function base(foto) {
  const s = pres.addSlide();
  s.background = { color: CREMA };
  s.addImage({ path: foto, x: 0, y: 0, w: FRANJA, h: 7.5,
    sizing: { type: 'cover', w: FRANJA, h: 7.5 } });
  s.addImage({ path: LOGOS, x: 10.72, y: 6.66, w: 2.25, h: 0.6 });
  return s;
}

function titulo(s, t, bajada) {
  s.addText(t, { x: X0, y: 0.42, w: ANCHO, h: 0.55, fontSize: 25, bold: true,
    color: AZUL, fontFace: 'Calibri', isTextBox: true, margin: 0 });
  if (bajada) s.addText(bajada, { x: X0, y: 0.98, w: ANCHO, h: 0.4, fontSize: 12.5,
    color: GRIS, fontFace: 'Calibri', isTextBox: true, margin: 0 });
}

const fuente = (s, t) => s.addText(t, { x: X0, y: 6.88, w: 7.0, h: 0.3,
  fontSize: 9, italic: true, color: TENUE, fontFace: 'Calibri',
  isTextBox: true, margin: 0 });

/* Tarjeta de cifra: número grande, etiqueta debajo, sin franjas de color. */
function tarjeta(s, x, y, w, h, cifra, etiqueta, pie, col) {
  s.addShape(pres.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.06,
    fill: { color: 'FFFFFF' }, line: { color: 'E6DFCB', width: 1 },
    shadow: { type: 'outer', color: 'C9BFA5', blur: 6, offset: 1, angle: 90, opacity: 0.3 } });
  s.addText(cifra, { x: x + 0.16, y: y + 0.14, w: w - 0.32, h: h * 0.46,
    fontSize: 30, bold: true, color: col || AZUL, fontFace: 'Calibri',
    isTextBox: true, margin: 0, valign: 'middle' });
  s.addText(etiqueta, { x: x + 0.16, y: y + h * 0.50, w: w - 0.32, h: 0.42,
    fontSize: 11.5, bold: true, color: '1A1A1A', fontFace: 'Calibri',
    isTextBox: true, margin: 0 });
  if (pie) s.addText(pie, { x: x + 0.16, y: y + h * 0.72, w: w - 0.32, h: 0.44,
    fontSize: 9.5, color: GRIS, fontFace: 'Calibri', isTextBox: true, margin: 0 });
}

function vinetas(s, x, y, w, items, tam) {
  s.addText(items.map((t, i) => ({
    text: t, options: { bullet: true, breakLine: i < items.length - 1,
      paraSpaceAfter: 9 } })),
    { x, y, w, h: 0.4 + items.length * 0.44, fontSize: tam || 13,
      color: '1A1A1A', fontFace: 'Calibri', isTextBox: true, margin: 0,
      valign: 'top', lineSpacing: (tam || 13) * 1.42 });
}

/* Lee ancho y alto de un PNG desde su cabecera IHDR. Sin esto hay que
   adivinar la proporción y la imagen queda con franjas vacías a los lados. */
function tamPng(f) {
  const b = fs.readFileSync(f);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
}

/* Coloca la imagen lo más grande que quepa en el área y la centra. */
function grafica(s, f, y, hMax, wMax, x) {
  const W = wMax || ANCHO, X = x === undefined ? X0 : x;
  const t = tamPng(f), r = t.w / t.h;
  let w = W, h = W / r;
  if (h > hMax) { h = hMax; w = hMax * r; }
  s.addImage({ path: f, x: X + (W - w) / 2, y: y + (hMax - h) / 2, w, h });
}

/* Lámina de mapa: el mapa a la izquierda del área de contenido y una columna
   de lectura a la derecha. El mapa es casi cuadrado, así que ocuparlo todo a
   lo ancho desperdiciaría media lámina. */
const MAPA_W = 5.95, TXT_X = X0 + MAPA_W + 0.25, TXT_W = ANCHO - MAPA_W - 0.25;

function laminaMapa(s, png, lecturas, colAcento) {
  grafica(s, png, 1.38, 5.45, MAPA_W);
  let y = 1.42;
  lecturas.forEach((l, i) => {
    s.addShape(pres.ShapeType.ellipse, { x: TXT_X, y: y + 0.03, w: 0.29, h: 0.29,
      fill: { color: i === 0 ? (colAcento || ROJO) : AZUL } });
    s.addText(String(i + 1), { x: TXT_X, y: y + 0.03, w: 0.29, h: 0.29,
      fontSize: 12, bold: true, color: 'FFFFFF', align: 'center', valign: 'middle',
      fontFace: 'Calibri', isTextBox: true, margin: 0 });
    s.addText(l[0], { x: TXT_X + 0.4, y: y - 0.04, w: TXT_W - 0.4, h: 0.52,
      fontSize: 11.5, bold: true, color: AZUL, fontFace: 'Calibri',
      isTextBox: true, margin: 0, valign: 'top', lineSpacing: 14 });
    s.addText(l[1], { x: TXT_X + 0.4, y: y + 0.52, w: TXT_W - 0.4, h: 1.25,
      fontSize: 10.5, color: '3A3A3A', fontFace: 'Calibri', isTextBox: true,
      margin: 0, valign: 'top', lineSpacing: 14 });
    y += 1.78;
  });
}

/* ═════ 1 · PORTADA ═════ */
{
  const s = pres.addSlide();
  s.background = { color: CREMA };
  s.addImage({ path: FR_AGUA, x: 0, y: 0, w: FRANJA, h: 7.5,
    sizing: { type: 'cover', w: FRANJA, h: 7.5 } });
  s.addImage({ path: LOGOS, x: 10.72, y: 6.66, w: 2.25, h: 0.6 });
  s.addText('OBSERVATORIO DE TURISMO · VALLE DEL CAUCA',
    { x: X0, y: 1.75, w: ANCHO, h: 0.34, fontSize: 12.5, bold: true, color: GRIS,
      charSpacing: 2.2, fontFace: 'Calibri', isTextBox: true, margin: 0 });
  s.addText('La cadena de valor del turismo\ndespués del terremoto',
    { x: X0, y: 2.2, w: ANCHO, h: 1.5, fontSize: 40, bold: true, color: AZUL,
      fontFace: 'Calibri', isTextBox: true, margin: 0, lineSpacing: 46 });
  s.addText('Censo de afectación y Registro Nacional de Turismo, municipio a municipio',
    { x: X0, y: 3.85, w: ANCHO, h: 0.4, fontSize: 16, color: '3A3A3A',
      fontFace: 'Calibri', isTextBox: true, margin: 0 });
  s.addText([
    { text: `${n(TUR.n)} negocios turísticos afectados en 42 municipios`,
      options: { bold: true, breakLine: true } },
    { text: `${c1(TUR.pct_sev)} % en nivel crítico o grave  ·  ${n(CON_EMPLEO)} con empleo comprometido (${c1(100 * CON_EMPLEO / TUR.n)} %)  ·  $${n(TUR.perd_min)} millones en pérdidas declaradas`,
      options: {} },
  ], { x: X0, y: 4.55, w: ANCHO, h: 0.95, fontSize: 14, color: ROJO,
       fontFace: 'Calibri', isTextBox: true, margin: 0, lineSpacing: 22 });
  s.addText('Corte 3 de septiembre de 2026 · sismo del 10 de agosto de 2026',
    { x: X0, y: 5.7, w: ANCHO, h: 0.3, fontSize: 11, color: TENUE,
      fontFace: 'Calibri', isTextBox: true, margin: 0 });
  s.addNotes('Deck complementario al censo de empresas de turismo afectadas. '
    + 'Cifras recalculadas sobre el corte del 3 de septiembre, depurado de doble notificación. '
    + 'El RNT se compara por municipio, no estableciendo por establecimiento.');
}

/* ═════ 2 · LAS CIFRAS ═════ */
{
  const s = base(FR_SOMB);
  titulo(s, 'Las cifras que resumen el impacto',
    `Alojamiento, comida y transporte · ${n(TUR.n)} de los ${n(TOD.n)} establecimientos del censo`);
  const W = 2.9, H = 1.62, GX = 0.25, GY = 0.28;
  const filas = [
    [[n(TUR.n), 'Negocios afectados', `${c1(100 * TUR.n / TOD.n)} % del censo total`, ROJO],
     [`${c1(TUR.pct_sev)} %`, 'En nivel crítico o grave', `${n(TUR.sev)} establecimientos`, ROJO],
     [`${c1(TUR.pct_no_opera)} %`, 'No puede operar', `${n(TUR.no_opera)} de ${n(TUR.base_cont)} que informan`, NARA]],
    [[n(CON_EMPLEO), 'Con empleo en riesgo', `${c1(100 * CON_EMPLEO / TUR.n)} % de los ${n(TUR.n)} · ${c1(TUR.pct_empl)} % de los ${n(TUR.base_empl)} que responden`, NARA],
     [`$${n(TUR.perd_min)} M`, 'Pérdidas declaradas', `piso; ${TUR.perd_ab} sin techo declarado`, ROJO],
     [n(RNT.vigentes), 'Prestadores con RNT', `oferta formal vigente ${RNT.ano}`, AZUL]],
  ];
  filas.forEach((f, r) => f.forEach((t, i) => tarjeta(s,
    X0 + i * (W + GX), 1.58 + r * (H + GY), W, H, t[0], t[1], t[2], t[3])));
  s.addText([
    { text: 'Lectura. ', options: { bold: true } },
    { text: `El turismo es el ${c1(100 * TUR.n / TOD.n)} % de los establecimientos que `
      + `reportaron daño, pero aporta el ${c1(100 * TUR.perd_min / TOD.perd_min)} % de las `
      + `pérdidas declaradas y está peor que el promedio en los cuatro indicadores.`,
      options: {} },
  ], { x: X0, y: 5.35, w: ANCHO, h: 0.75, fontSize: 12.5, color: '1A1A1A',
       fontFace: 'Calibri', isTextBox: true, margin: 0, lineSpacing: 18 });
  fuente(s, `Base depurada de doble notificación · corte 3 de septiembre de 2026 · ${n(R.recibidos)} reportes recibidos, ${n(R.dobles)} dobles notificaciones retiradas.`);
}

/* ═════ 3 · MAPA · LA OFERTA FORMAL ═════ */
{
  const s = base(FR_MUJ);
  const cats = RNT.categorias;   // objeto, no Object.entries: indexar un array por clave da NaN
  titulo(s, 'Dónde está la oferta turística formal',
    `${n(RNT.vigentes)} prestadores con RNT vigente ${RNT.ano} · ${n(RNT.empleos_rnt)} empleos declarados al registro`);
  laminaMapa(s, 'mt4_oferta.png', [
    ['El registro se concentra en Cali',
     `${n(mu('CALI').rnt_vigentes)} de los ${n(RNT.vigentes)} prestadores están en la capital `
     + `(${c1(100 * mu('CALI').rnt_vigentes / RNT.vigentes)} %). Le siguen Palmira con `
     + `${n(mu('PALMIRA').rnt_vigentes)}, Buga con ${n(mu('BUGA').rnt_vigentes)} y Calima con `
     + `${n(mu('CALIMA').rnt_vigentes)}.`],
    ['Más de la mitad son viviendas turísticas',
     `${n(cats['VIVIENDAS TURÍSTICAS'])} de ${n(RNT.vigentes)} `
     + `(${c1(100 * cats['VIVIENDAS TURÍSTICAS'] / RNT.vigentes)} %), seguidas de agencias de viajes `
     + `(${n(cats['AGENCIAS DE VIAJES'])}) y alojamiento turístico `
     + `(${n(cats['ESTABLECIMIENTOS DE ALOJAMIENTO TURÍSTICO'])}).`],
    ['El RNT se renueva cada año',
     `«Vigente» significa corte ${RNT.ano}. Los ${n(RNT.historicos)} códigos históricos `
     + `incluyen registros caducados y no representan oferta activa.`],
  ], AZUL);
  fuente(s, 'Registro Nacional de Turismo · Valle del Cauca · corte 2026.');
}

/* ═════ 4 · MAPA · NEGOCIOS AFECTADOS ═════ */
{
  const s = base(FR_AGUA);
  const cali = mu('CALI'), bva = mu('BUENAVENTURA'), rol = mu('ROLDANILLO');
  titulo(s, 'Negocios turísticos afectados por municipio',
    `${n(TUR.n)} establecimientos de alojamiento, comida y transporte reportaron daño`);
  laminaMapa(s, 'mt1_afectados.png', [
    ['Cali, Buenaventura y Roldanillo concentran el volumen',
     `${n(cali.n)}, ${n(bva.n)} y ${n(rol.n)} reportes: entre los tres suman el `
     + `${c1(100 * (cali.n + bva.n + rol.n) / TUR.n)} % del total departamental.`],
    ['El norte aparece completo',
     'Cartago, Sevilla, Alcalá, Caicedonia, La Unión, Zarzal, Versalles y Ansermanuevo '
     + 'forman un bloque continuo de veinte o más reportes cada uno.'],
    ['El sur casi no reporta',
     `Florida (${n(mu('FLORIDA').n)}), Candelaria (${n(mu('CANDELARIA').n)}) y Pradera `
     + `(${n(mu('PRADERA').n)}) suman ${n(SUR)} reportes turísticos entre los tres.`],
  ]);
  fuente(s, 'Cada municipio muestra su nombre y su número de reportes. Geometría: DANE.');
}

/* ═════ 5 · RANKING POR SEVERIDAD ═════ */
{
  const s = base(FR_SOMB);
  const cali = mu('CALI');
  titulo(s, 'Los quince municipios con más negocios afectados, sin Cali',
    `Cali aparte con ${n(cali.n)} reportes y ${c1(cali.pct_sev)} % en nivel crítico o grave`);
  grafica(s, 't1_severidad.png', 1.45, 5.15);
  fuente(s, `Nivel de afectación declarado por el establecimiento en el censo. `
    + `${n(TUR.no_afectado)} de los ${n(TUR.n)} reportes turísticos declaran no haber sufrido `
    + `afectación y se muestran aparte en la barra.`);
}

/* ═════ 6 · MAPA · INTENSIDAD ═════ */
{
  const s = base(FR_MUJ);
  titulo(s, 'Peso del daño frente al tamaño de la oferta formal',
    'Reportes turísticos por cada 100 prestadores con RNT vigente en el municipio');
  laminaMapa(s, 'mt2_intensidad.png', [
    ['El corredor norte concentra la intensidad',
     `El Dovio (${c0(mu('EL DOVIO').reportes_x100_rnt)}), El Águila `
     + `(${c0(mu('EL AGUILA').reportes_x100_rnt)}), El Cairo `
     + `(${c0(mu('EL CAIRO').reportes_x100_rnt)}), Argelia `
     + `(${c0(mu('ARGELIA').reportes_x100_rnt)}) y Versalles `
     + `(${c0(mu('VERSALLES').reportes_x100_rnt)}) reportan mucho más daño del que su `
     + `registro formal haría esperar.`],
    ['Cali y Palmira están en el extremo opuesto',
     `${c0(mu('CALI').reportes_x100_rnt)} y ${c0(mu('PALMIRA').reportes_x100_rnt)} reportes `
     + `por cada 100 inscritos, frente a ${c1(R.intensidad_dpto)} del departamento. `
     + `Concentran la oferta, no la intensidad del daño.`],
    ['No es el porcentaje del RNT afectado',
     'El censo incluye negocios sin RNT y el registro incluye viviendas turísticas que casi '
     + 'nunca reportan. El indicador compara municipios entre sí, no mide una tasa.'],
  ], MORA);
  fuente(s, 'Censo de afectación (3 sep) y RNT vigente 2026, agregados por municipio.');
}

/* ═════ 7 · MAPA · SEVERIDAD ═════ */
{
  const s = base(FR_AGUA);
  titulo(s, 'Severidad declarada por el sector turístico',
    `${c1(TUR.pct_sev)} % departamental en nivel crítico o grave, frente a ${c1(TOD.pct_sev)} % de toda la economía`);
  laminaMapa(s, 'mt3_severidad.png', [
    ['El norte alto es el más severo',
     // Escribir estos nombres a mano ya falló una vez: se ordenan del dato.
     `Con al menos quince reportes, encabezan ${TOP_SEV.map(m =>
        `${nm(m.municipio)} (${c0(m.pct_sev)} %)`).join(', ')}. Todos por encima `
     + `del ${c1(TUR.pct_sev)} % departamental.`],
    ['Buenaventura combina volumen e intensidad',
     `${n(mu('BUENAVENTURA').n)} reportes con ${c0(mu('BUENAVENTURA').pct_sev)} % en nivel `
     + `crítico o grave: es el único municipio que está arriba en las dos lecturas.`],
    ['Cuidado con los municipios de pocos reportes',
     `El Cerrito marca ${c0(mu('EL CERRITO').pct_sev)} % sobre ${n(mu('EL CERRITO').n)} reportes `
     + `y Candelaria ${c0(mu('CANDELARIA').pct_sev)} % sobre ${n(mu('CANDELARIA').n)}. `
     + 'En esos casos el porcentaje describe un puñado de casos, no al municipio.'],
  ], NARA);
  fuente(s, 'Porcentaje calculado sobre los reportes turísticos de cada municipio.');
}

/* ═════ 8 · EMPLEO Y PÉRDIDAS ═════ */
{
  const s = base(FR_SOMB);
  titulo(s, 'Empleo comprometido y pérdidas declaradas',
    `${n(CON_EMPLEO)} negocios con empleo comprometido · ${c1(TUR.pct_empl)} % de los ${n(TUR.base_empl)} que responden la pregunta · ${c1(100 * CON_EMPLEO / TUR.n)} % de los ${n(TUR.n)} afectados`);
  grafica(s, 't3_empleo_perdidas.png', 1.42, 4.5);
  s.addText([
    { text: 'El empleo en riesgo está pulverizado. ', options: { bold: true } },
    { text: `${c1(100 * TUR.empl_t1 / CON_EMPLEO)} % de esos negocios reporta entre uno y cinco `
      + `puestos, y solo ${n(TUR.empl_t3)} en todo el departamento reportan más de veinte. `
      + `Son muchísimos establecimientos con pocos empleos cada uno, no unas pocas empresas `
      + `grandes: eso define el tamaño del subsidio y el número de operaciones, no el monto total.`,
      options: {} },
  ], { x: X0, y: 6.02, w: ANCHO, h: 0.78, fontSize: 12, color: '1A1A1A',
       fontFace: 'Calibri', isTextBox: true, margin: 0, lineSpacing: 17 });
  fuente(s, 'Los tramos cuentan negocios, no empleos: la encuesta pregunta por rangos. '
    + `${n(TUR.n - TUR.base_empl)} de los ${n(TUR.n)} negocios turísticos dejaron esta pregunta en blanco `
    + 'y quedan fuera del porcentaje sobre quienes responden.');
  s.addNotes('El tramo de empleo es un conteo exacto de establecimientos. '
    + `La cifra de empleos (${n(TUR.empl_lo)} a ${n(TUR.empl_hi)} en el departamento) es `
    + 'un intervalo porque los rangos no permiten sumar exacto, y por eso no se grafica aquí.');
}


/* ═════ 9 · CONTINUIDAD DEL NEGOCIO ═════
   Réplica del bloque «Continuidad del negocio» del informe de la Secretaría,
   acotado al turismo y puesto al lado del dato departamental. */
{
  const s = base(FR_MUJ);
  titulo(s, 'Continuidad del negocio en la cadena turística',
    `${n(PT.base_cont)} de los ${n(PT.n)} negocios turísticos informan su estado de operación`);
  grafica(s, 'p1_continuidad.png', 1.45, 2.05);
  const W = 2.9, H = 1.5, GX = 0.25;
  const t = [
    [`${c1(PT.pct_normal)} %`, 'Opera normalmente', `${n(PT.normal)} negocios`, VERD],
    [`${c1(PT.pct_parcial)} %`, 'Opera parcialmente', `${n(PT.parcial)} negocios`, NARA],
    [`${c1(PT.pct_no_opera)} %`, 'No puede operar', `${n(PT.no_opera)} negocios`, ROJO],
  ];
  t.forEach((x, i) => tarjeta(s, X0 + i * (W + GX), 3.78, W, H, x[0], x[1], x[2], x[3]));
  s.addText([
    { text: `${c1(PT.pct_restriccion)} % de la cadena turística no ha recuperado su operación normal. `,
      options: { bold: true } },
    { text: `El cierre total pesa ${c1(PT.pct_no_opera - PD.pct_no_opera)} puntos más que en el `
      + `conjunto de la economía (${c1(PT.pct_no_opera)} % frente a ${c1(PD.pct_no_opera)} %), `
      + `y la operación normal pesa ${c1(PD.pct_normal - PT.pct_normal)} puntos menos. `
      + `El cuello de botella del sector no es vender: es volver a abrir.`, options: {} },
  ], { x: X0, y: 5.48, w: ANCHO, h: 0.9, fontSize: 12.5, color: '1A1A1A',
       fontFace: 'Calibri', isTextBox: true, margin: 0, lineSpacing: 18 });
  fuente(s, `Misma variable y misma construcción del informe de la Secretaría de Desarrollo `
    + `Económico · ${n(PT.n - PT.base_cont)} negocios turísticos no informan operación.`);
  s.addNotes('El informe departamental reporta 29,5 % normal, 42,2 % parcial y 28,4 % sin '
    + 'operar sobre 12.629 empresas. Esta base, depurada de doble notificación, da '
    + `${c1(PD.pct_normal)} / ${c1(PD.pct_parcial)} / ${c1(PD.pct_no_opera)} sobre `
    + `${n(PD.base_cont)}: la diferencia es menor a un punto en los tres estados.`);
}

/* ═════ 10 · QUÉ SE DAÑÓ ═════ */
{
  const s = base(FR_AGUA);
  const INF = 'Infraestructura, maquinaria o equipos';
  const INV = 'Inventarios o mercancías';
  titulo(s, 'Qué se dañó en los negocios turísticos',
    `Afectaciones declaradas por ${n(PT.base_dano)} establecimientos · selección múltiple`);
  grafica(s, 'p2_dano.png', 1.42, 3.9);
  s.addText([
    { text: 'El daño del turismo es físico antes que comercial. ', options: { bold: true } },
    { text: `${c1(pd(PT, INF))} % reporta daño en infraestructura, maquinaria o equipos, `
      + `${c1(pd(PT, INF) - pd(PD, INF))} puntos por encima del resto de la economía `
      + `(${c1(pd(PD, INF))} %). En inventarios pasa lo contrario: `
      + `${c1(pd(PT, INV))} % frente a ${c1(pd(PD, INV))} %, porque un hotel o un `
      + `restaurante no vive de la mercancía en bodega sino del local y del equipo.`,
      options: {} },
  ], { x: X0, y: 5.58, w: ANCHO, h: 1.1, fontSize: 12.5, color: '1A1A1A',
       fontFace: 'Calibri', isTextBox: true, margin: 0, lineSpacing: 18 });
  fuente(s, 'Los porcentajes no suman 100: cada establecimiento puede marcar varias opciones.');
}

/* ═════ 11 · TIPOS DE NEGOCIO ═════
   El informe departamental deja el turismo como un solo renglón del 16 %.
   Esta lámina lo abre; la base tipificable se declara siempre. */
{
  const s = base(FR_SOMB);
  const T1 = PF.tipificables[0], T2 = PF.tipificables[1];
  const peor = [...PF.tipificables].filter(t => t.n >= 13)
    .sort((a, b) => b.pct_sev - a.pct_sev)[0];
  titulo(s, 'Qué tipo de negocio turístico resultó afectado',
    `${n(PF.base_tipo)} de los ${n(PT.n)} establecimientos cuyo nombre comercial permite identificar el tipo`);
  grafica(s, 'p3_tipos.png', 1.42, 4.15);
  s.addText([
    { text: `${nm2(T1.tipo)} y ${nm2(T2.tipo).toLowerCase()} concentran el `
      + `${c1(T1.pct_tipificables + T2.pct_tipificables)} % de lo tipificable. `,
      options: { bold: true } },
    { text: `Son ${n(T1.n)} y ${n(T2.n)} establecimientos. `
      + `Pero el alojamiento está más golpeado: ${c1(T2.pct_sev)} % en crítico o grave `
      + `frente a ${c1(T1.pct_sev)} % de la comida, y declara $${n(T2.perd_min)} millones `
      + `con la mitad de establecimientos. El tipo con mayor severidad es `
      + `${nm2(peor.tipo).toLowerCase()} (${c1(peor.pct_sev)} %).`, options: {} },
  ], { x: X0, y: 5.72, w: ANCHO, h: 1.0, fontSize: 12, color: '1A1A1A',
       fontFace: 'Calibri', isTextBox: true, margin: 0, lineSpacing: 17 });
  fuente(s, `El formulario no pregunta el tipo de negocio: se deduce de palabras del nombre `
    + `comercial. ${n(PF.sin_tipificar['Sin clasificar'])} nombres no traen ninguna palabra `
    + `reconocible y ${n(PF.sin_tipificar['Registrado a nombre de persona natural'])} están `
    + `registrados a nombre de una persona natural; ambos quedan fuera de esta lámina.`);
  s.addNotes('La tipología es una heurística sobre la razón social, no un dato del censo. '
    + 'Sirve para orientar el diseño del alivio, no para contar el universo. '
    + 'Pedir el tipo de prestador en el formulario cerraría este vacío.');
}

/* ═════ 12 · MAPA · PÉRDIDAS ESTIMADAS ═════ */
{
  const s = base(FR_AGUA);
  const totMun = MU.reduce((a, m) => a + (m.perd_min || 0), 0);
  const top5 = [...MU].sort((a, b) => b.perd_min - a.perd_min).slice(0, 5);
  const cali = mu('CALI'), bva = mu('BUENAVENTURA'), rol = mu('ROLDANILLO');
  titulo(s, 'Pérdidas estimadas por municipio',
    `$${n(TUR.perd_min)} millones declarados por la cadena turística · cota inferior`);
  grafica(s, 'mt5_perdidas.png', 1.32, 5.0, 5.6);
  grafica(s, 'mt5_ranking.png', 1.32, 5.0, 3.35, X0 + 5.8);
  s.addText([
    { text: 'Cinco municipios concentran el '
      + `${c1(100 * top5.reduce((a, m) => a + m.perd_min, 0) / totMun)} % de las pérdidas. `,
      options: { bold: true } },
    { text: `Cali aporta ${c1(100 * cali.perd_min / totMun)} %, Buenaventura `
      + `${c1(100 * bva.perd_min / totMun)} % y Roldanillo ${c1(100 * rol.perd_min / totMun)} %, `
      + `que con ${n(rol.n)} negocios declara el ${c0(100 * rol.perd_min / bva.perd_min)} % `
      + `de lo que declara Buenaventura, que tiene ${n(bva.n)}.`, options: {} },
  ], { x: X0, y: 6.40, w: ANCHO, h: 0.5, fontSize: 11.5, color: '1A1A1A',
       fontFace: 'Calibri', isTextBox: true, margin: 0, lineSpacing: 16 });
  fuente(s, 'Cota inferior: piso de cada rango declarado más $100 millones por cada uno de '
    + `los ${TUR.perd_ab} reportes del tramo abierto. El daño real es mayor.`);
  s.addNotes('La variable «Pérdidas económicas» se declara en cuatro rangos. La suma solo '
    + 'puede acotarse por abajo, porque el tramo «más de $100 millones» no tiene techo. '
    + `${n(TUR.base_perd)} de los ${n(TUR.n)} negocios turísticos respondieron esta pregunta.`);
}

/* ═════ 13 · ALIVIOS ═════ */
{
  const s = base(FR_MUJ);
  titulo(s, 'Qué alivios pide el sector',
    'La necesidad declarada y el instrumento financiero preferido');
  grafica(s, 't4_alivios.png', 1.5, 4.0);
  s.addText([
    { text: 'El turismo invierte el orden del resto de la economía. ', options: { bold: true } },
    { text: `En el departamento manda el capital de trabajo; en el turismo manda reparar `
      + `instalaciones (${c1(100 * TUR.nec['Reparar instalaciones o equipos'] / TUR.base_nec)} % `
      + `frente a ${c1(100 * TUR.nec['Capital de trabajo o insumos'] / TUR.base_nec)} %). `
      + `Un hotel o un restaurante no puede vender con el local dañado. `
      + `Y el ${c1(100 * TUR.apo['Capital semilla (no reembolsable)'] / TUR.base_apo)} % `
      + `pide capital no reembolsable frente a `
      + `${c1(100 * TUR.apo['Nuevo crédito'] / TUR.base_apo)} % que pide crédito.`, options: {} },
  ], { x: X0, y: 5.62, w: ANCHO, h: 1.1, fontSize: 12.5, color: '1A1A1A',
       fontFace: 'Calibri', isTextBox: true, margin: 0, lineSpacing: 18 });
  fuente(s, 'Selección múltiple: los porcentajes no suman 100.');
}

/* ═════ 14 · TURISMO VS ECONOMÍA ═════ */
{
  const s = base(FR_AGUA);
  titulo(s, 'El turismo quedó peor que el promedio de la economía',
    'Mismos indicadores, mismo corte, mismas bases de respuesta');
  grafica(s, 't5_contraste.png', 1.5, 4.0);
  /* Cuál es la mayor diferencia se calcula: escribirla a mano ya falló una vez. */
  const BR = [['la severidad', 'pct_sev', 'está en nivel crítico o grave'],
              ['la parálisis', 'pct_no_opera', 'no puede operar'],
              ['el empleo en riesgo', 'pct_empl', 'tiene algún empleo en riesgo'],
              ['las pérdidas altas', 'pct_perd_alta', 'declara pérdidas sobre $20 millones']];
  const may = BR.map(b => ({ et: b[0], txt: b[2], d: TUR[b[1]] - TOD[b[1]],
    t: TUR[b[1]], g: TOD[b[1]] })).sort((a, b) => b.d - a.d)[0];
  s.addText([
    { text: `La diferencia más grande está en ${may.et}: `, options: { bold: true } },
    { text: `${c1(may.t)} % de los negocios turísticos ${may.txt}, frente a `
      + `${c1(may.g)} % del total de la economía. Son ${c1(may.d)} puntos, sobre un sector `
      + `que además vive de un flujo de visitantes que también se interrumpió.`, options: {} },
  ], { x: X0, y: 5.62, w: ANCHO, h: 0.9, fontSize: 12.5, color: '1A1A1A',
       fontFace: 'Calibri', isTextBox: true, margin: 0, lineSpacing: 18 });
  fuente(s, `Cadena turística frente a los ${n(TOD.n)} establecimientos de todos los sectores.`);
}

/* ═════ 15 · QUÉ HACER ═════ */
{
  const s = base(FR_SOMB);
  titulo(s, 'Cinco decisiones que se desprenden de estos datos', null);
  const acc = [
    ['Diseñar el alivio principal como capital no reembolsable con componente de obra.',
     `El ${c1(100 * TUR.apo['Capital semilla (no reembolsable)'] / TUR.base_apo)} % lo pide así, y la necesidad número uno del sector es reparar instalaciones.`],
    ['No exigir RNT vigente como requisito de entrada.',
     `El censo recoge cualquier negocio turístico; el RNT tiene ${n(RNT.vigentes)} inscritos y más de la mitad son viviendas turísticas. Condicionar el alivio al registro deja fuera al turismo informal, que es el que más reporta en el norte.`],
    ['Atender el corredor norte por intensidad, no por volumen.',
     `${CORREDOR.map(m => nm(m.municipio)).join(', ')} reportan entre `
     + `${c0(Math.min(...CORREDOR.map(m => m.reportes_x100_rnt)))} y `
     + `${c0(Math.max(...CORREDOR.map(m => m.reportes_x100_rnt)))} daños por cada 100 inscritos: `
     + 'son municipios pequeños que un ranking por totales esconde.'],
    ['Revisar por qué el sur casi no reporta.',
     `Florida, Candelaria y Pradera suman ${n(mu('FLORIDA').n + mu('CANDELARIA').n + mu('PRADERA').n)} reportes turísticos entre los tres. Antes de concluir que no hubo daño conviene verificar cómo se difundió el formulario.`],
    ['Pedir el código RNT en el formulario de reporte.',
     'Hoy las dos bases solo pueden compararse por municipio. Un campo de RNT permitiría medir la afectación del registro establecimiento por establecimiento.'],
  ];
  let y = 1.5;
  acc.forEach((a, i) => {
    s.addShape(pres.ShapeType.ellipse, { x: X0, y: y + 0.04, w: 0.34, h: 0.34,
      fill: { color: i < 2 ? ROJO : AZUL } });
    s.addText(String(i + 1), { x: X0, y: y + 0.04, w: 0.34, h: 0.34, fontSize: 14,
      bold: true, color: 'FFFFFF', align: 'center', valign: 'middle',
      fontFace: 'Calibri', isTextBox: true, margin: 0 });
    s.addText(a[0], { x: X0 + 0.5, y, w: ANCHO - 0.5, h: 0.3, fontSize: 13.5,
      bold: true, color: AZUL, fontFace: 'Calibri', isTextBox: true, margin: 0 });
    s.addText(a[1], { x: X0 + 0.5, y: y + 0.32, w: ANCHO - 0.5, h: 0.62, fontSize: 11,
      color: '3A3A3A', fontFace: 'Calibri', isTextBox: true, margin: 0,
      valign: 'top', lineSpacing: 14 });
    y += 1.07;
  });
  fuente(s, 'Elaboración propia sobre el censo de afectación y el RNT vigente.');
}

/* ═════ 16 · MÉTODO ═════ */
{
  const s = base(FR_MUJ);
  titulo(s, 'Cómo se construyeron estas cifras', null);
  s.addText('Fuentes', { x: X0, y: 1.22, w: ANCHO, h: 0.3, fontSize: 14, bold: true,
    color: AZUL, fontFace: 'Calibri', isTextBox: true, margin: 0 });
  vinetas(s, X0, 1.56, ANCHO, [
    `Censo de afectación empresarial · ${n(TOD.n)} establecimientos únicos tras depurar ${n(R.dobles)} dobles notificaciones sobre ${n(R.recibidos)} reportes recibidos, corte 3 de septiembre de 2026.`,
    `Registro Nacional de Turismo del Valle · ${n(RNT.vigentes)} prestadores vigentes ${RNT.ano} en ${RNT.municipios} municipios, ${n(RNT.empleos_rnt)} empleos declarados.`,
  ], 11.8);
  s.addText('Qué cuenta como cadena de valor del turismo', { x: X0, y: 2.70, w: ANCHO,
    h: 0.3, fontSize: 14, bold: true, color: AZUL, fontFace: 'Calibri',
    isTextBox: true, margin: 0 });
  vinetas(s, X0, 3.04, ANCHO, [
    `Los sectores «${R.definicion[0]}» y «${R.definicion[1]}» del censo: ${n(TUR.n)} establecimientos. Es el mismo criterio con el que se construyó la cifra ya socializada, aplicado a la base depurada.`,
    `Dentro de esos ${n(TUR.n)}, ${n(TUR.no_afectado)} declaran no haber sufrido afectación. Se conservan en el universo para no romper la comparación con la cifra ya socializada, y quedan visibles como categoría propia en los gráficos.`,
  ], 11.8);
  s.addText('Por qué el cruce con el RNT es solo municipal', { x: X0, y: 4.62, w: ANCHO,
    h: 0.3, fontSize: 14, bold: true, color: AZUL, fontFace: 'Calibri',
    isTextBox: true, margin: 0 });
  vinetas(s, X0, 4.96, ANCHO, [
    `Las dos bases no comparten identificador: el RNT no trae NIT. Emparejar por razón social uno a uno solo logra ${n(CR.cruzan)} coincidencias sobre ${n(TUR.n)} reportes (${c1(100 * CR.cruzan / TUR.n)} %), base insuficiente para decir nada por municipio.`,
    `El cruce municipal, en cambio, cubre ${RNT.municipios} de los ${MU.length} municipios y el ${c1(100 * (TUR.n - mu('OBANDO').n) / TUR.n)} % de los negocios afectados: se comparan agregados —cuántos prestadores inscritos hay y cuántos reportes de daño se recibieron—, sin depender de emparejar nombres.`,
    'De ahí que «reportes por cada 100 inscritos» sea un indicador de comparación entre municipios y no una tasa de afectación del registro.',
  ], 11);
  fuente(s, 'Scripts reproducibles: cruce_rnt_0903.py, turismo_mun_0903.py, mapas_turismo.py, figuras_turismo.py, deck_turismo.js. '
    + 'El listado nominal establecimiento por establecimiento va en el Excel de base cruzada.');
}

pres.writeFile({ fileName: 'Turismo_afectacion_RNT_2026-09-21.pptx' })
  .then(f => console.log('generado:', f));

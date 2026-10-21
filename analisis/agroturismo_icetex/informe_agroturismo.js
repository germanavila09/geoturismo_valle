/* Línea base de afectación del sector turístico y agroturístico del Valle del
   Cauca tras el sismo del 10 de agosto de 2026.

   Documento de insumo para la propuesta UCEVA y aliados a la convocatoria de
   subvenciones de ICETEX. Todo el contenido numérico se lee de los JSON
   producidos por los scripts del observatorio; no hay cifras escritas a mano,
   porque hacerlo ya introdujo errores antes.

   PROTECCIÓN DE DATOS
   El documento es exclusivamente de agregados municipales. No contiene nombre,
   documento, teléfono, correo, NIT, dirección, barrio ni razón social de
   ningún reportante.                                                        */
const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, PageBreak,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle, ImageRun,
  TableOfContents, Header, Footer, PageNumber, convertInchesToTwip,
} = require('docx');

const AG = JSON.parse(fs.readFileSync('agroturismo.json', 'utf8'));
const PF = JSON.parse(fs.readFileSync('perfil_turismo.json', 'utf8'));
const TU = AG.turismo, AGRO = AG.agro, RNT = AG.rnt, MU = AG.municipios;
const PT = PF.turismo;
const mu = k => MU.find(m => m.municipio === k);
/* Une una lista en prosa: «A, B y C». Hacerlo con join(' y ') produjo
   «A y B y C» en la primera versión del documento. */
const lista = a => a.length < 2 ? (a[0] || '')
  : a.slice(0, -1).join(', ') + ' y ' + a[a.length - 1];

const AZUL = '1F3864', ROJO = 'B3261E', GRIS = '5A5A5A', VERDE = '2D6A4F';
const CREMA = 'FBF6E9', BORDE = 'D8D0B8';

const n = x => Number(x).toLocaleString('es-CO');
const c1 = x => Number(x).toFixed(1).replace('.', ',');
const c0 = x => String(Math.round(Number(x)));
const pct = (a, b) => c1(100 * a / b);

/* Nombres propios: la base guarda el municipio en mayúsculas sin tildes. */
const TILDE = {
  ALCALA: 'Alcalá', ANDALUCIA: 'Andalucía', BOLIVAR: 'Bolívar',
  'EL AGUILA': 'El Águila', GUACARI: 'Guacarí', JAMUNDI: 'Jamundí',
  'LA UNION': 'La Unión', RIOFRIO: 'Riofrío', TULUA: 'Tuluá', BUGA: 'Buga',
  CALIMA: 'Calima (El Darién)', CALI: 'Cali',
};
const MIN = { DE: 1, DEL: 1, LA: 1, EL: 1, LOS: 1, LAS: 1, Y: 1 };
const nm = k => TILDE[k] || k.split(' ').map((w, i) => {
  const b = w.charAt(0) + w.slice(1).toLowerCase();
  return i && MIN[w] ? b.toLowerCase() : b;
}).join(' ');

/* ── piezas de texto ─────────────────────────────────────────────────── */
const p = (text, o = {}) => new Paragraph({
  spacing: { after: o.after === undefined ? 140 : o.after, line: 288 },
  alignment: o.align,
  indent: o.indent,
  children: [new TextRun({
    text, size: (o.size || 10.5) * 2, color: o.color || '1A1A1A',
    bold: o.bold, italics: o.italics, font: 'Calibri',
  })],
});

/* Párrafo con tramos en negrita: ['normal', ['negrita', true], …] */
const pr = (tramos, o = {}) => new Paragraph({
  spacing: { after: o.after === undefined ? 140 : o.after, line: 288 },
  children: tramos.map(t => new TextRun({
    text: Array.isArray(t) ? t[0] : t,
    bold: Array.isArray(t) ? t[1] : false,
    size: (o.size || 10.5) * 2, color: o.color || '1A1A1A', font: 'Calibri',
  })),
});

const h1 = t => new Paragraph({
  heading: HeadingLevel.HEADING_1, spacing: { before: 300, after: 180 },
  children: [new TextRun({ text: t, size: 32, bold: true, color: AZUL, font: 'Calibri' })],
});
const h2 = t => new Paragraph({
  heading: HeadingLevel.HEADING_2, spacing: { before: 240, after: 120 },
  children: [new TextRun({ text: t, size: 24, bold: true, color: AZUL, font: 'Calibri' })],
});

const vin = t => new Paragraph({
  numbering: { reference: 'puntos', level: 0 },
  spacing: { after: 90, line: 276 },
  children: [new TextRun({ text: t, size: 21, font: 'Calibri', color: '1A1A1A' })],
});

const nota = t => new Paragraph({
  spacing: { after: 160, line: 264 },
  children: [new TextRun({ text: t, size: 17, italics: true, color: GRIS, font: 'Calibri' })],
});

/* Figura con pie. El ancho se fija y el alto se deduce de la cabecera IHDR
   del PNG: adivinar la proporción deja franjas vacías a los lados. */
function tamPng(f) {
  const b = fs.readFileSync(f);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
}
function figura(archivo, pie, anchoPulg = 6.3) {
  const t = tamPng(archivo);
  const w = anchoPulg * 96, h = w * t.h / t.w;
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { before: 120, after: 60 },
      children: [new ImageRun({
        type: 'png', data: fs.readFileSync(archivo),
        transformation: { width: Math.round(w), height: Math.round(h) },
      })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { after: 220 },
      children: [new TextRun({ text: pie, size: 16, italics: true, color: GRIS, font: 'Calibri' })],
    }),
  ];
}

/* Tabla: anchos duales en DXA, sombreado CLEAR. */
function tabla(cabeceras, filas, anchos, o = {}) {
  const total = anchos.reduce((a, b) => a + b, 0);
  const celda = (txt, i, cab, alt) => new TableCell({
    width: { size: anchos[i], type: WidthType.DXA },
    shading: { type: ShadingType.CLEAR, fill: cab ? AZUL : (alt ? CREMA : 'FFFFFF'), color: 'auto' },
    margins: { top: 60, bottom: 60, left: 90, right: 90 },
    children: [new Paragraph({
      alignment: i === 0 ? AlignmentType.LEFT : AlignmentType.RIGHT,
      spacing: { after: 0 },
      children: [new TextRun({
        text: String(txt), size: (o.size || 8.5) * 2, bold: cab,
        color: cab ? 'FFFFFF' : '1A1A1A', font: 'Calibri',
      })],
    })],
  });
  return new Table({
    columnWidths: anchos,
    width: { size: total, type: WidthType.DXA },
    borders: ['top', 'bottom', 'left', 'right', 'insideHorizontal', 'insideVertical']
      .reduce((a, k) => (a[k] = { style: BorderStyle.SINGLE, size: 2, color: BORDE }, a), {}),
    rows: [
      new TableRow({
        tableHeader: true,
        children: cabeceras.map((c, i) => celda(c, i, true)),
      }),
      ...filas.map((f, j) => new TableRow({
        children: f.map((c, i) => celda(c, i, false, j % 2 === 1)),
      })),
    ],
  });
}

/* ── contenido ───────────────────────────────────────────────────────── */
const hijos = [];

/* PORTADA */
hijos.push(
  new Paragraph({ spacing: { after: 2600 }, children: [] }),
  new Paragraph({
    spacing: { after: 160 },
    children: [new TextRun({
      text: 'GOBERNACIÓN DEL VALLE DEL CAUCA  ·  OBSERVATORIO DE TURISMO',
      size: 18, bold: true, color: GRIS, characterSpacing: 40, font: 'Calibri',
    })],
  }),
  new Paragraph({
    spacing: { after: 200 },
    children: [new TextRun({
      text: 'Línea base de afectación del sector turístico y agroturístico',
      size: 52, bold: true, color: AZUL, font: 'Calibri',
    })],
  }),
  new Paragraph({
    spacing: { after: 420 },
    children: [new TextRun({
      text: `Valle del Cauca · sismo del ${AG.sismo}`,
      size: 28, color: '3A3A3A', font: 'Calibri',
    })],
  }),
  pr([['Documento de insumo', true],
      ' para la propuesta de la UCEVA y universidades aliadas a la convocatoria '
      + 'de subvenciones de ICETEX, en el marco del proyecto de innovación en '
      + 'destinos turísticos y agrícolas con enfoque de agroturismo.'], { size: 11 }),
  pr([
    [`${n(TU.n)} negocios de la cadena de valor del turismo afectados`, true],
    `  ·  ${c1(TU.pct_sev)} % en nivel crítico o grave  ·  `,
    [`${n(RNT.rural)} prestadores de alojamiento y atractivo rural`, true],
    ' inscritos en el Registro Nacional de Turismo.',
  ], { size: 10.5, color: ROJO, after: 400 }),
  nota(`Corte del censo de afectación: ${AG.corte}. Registro Nacional de Turismo: `
    + `vigencia 2026. Elaborado por el Observatorio de Turismo del Valle del Cauca. `
    + `Documento de agregados municipales: no contiene datos personales ni razones `
    + `sociales de los establecimientos reportantes.`),
  new Paragraph({ children: [new PageBreak()] }),
);

/* 1 · ALCANCE */
hijos.push(
  h1('1. Qué contiene esta línea base y qué no'),
  p('Este documento responde a tres preguntas concretas del equipo formulador: '
    + 'cuántos prestadores turísticos y agroturísticos resultaron afectados y dónde, '
    + 'de qué tipo fue la afectación y cuánto empleo quedó comprometido, y qué '
    + 'municipios están priorizados para la reactivación turística.'),

  h2('Las dos fuentes'),
  vin(`Censo de afectación empresarial de la Gobernación del Valle. `
    + `${n(AG.censo.recibidos)} reportes recibidos con corte al ${AG.corte}, de los que `
    + `quedan ${n(AG.censo.unicos)} establecimientos únicos tras retirar `
    + `${n(AG.censo.dobles)} dobles notificaciones. Es un censo por autorreporte: `
    + `recoge al negocio que diligenció el formulario, tenga o no registro formal.`),
  vin(`Registro Nacional de Turismo (RNT), vigencia 2026 para el Valle del Cauca. `
    + `${n(RNT.vigentes)} prestadores vigentes en ${RNT.municipios} municipios. Es el `
    + `registro de la oferta formal y se renueva cada año.`),

  h2('Lo que estas fuentes no permiten decir'),
  p('Conviene dejarlo escrito antes de las cifras, porque condiciona cómo se usan:'),
  vin('El censo no pregunta si el negocio es agroturístico, ni su tipo de prestador. '
    + 'Por eso no existe una cifra de «fincas agroturísticas afectadas»: lo que sí se '
    + 'puede hacer es cruzar, por municipio, dónde está la oferta rural formal y dónde '
    + 'se concentró el daño.'),
  vin('Las dos bases no comparten identificador —el RNT no trae NIT—, así que el '
    + 'emparejamiento establecimiento por establecimiento solo alcanza al 5,2 % de los '
    + 'reportes turísticos. El cruce que sostiene este documento es municipal, y cubre '
    + `${RNT.municipios} de los ${MU.length} municipios.`),
  vin('Las pérdidas y el empleo se declaran en rangos, no en cifras exactas. Por eso '
    + 'las pérdidas se reportan como cota inferior y el empleo como intervalo. Ninguna '
    + 'de las dos debe citarse como un valor puntual.'),
  vin('El censo mide quién reportó, no quién fue afectado. Un municipio con pocos '
    + 'reportes puede haber tenido poca difusión del formulario y no poco daño.'),
  nota('Tratamiento de datos. El censo contiene datos personales de los reportantes. '
    + 'Este documento se construyó únicamente con agregados municipales y no incluye '
    + 'nombre, documento, teléfono, correo, NIT, dirección, barrio ni razón social. '
    + 'La entrega de cualquier listado nominal requiere verificar la autorización de '
    + 'tratamiento en los términos de la Ley 1581 de 2012.'),
  new Paragraph({ children: [new PageBreak()] }),
);

/* 2 · RESUMEN */
const RES = [
  ['Oferta turística formal (RNT vigente 2026)', n(RNT.vigentes), 'prestadores'],
  ['De ella, alojamiento o atractivo en suelo rural', n(RNT.rural),
    `prestadores · ${c1(RNT.pct_rural)} % del registro`],
  ['Capacidad instalada de esa oferta rural', n(RNT.camas),
    `camas en ${n(RNT.habitaciones)} habitaciones`],
  ['Municipios con oferta rural inscrita', n(RNT.municipios_rural), `de ${MU.length}`],
  ['Negocios de la cadena turística afectados', n(TU.n),
    `${c1(100 * TU.n / AG.censo.unicos)} % del censo empresarial`],
  ['En nivel crítico o grave', n(TU.sev), `${c1(TU.pct_sev)} % de los turísticos`],
  ['Sin poder operar', n(TU.no_opera), `${c1(TU.pct_no_opera)} % de los que informan`],
  ['Negocios turísticos con empleo comprometido', n(TU.con_empleo),
    `${c1(TU.pct_empleo)} % de los ${n(TU.base_empl)} que responden`],
  ['Empleos comprometidos en el sector', `${n(TU.empl_lo)} – ${n(TU.empl_hi)}`,
    'intervalo; la encuesta pregunta por rangos'],
  ['Pérdidas declaradas por el sector', `$${n(TU.perd_min)} millones`,
    `cota inferior; ${TU.perd_ab} reportes sin techo declarado`],
  ['Unidades agropecuarias afectadas', n(AGRO.n),
    `${c1(AGRO.pct_sev)} % en crítico o grave`],
  ['Pérdidas declaradas por el sector agropecuario', `$${n(AGRO.perd_min)} millones`,
    'cota inferior'],
];
hijos.push(
  h1('2. Resumen de la línea base'),
  p('Las cifras de referencia del diagnóstico, en una sola tabla. Cada una se '
    + 'desarrolla en los capítulos siguientes.'),
  tabla(['Indicador', 'Valor', 'Base y lectura'],
        RES.map(r => [r[0], r[1], r[2]]), [4400, 1700, 3200]),
  nota(`Censo de afectación con corte al ${AG.corte}, depurado de doble notificación. `
    + `Registro Nacional de Turismo vigencia 2026.`),
  new Paragraph({ children: [new PageBreak()] }),
);

/* 3 · OFERTA AGROTURÍSTICA */
const topRur = [...MU].sort((a, b) => b.rnt_rural - a.rnt_rural).slice(0, 8);
const topPct = [...MU].filter(m => m.rnt_vigentes >= 10)
  .sort((a, b) => b.pct_rural - a.pct_rural).slice(0, 8);
hijos.push(
  h1('3. La oferta agroturística formal del Valle'),
  p('El RNT no tiene una categoría llamada «agroturismo». Sí tiene subcategorías que '
    + 'describen alojamiento y atractivos en suelo rural, y ese conjunto es el mejor '
    + 'proxy disponible de la base formal sobre la que un proyecto de agroturismo puede '
    + 'trabajar. Se usa aquí declarándolo como proxy.'),
  tabla(['Subcategoría del RNT', 'Prestadores', '% del proxy rural'],
        Object.entries(RNT.sub).map(([k, v]) =>
          [k.charAt(0) + k.slice(1).toLowerCase(), n(v), pct(v, RNT.rural) + ' %']),
        [5000, 2100, 2200]),
  p(''),
  pr([`Son ${n(RNT.rural)} prestadores, el ${c1(RNT.pct_rural)} % del registro turístico `,
      'del departamento, repartidos en ', [`${RNT.municipios_rural} municipios`, true],
      `. Declaran ${n(RNT.camas)} camas en ${n(RNT.habitaciones)} habitaciones. `,
      `Las fincas turísticas de alojamiento rural son `,
      [`${pct(RNT.sub['FINCAS TURÍSTICAS (ALOJAMIENTO RURAL)'], RNT.rural)} % `, true],
      'de ese universo: el agroturismo del Valle es, ante todo, alojamiento en finca.']),

  ...figura('ag1_oferta_rural.png',
    'Figura 1. Prestadores de alojamiento y atractivo rural con RNT vigente 2026, por municipio. '
    + 'Geometría: Marco Geoestadístico Nacional (DANE).', 5.5),

  h2('Dónde se concentra'),
  tabla(['Municipio', 'Prestadores rurales', '% de su oferta formal', 'Camas'],
        topRur.map(m => [nm(m.municipio), n(m.rnt_rural),
                         m.pct_rural === null ? '—' : c1(m.pct_rural) + ' %',
                         n(m.camas_rural)]),
        [3600, 2000, 2200, 1500]),
  p(''),
  p('El conteo absoluto premia a los municipios grandes. Para un proyecto de '
    + 'agroturismo importa igual o más qué proporción de la oferta formal de cada '
    + 'municipio es rural, porque eso describe la vocación del territorio:'),
  tabla(['Municipio', '% rural de su oferta', 'Rurales', 'Total RNT'],
        topPct.map(m => [nm(m.municipio), c1(m.pct_rural) + ' %',
                         n(m.rnt_rural), n(m.rnt_vigentes)]),
        [3600, 2200, 1700, 1800]),
  nota('Solo municipios con 10 o más prestadores inscritos: por debajo de ese umbral '
    + 'el porcentaje describe a dos o tres establecimientos y no al territorio.'),
  new Paragraph({ children: [new PageBreak()] }),
);

/* 4 · AFECTACIÓN DEL TURISMO */
const D = PT.dano, BD = PT.base_dano;
const INF = 'Infraestructura, maquinaria o equipos';
const INV = 'Inventarios o mercancías';
const VEN = 'Reducción de clientes, pedidos o ventas';
const PRO = 'Proveedores, logística o servicios públicos';
hijos.push(
  h1('4. Afectación de la cadena de valor del turismo'),
  p(`La cadena de valor del turismo se define, en el censo, como los sectores `
    + `«Alojamiento y servicios de comida» y «Transporte y almacenamiento»: `
    + `${n(TU.n)} establecimientos, el ${c1(100 * TU.n / AG.censo.unicos)} % de todo `
    + `el censo empresarial del departamento.`),

  h2('Tipo de afectación'),
  tabla(['Qué se dañó', 'Establecimientos', '% de los que informan'],
        [[INF, n(D[INF]), pct(D[INF], BD) + ' %'],
         [VEN, n(D[VEN]), pct(D[VEN], BD) + ' %'],
         [INV, n(D[INV]), pct(D[INV], BD) + ' %'],
         [PRO, n(D[PRO]), pct(D[PRO], BD) + ' %']],
        [5200, 2000, 2100]),
  p(''),
  pr(['El daño del sector es ', ['físico antes que comercial', true],
      `: ${pct(D[INF], BD)} % reporta daño en infraestructura, maquinaria o equipos, `
      + `por encima del ${pct(PF.todos.dano[INF], PF.todos.base_dano)} % del conjunto de `
      + 'la economía. Un hotel, una finca turística o un restaurante no vive de la '
      + 'mercancía en bodega sino del inmueble y de la dotación, y eso define qué tipo '
      + 'de alivio sirve.'], { after: 60 }),
  nota('Selección múltiple: los porcentajes no suman 100. Base: '
    + `${n(BD)} establecimientos turísticos que respondieron la pregunta.`),

  h2('Continuidad del negocio'),
  tabla(['Estado de operación', 'Establecimientos', '% de los que informan'],
        [['Opera normalmente', n(PT.normal), c1(PT.pct_normal) + ' %'],
         ['Opera parcialmente', n(PT.parcial), c1(PT.pct_parcial) + ' %'],
         ['No puede operar', n(PT.no_opera), c1(PT.pct_no_opera) + ' %']],
        [5200, 2000, 2100]),
  p(''),
  pr([[`${c1(PT.pct_restriccion)} % de la cadena turística no ha recuperado su operación normal. `, true],
      `El cierre total pesa ${c1(PT.pct_no_opera - PF.todos.pct_no_opera)} puntos más que `
      + `en el conjunto de la economía (${c1(PT.pct_no_opera)} % frente a `
      + `${c1(PF.todos.pct_no_opera)} %). El cuello de botella del sector no es vender: `
      + 'es volver a abrir.']),

  h2('Empleo comprometido'),
  pr([`De los ${n(TU.base_empl)} negocios turísticos que responden la pregunta de empleo, `,
      [`${n(TU.con_empleo)} declaran al menos un puesto afectado o en riesgo`, true],
      ` (${c1(TU.pct_empleo)} % de esa base, ${c1(100 * TU.con_empleo / TU.n)} % del total `
      + `de ${n(TU.n)} afectados). Sumando los rangos declarados, el empleo comprometido `
      + `está entre ${n(TU.empl_lo)} y ${n(TU.empl_hi)} puestos.`]),
  pr(['El empleo está ', ['pulverizado', true],
      `: ${pct(PT.tam.Microempresa, PT.n)} % de los establecimientos turísticos `
      + `afectados son microempresas. Son muchísimas unidades con pocos empleos cada una, `
      + 'no unas pocas empresas grandes, y eso determina el número de operaciones de un '
      + 'programa de reactivación más que su monto total.']),

  h2('Qué tipo de negocio turístico resultó afectado'),
  p('El formulario no pregunta el tipo de prestador. El tipo se deduce de palabras del '
    + `nombre comercial, lo que permite tipificar ${n(PF.base_tipo)} de los `
    + `${n(TU.n)} establecimientos. La distribución es orientativa, no censal:`),
  tabla(['Tipo de negocio', 'Establecimientos', '% de lo tipificable', '% crítico o grave'],
        PF.tipificables.map(t => [t.tipo, n(t.n), c1(t.pct_tipificables) + ' %',
                                  c1(t.pct_sev) + ' %']),
        [4000, 1800, 1800, 1700]),
  nota(`${n(PF.sin_tipificar['Sin clasificar'])} nombres no traen ninguna palabra `
    + `reconocible y ${n(PF.sin_tipificar['Registrado a nombre de persona natural'])} están `
    + 'registrados a nombre de una persona natural; quedan fuera de la tabla. '
    + 'Incorporar el tipo de prestador al formulario cerraría este vacío para futuras '
    + 'mediciones.'),
  new Paragraph({ children: [new PageBreak()] }),
);

/* 5 · AGRO */
const topAgro = [...MU].filter(m => m.agro_n > 0)
  .sort((a, b) => b.agro_n - a.agro_n).slice(0, 10);
hijos.push(
  h1('5. Afectación del sector agropecuario'),
  pr([`El censo registra `, [`${n(AGRO.n)} unidades del sector `, true],
      '«Agricultura, ganadería, caza, silvicultura y pesca» con reporte de daño. Es un '
      + 'universo pequeño frente al turístico, pero relevante para el proyecto porque es '
      + 'el otro lado de la cadena agroturística.']),
  tabla(['Indicador del sector agropecuario', 'Valor', 'Base'],
        [['Unidades con reporte de daño', n(AGRO.n), 'censo empresarial'],
         ['En nivel crítico o grave', n(AGRO.sev), c1(AGRO.pct_sev) + ' % de las ' + n(AGRO.n)],
         ['Sin poder operar', n(AGRO.no_opera),
          c1(AGRO.pct_no_opera) + ' % de ' + n(AGRO.base_cont) + ' que informan'],
         ['Con empleo comprometido', n(AGRO.con_empleo),
          c1(AGRO.pct_empleo) + ' % de ' + n(AGRO.base_empl) + ' que responden'],
         ['Empleos comprometidos', n(AGRO.empl_lo) + ' – ' + n(AGRO.empl_hi), 'intervalo'],
         ['Pérdidas declaradas', '$' + n(AGRO.perd_min) + ' millones', 'cota inferior']],
        [4600, 2300, 2400]),
  p(''),
  p('Por municipio, la afectación agropecuaria se concentra donde también hay daño '
    + 'turístico, lo que refuerza la pertinencia de una intervención integrada:'),
  tabla(['Municipio', 'Agropecuarias afectadas', 'En crítico o grave', 'Negocios turísticos afectados'],
        topAgro.map(m => [nm(m.municipio), n(m.agro_n), n(m.agro_sev), n(m.tur_n)]),
        [3200, 2200, 1900, 2000]),
  nota('El censo empresarial recoge unidades productivas que diligenciaron el formulario, '
    + 'no predios. No sustituye un censo agropecuario y debe leerse como indicio de dónde '
    + 'mirar, no como medición del daño al campo.'),
  new Paragraph({ children: [new PageBreak()] }),
);

/* 6 · PRIORIZACIÓN */
const PRIO = AG.priorizados_gobernacion;
const dmu = Object.fromEntries(MU.map(m => [m.municipio, m]));
const top12 = MU.slice(0, 12);
// «Rezagado» en vocación rural, no en daño: puesto bajo del índice pese a
// estar priorizado. El umbral se fija en el puesto 20 para no llamar así a
// municipios que quedan a media tabla.
const REZAGO = PRIO.filter(k => dmu[k].rank > 20);
hijos.push(
  h1('6. Municipios priorizados para la reactivación turística'),
  h2('Los seis priorizados por la Gobernación'),
  p('La Gobernación ya definió seis municipios para la reactivación del sector '
    + 'turístico. Esta es su situación según la línea base:'),
  tabla(['Municipio', 'Negocios turísticos afectados', '% crítico o grave',
         'Empleo comprometido', 'Pérdidas (cota inferior)', 'Prestadores rurales'],
        PRIO.map(k => {
          const m = dmu[k];
          return [nm(k), n(m.tur_n), c1(m.tur_pct_sev) + ' %',
                  `${n(m.tur_empl_lo)} – ${n(m.tur_empl_hi)}`,
                  '$' + n(m.tur_perd_min) + ' M', n(m.rnt_rural)];
        }),
        [2200, 1900, 1500, 1800, 1700, 1700], { size: 8 }),
  p(''),

  h2('Un criterio adicional para el enfoque agroturístico'),
  p('Esos seis se priorizaron por daño turístico. Un proyecto de agroturismo necesita '
    + 'además que haya base rural sobre la cual trabajar, así que la línea base propone '
    + 'un índice explícito y reproducible con tres componentes de igual peso:'),
  vin('Vocación rural: prestadores de alojamiento o atractivo rural con RNT vigente.'),
  vin('Daño declarado: negocios de la cadena turística que reportaron afectación.'),
  vin('Severidad: porcentaje de esos negocios en nivel crítico o grave, contabilizado '
    + `solo cuando el municipio tiene al menos ${AG.min_reportes_sev} reportes.`),
  p('Cada componente se lleva a una escala de 0 a 100 dividiendo por el máximo '
    + 'departamental, para que ninguno domine por su unidad de medida. Los pesos son '
    + 'discutibles y por eso quedan escritos: con otros pesos el orden cambia, y el '
    + 'archivo de datos que acompaña este documento permite recalcularlo.'),

  ...figura('ag4_indice.png',
    'Figura 2. Índice de priorización agroturística, abierto en sus tres componentes. '
    + 'Los quince primeros municipios.'),

  tabla(['#', 'Municipio', 'Índice', 'Prestadores rurales', 'Turísticos afectados', '% crít. o grave'],
        top12.map(m => [String(m.rank), nm(m.municipio), c1(m.indice), n(m.rnt_rural),
                        n(m.tur_n), m.tur_pct_sev === null ? '—' : c1(m.tur_pct_sev) + ' %']),
        [700, 2800, 1300, 1900, 1900, 1700], { size: 8.5 }),
  p(''),

  ...figura('ag3_cuadrantes.png',
    'Figura 3. Vocación agroturística frente a daño turístico declarado. El tamaño del '
    + 'punto es proporcional a las pérdidas declaradas. Cali queda fuera de la escala y '
    + 'se indica en la nota de la figura.'),

  h2('Lectura'),
  pr([['El cuadrante que interesa al proyecto es el superior derecho', true],
      ': municipios donde hay oferta rural formal sobre la cual construir y donde el '
      + 'daño declarado justifica intervenir. Allí aparecen '
      + `${nm('CALIMA')}, ${nm('DAGUA')}, ${nm('ALCALA')}, ${nm('SEVILLA')}, `
      + `${nm('BUENAVENTURA')} y ${nm('YUMBO')}.`]),
  pr([`De los seis priorizados por la Gobernación, `,
      [`${lista(PRIO.filter(k => dmu[k].rank <= 10).map(nm))} quedan también entre los diez primeros`, true],
      ' de este índice. En cambio ',
      lista(REZAGO.map(k => `${nm(k)}, en el puesto ${dmu[k].rank}`)),
      ` ${REZAGO.length > 1 ? 'tienen' : 'tiene'} daño turístico alto con muy poca oferta `
      + `rural inscrita (${lista(REZAGO.map(k => `${dmu[k].rnt_rural} prestadores en ${nm(k)}`))}). `
      + 'Eso no los excluye del proyecto, pero sugiere que allí el componente '
      + 'agroturístico sea de creación de oferta y no de recuperación de la existente.']),
  pr([[`${nm('ULLOA')}, ${nm('RIOFRIO')} y ${nm('TRUJILLO')} merecen atención aparte`, true],
      `: son los municipios cuya oferta formal es más rural del departamento `
      + `(${c1(dmu['ULLOA'].pct_rural)} %, ${c1(dmu['RIOFRIO'].pct_rural)} % y `
      + `${c1(dmu['TRUJILLO'].pct_rural)} % respectivamente), con daño declarado moderado. `
      + 'Son candidatos naturales para el componente de innovación en destino, más que '
      + 'para el de reparación.']),
  new Paragraph({ children: [new PageBreak()] }),
);

/* 7 · QUÉ FALTA */
hijos.push(
  h1('7. Qué le falta a esta línea base'),
  p('El diagnóstico del proyecto puede apoyarse en lo anterior, pero conviene que el '
    + 'levantamiento propio cubra los vacíos que las fuentes oficiales no resuelven. '
    + 'Cinco, en orden de importancia para un proyecto de agroturismo:'),
  vin('Identificación del prestador agroturístico. Ni el censo ni el RNT permiten '
    + 'separar la finca que hace agroturismo de la vivienda turística rural que solo '
    + 'arrienda. Un instrumento propio que pregunte por actividad agropecuaria asociada '
    + 'al servicio turístico resolvería la pregunta central del proyecto.'),
  vin('Código RNT en el reporte de afectación. Hoy las dos bases solo se pueden comparar '
    + 'por municipio. Un campo de RNT en el formulario permitiría medir la afectación del '
    + 'registro establecimiento por establecimiento.'),
  vin('Daño en el activo productivo agrícola. El censo empresarial mide la unidad de '
    + 'negocio, no el cultivo, el suelo ni la infraestructura de riego. El proyecto '
    + 'necesita ese dato para el componente agrícola.'),
  vin('Cobertura del sur del departamento. Florida, Candelaria y Pradera suman '
    + `${n(mu('FLORIDA').tur_n + mu('CANDELARIA').tur_n + mu('PRADERA').tur_n)} reportes `
    + 'turísticos entre los tres. Antes de concluir que no hubo daño hay que verificar '
    + 'cómo se difundió el formulario.'),
  vin('Línea base de demanda. Todo lo anterior describe la oferta y su daño. No hay '
    + 'medición de visitantes, ocupación ni gasto antes y después del sismo, que es lo '
    + 'que permitiría evaluar la recuperación del destino.'),

  h1('8. Fuentes y trazabilidad'),
  vin(`Censo de afectación empresarial, Gobernación del Valle del Cauca. Corte `
    + `${AG.corte}. ${n(AG.censo.recibidos)} reportes recibidos, `
    + `${n(AG.censo.unicos)} establecimientos únicos tras depurar `
    + `${n(AG.censo.dobles)} dobles notificaciones mediante identificadores fuertes.`),
  vin(`Registro Nacional de Turismo, Valle del Cauca, vigencia 2026. `
    + `${n(RNT.vigentes)} prestadores vigentes.`),
  vin('Informe de la Secretaría de Desarrollo Económico, Competitividad y Fomento del '
    + 'Empleo presentado al Consejo de Gobierno del 15 de septiembre de 2026. Los '
    + 'indicadores departamentales de este documento reproducen los de ese informe con '
    + 'diferencias menores a un punto porcentual en severidad y continuidad operativa.'),
  vin('Geometría municipal: Marco Geoestadístico Nacional, DANE.'),
  p(''),
  nota('Todas las cifras de este documento se generan desde los scripts del Observatorio '
    + 'de Turismo (agroturismo.py, perfil_turismo.py, cruce_rnt_0903.py) y el archivo '
    + 'agroturismo_municipal.csv acompaña al documento con la tabla municipal completa '
    + 'de los 42 municipios, para que el equipo formulador pueda recalcular el índice '
    + 'con otros pesos o filtrar por otros criterios.'),
);

/* ── documento ───────────────────────────────────────────────────────── */
const doc = new Document({
  creator: 'Observatorio de Turismo · Gobernación del Valle del Cauca',
  title: 'Línea base de afectación del sector turístico y agroturístico',
  description: 'Insumo para la convocatoria de subvenciones de ICETEX',
  numbering: {
    config: [{
      reference: 'puntos',
      levels: [{
        level: 0, format: 'bullet', text: '–', alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 360, hanging: 200 } } },
      }],
    }],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },     // Carta
        margin: { top: 1080, bottom: 1080, left: 1180, right: 1180 },
      },
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          children: [new TextRun({
            children: ['Observatorio de Turismo · Valle del Cauca    ', PageNumber.CURRENT],
            size: 16, color: GRIS, font: 'Calibri',
          })],
        })],
      }),
    },
    children: hijos,
  }],
});

Packer.toBuffer(doc).then(b => {
  const f = 'Linea_base_agroturismo_ICETEX_2026-10-19.docx';
  fs.writeFileSync(f, b);
  console.log('generado:', f, (b.length / 1024).toFixed(0) + ' KB');
});

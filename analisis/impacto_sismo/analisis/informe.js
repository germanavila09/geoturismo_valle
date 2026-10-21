const fs = require('fs');
const d = require('docx');
const {Document,Packer,Paragraph,TextRun,HeadingLevel,Table,TableRow,TableCell,
       WidthType,ShadingType,AlignmentType,BorderStyle,ImageRun,PageBreak,
       LevelFormat,convertInchesToTwip,TableOfContents} = d;
const D = JSON.parse(fs.readFileSync('datos.json','utf8'));

const AZUL="1F3864", ROJO="B3261E", GRIS="595959", CLARO="F2F5FA", BORDE="D5DBE5";
const n = x => (x===null||x===undefined) ? "—" : x.toLocaleString('es-CO');
const pct = x => x.toFixed(1).replace('.',',') + " %";

const titulo = t => String(t).toLowerCase()
  .replace(/(^|[\s(])(\w)/g, (m,a,b)=>a+b.toUpperCase())
  .replace(/\bDe\b/g,'de').replace(/\bEl\b(?!\s*$)/g,(m,o)=>o===0?'El':'el');
const P = (t,o={}) => new Paragraph({
  spacing:{after:o.after??140, line:300}, alignment:o.al,
  children:[new TextRun({text:t, size:o.size??20, bold:o.b, italics:o.i,
                         color:o.c??"1A1A1A", font:"Calibri"})]});
const Rich = (runs,o={}) => new Paragraph({
  spacing:{after:o.after??140, line:300}, alignment:o.al,
  children:runs.map(r => new TextRun({text:r[0], bold:r[1]==='b', italics:r[1]==='i',
                                      size:o.size??20, color:o.c??"1A1A1A", font:"Calibri"}))});
const H1 = t => new Paragraph({heading:HeadingLevel.HEADING_1, spacing:{before:340,after:150}, keepNext:true, keepLines:true,
  children:[new TextRun({text:t,size:28,bold:true,color:AZUL,font:"Calibri"})]});
const H2 = t => new Paragraph({heading:HeadingLevel.HEADING_2, spacing:{before:250,after:110}, keepNext:true, keepLines:true,
  children:[new TextRun({text:t,size:23,bold:true,color:AZUL,font:"Calibri"})]});
const Bul = t => new Paragraph({numbering:{reference:"vinetas",level:0},
  spacing:{after:80,line:290},
  children:[new TextRun({text:t,size:20,font:"Calibri",color:"1A1A1A"})]});
const Fuente = t => new Paragraph({spacing:{after:200},
  children:[new TextRun({text:t,size:16,italics:true,color:GRIS,font:"Calibri"})]});
const Cap = t => new Paragraph({spacing:{before:60,after:180},
  children:[new TextRun({text:t,size:17,bold:true,color:GRIS,font:"Calibri"})]});

const celda = (t,{b,al,w,sh,c,sz}={}) => new TableCell({
  width:{size:w,type:WidthType.DXA},
  shading:sh?{type:ShadingType.CLEAR,fill:sh,color:"auto"}:undefined,
  margins:{top:70,bottom:70,left:110,right:110},
  children:[new Paragraph({alignment:al??AlignmentType.LEFT,spacing:{after:0},
    children:[new TextRun({text:String(t),size:sz??17,bold:b,color:c??"1A1A1A",font:"Calibri"})]})]});

function tabla(cab, filas, anchos, opts={}){
  const bordes = {
    top:{style:BorderStyle.SINGLE,size:2,color:BORDE},
    bottom:{style:BorderStyle.SINGLE,size:2,color:BORDE},
    left:{style:BorderStyle.NONE},right:{style:BorderStyle.NONE},
    insideHorizontal:{style:BorderStyle.SINGLE,size:1,color:"E8ECF2"},
    insideVertical:{style:BorderStyle.NONE}};
  // Alineacion: la primera columna (y la ultima, si es texto) van a la
  // izquierda; las numericas a la derecha, que es como se leen las cifras.
  const der = (i, ncol) => i >= (opts.numDesde ?? 1)
    && !(opts.textoFinal && i === ncol - 1);
  const filaCab = new TableRow({tableHeader:true, children:cab.map((t,i)=>
    celda(t,{b:true,sh:AZUL,c:"FFFFFF",w:anchos[i],
             al:der(i,cab.length)?AlignmentType.RIGHT:AlignmentType.LEFT}))});
  const cuerpo = filas.map((f,j)=> new TableRow({children:f.map((t,i)=>
    celda(t,{w:anchos[i], sh:j%2?CLARO:undefined,
             al:der(i,f.length)?AlignmentType.RIGHT:AlignmentType.LEFT}))}));
  return new Table({columnWidths:anchos, width:{size:anchos.reduce((a,b)=>a+b,0),type:WidthType.DXA},
                    borders:bordes, rows:[filaCab,...cuerpo]});
}

function tablaFicha(filas, anchos){
  const bordes = {
    top:{style:BorderStyle.SINGLE,size:2,color:BORDE},
    bottom:{style:BorderStyle.SINGLE,size:2,color:BORDE},
    left:{style:BorderStyle.NONE},right:{style:BorderStyle.NONE},
    insideHorizontal:{style:BorderStyle.SINGLE,size:1,color:"E8ECF2"},
    insideVertical:{style:BorderStyle.NONE}};
  return new Table({columnWidths:anchos,
    width:{size:anchos.reduce((a,b)=>a+b,0),type:WidthType.DXA}, borders:bordes,
    rows:filas.map((f,j)=> new TableRow({children:[
      celda(f[0],{w:anchos[0],b:true,c:GRIS,sh:j%2?CLARO:undefined}),
      celda(f[1],{w:anchos[1],sh:j%2?CLARO:undefined})]}))});
}

function caja(titulo, texto, color=AZUL){
  return new Table({columnWidths:[9360], width:{size:9360,type:WidthType.DXA},
    borders:{top:{style:BorderStyle.NONE},bottom:{style:BorderStyle.NONE},
             left:{style:BorderStyle.SINGLE,size:18,color:color},
             right:{style:BorderStyle.NONE},
             insideHorizontal:{style:BorderStyle.NONE},insideVertical:{style:BorderStyle.NONE}},
    rows:[new TableRow({children:[new TableCell({
      width:{size:9360,type:WidthType.DXA},
      shading:{type:ShadingType.CLEAR,fill:CLARO,color:"auto"},
      margins:{top:160,bottom:160,left:220,right:180},
      children:[
        new Paragraph({spacing:{after:70},children:[new TextRun({text:titulo,bold:true,size:20,color:color,font:"Calibri"})]}),
        ...texto.map(t=> new Paragraph({spacing:{after:60,line:290},
          children:[new TextRun({text:t,size:19,color:"1A1A1A",font:"Calibri"})]}))]})]})]});
}
const img = (f,w,h) => new Paragraph({alignment:AlignmentType.CENTER,spacing:{before:120,after:60}, keepNext:true,
  children:[new ImageRun({type:"png",data:fs.readFileSync(f),transformation:{width:w,height:h}})]});
const esp = (a=120) => new Paragraph({spacing:{after:a},children:[]});

// ───────────────────────────────────────────────────────── contenido
const pri = D.pri, cru = D.cruce;
const top = pri.slice(0,12);
const sev = D.sev;
const K = k => sev[k]||0;

const body = [];
// PORTADA
body.push(new Paragraph({spacing:{after:60},children:[new TextRun({
  text:"OBSERVATORIO DE TURISMO · VALLE DEL CAUCA",size:17,bold:true,color:GRIS,
  font:"Calibri",characterSpacing:24})]}));
body.push(new Paragraph({spacing:{after:80},children:[new TextRun({
  text:"Sector turismo: afectación empresarial y priorización municipal",
  size:42,bold:true,color:AZUL,font:"Calibri"})]}));
body.push(new Paragraph({spacing:{after:260},border:{bottom:{style:BorderStyle.SINGLE,size:12,color:ROJO}},
  children:[new TextRun({text:"Terremoto del 10 de agosto de 2026 · análisis de "+n(D.n_reportes)+" reportes empresariales",
  size:24,color:GRIS,font:"Calibri"})]}));
body.push(tablaFicha([
  ["Corte de información","1 de septiembre de 2026"],
  ["Base analizada","reportes_emergencia_2026-09-01.xlsx · hojas «Reportes» y «Diccionario»"],
  ["Informe que actualiza","Informe de priorización del 26 de agosto de 2026"],
  ["Cobertura","Valle del Cauca · 42 municipios · información agregada, sin datos personales"],
  ["Cartografía y contraste","Observatorio GeoRiesgo · balance oficial de la Secretaría de Gestión del Riesgo"],
],[2200,7160]));
body.push(esp(280));

body.push(caja("Resultado central",[
  "Con el corte del 1 de septiembre, "+n(D.cg)+" establecimientos turísticos de "+n(D.tur_est)+" ("+pct(D.pct_cg)+") están en condición crítica o grave. Son "+n(D.cg-448)+" más que en el corte del 26 de agosto.",
  "La primera ola de atención debe concentrarse en Cali, Buenaventura, Roldanillo, Sevilla y Caicedonia. Cali aporta el mayor volumen absoluto; los otros cuatro combinan alta proporción severa con afectación oficial alta o muy alta.",
  "Antes de asignar recursos hay que resolver dos problemas de la base: 1.576 reportes contienen datos personales sin consentimiento expreso, y 195 establecimientos turísticos siguen sin severidad clasificada."],ROJO));
body.push(esp(200));

// 1 RESUMEN
body.push(H1("1. Resumen ejecutivo"));
body.push(P("Este informe actualiza el análisis del 26 de agosto con la base cerrada el 1 de septiembre de 2026. La base creció de 9.169 a "+n(D.n_reportes)+" reportes (+57 %) y el universo turístico identificado pasó de 784 a "+n(D.tur_est)+" establecimientos, distribuidos ahora en los "+D.tur_mun+" municipios del departamento —cinco más que en el corte anterior."));
body.push(P("El crecimiento no es solo de volumen: la proporción de establecimientos en condición severa subió de 57,1 % a "+pct(D.pct_cg)+". Los reportes que siguieron llegando después del 26 de agosto describen, en promedio, situaciones peores que los primeros."));

body.push(H2("Hallazgos que orientan la intervención"));
body.push(Bul(n(D.cg)+" establecimientos en condición crítica o grave: "+n(K("Crítica"))+" críticos y "+n(K("Grave"))+" graves."));
body.push(Bul("De los "+n(D.cont.base)+" que informan continuidad ("+D.cont.pct_base+" % del universo), "+n(D.cont.c["No puede operar"])+" no pueden operar y "+n(D.cont.c["Sí, pero parcialmente"])+" operan parcialmente: tres de cada cuatro tienen la operación comprometida."));
body.push(Bul("De los "+n(D.empleo.base)+" que informan empleo, "+n(D.empleo.con)+" ("+pct(100*D.empleo.con/D.empleo.base)+") reportan al menos un empleo en riesgo. La exposición está entre "+n(D.empleo.lo)+" y "+n(D.empleo.hi)+" puestos de trabajo."));
body.push(Bul("Las pérdidas declaradas suman al menos $"+n(D.econ.minimo)+" millones, y esa cifra es un piso: "+n(D.econ.abierto)+" establecimientos declaran «más de $100 millones» sin techo."));
body.push(Bul("La necesidad más frecuente es reparar instalaciones o equipos ("+n(D.nec["Reparar instalaciones, maquinaria o equipos"])+"), seguida de capital de trabajo ("+n(D.nec["Capital de trabajo, inventarios o insumos"])+")."));
body.push(Bul("Los alojamientos identificables por su razón social son "+D.hot.n+", repartidos en "+D.hot.mun+" municipios; "+D.hot.cg+" están en nivel crítico o grave ("+pct(D.hot.pct)+"), casi nueve puntos por encima del promedio del sector."));
body.push(Bul(pct(D.conc.cali_pct)+" del universo turístico está en Cali y "+pct(D.conc.top5)+" en los cinco primeros municipios. La concentración exige leer con cuidado los municipios pequeños."));
body.push(esp(80));

body.push(caja("Decisión sugerida",[
  "Primera ola: Cali, Buenaventura, Roldanillo, Sevilla y Caicedonia. Los cinco superan 80 puntos de prioridad y tienen afectación oficial alta o muy alta.",
  "Segunda ola: Calima (El Darién), Yumbo, Argelia, Alcalá y La Unión.",
  "En paralelo y antes de desembolsar: completar la severidad de los 195 establecimientos sin clasificar, verificar los municipios con posible subregistro (Bolívar, Toro, Dagua, Restrepo) y sanear el consentimiento de datos personales."]));


// 2 QUE CAMBIO
body.push(H1("2. Qué cambió frente al corte del 26 de agosto"));
body.push(P("La comparación entre cortes permite distinguir el crecimiento del registro del empeoramiento real de las condiciones. Ambos ocurren."));
body.push(tabla(["Indicador","26 de agosto","1 de septiembre","Variación"],[
  ["Reportes en la base","9.169",n(D.n_reportes),"+57 %"],
  ["Establecimientos turísticos","784",n(D.tur_est),"+127 %"],
  ["Municipios con registro","37",String(D.tur_mun),"+5"],
  ["Críticos o graves","448",n(D.cg),"+146 %"],
  ["Proporción severa","57,1 %",pct(D.pct_cg),"+4,7 pp"],
],[3000,2100,2130,2130]));
body.push(Fuente("Las cifras del 26 de agosto provienen del informe previo. La comparación de «establecimientos» debe leerse con cautela: los dos cortes aplicaron reglas de deduplicación con rendimientos muy distintos —146 fusiones entonces frente a "+D.fusionados+" ahora sobre una base mayor—, lo que sugiere que el archivo anterior tenía más registros repetidos o una regla más agresiva."));
body.push(P("El aumento de la proporción severa en 4,7 puntos porcentuales es el dato relevante para la operación. Si los reportes nuevos fueran una muestra equivalente a la inicial, esa proporción se habría mantenido estable. Que suba indica que el registro está alcanzando ahora a establecimientos que en las primeras dos semanas no reportaron, y que esos establecimientos están peor."));
body.push(esp(60));
body.push(caja("Interpretación con cautela",[
  "También es posible que la plataforma haya cambiado el modo de calcular el nivel de afectación entre cortes, o que la difusión posterior haya llegado a públicos distintos. El informe no puede distinguir entre esas explicaciones con los datos disponibles; se recomienda confirmar con el administrador de la plataforma si la fórmula del campo «Nivel de afectación» se mantuvo constante."]));

// 3 ALCANCE
body.push(H1("3. Alcance, unidad de análisis y depuración"));
body.push(P("La base contiene "+n(D.n_reportes)+" reportes de todos los sectores en los 42 municipios del Valle del Cauca. Tras consolidar los registros que corresponden al mismo establecimiento quedan "+n(D.n_est)+" unidades: se fusionaron "+D.fusionados+" reportes duplicados."));
body.push(H2("Regla de deduplicación aplicada"));
body.push(P("Se identifica el establecimiento por NIT cuando existe; cuando no, por la combinación de nombre normalizado y municipio. Al fusionar se conserva el registro con la severidad más alta, criterio conservador: entre dos reportes del mismo negocio, se asume el peor estado declarado."));
body.push(esp(60));
body.push(caja("Definición operativa de turismo",[
  "Se conserva la clasificación de la fuente: «Alojamiento y servicios de comida» más «Transporte y almacenamiento». Es la misma definición del informe del 26 de agosto, para que los dos cortes sean comparables.",
  "La definición es amplia y el informe no puede estrecharla: la actividad económica registrada no distingue un hotel de una fonda de barrio, ni un transportador turístico de uno de carga. Las cifras representan establecimientos clasificados por la fuente, no prestadores turísticos certificados ante el Registro Nacional de Turismo."]));
body.push(esp(120));
body.push(tabla(["Componente","Establecimientos","Críticos/graves","% severo"],[
  ["Alojamiento y servicios de comida",n(D.comp["Alojamiento y servicios de comida"].n),n(D.comp["Alojamiento y servicios de comida"].cg),pct(100*D.comp["Alojamiento y servicios de comida"].cg/D.comp["Alojamiento y servicios de comida"].n)],
  ["Transporte y almacenamiento",n(D.comp["Transporte y almacenamiento"].n),n(D.comp["Transporte y almacenamiento"].cg),pct(100*D.comp["Transporte y almacenamiento"].cg/D.comp["Transporte y almacenamiento"].n)],
  ["Alojamientos identificados por razón social*",n(D.hot.n),n(D.hot.cg),pct(D.hot.pct)],
  ["Total sector turismo",n(D.tur_est),n(D.cg),pct(D.pct_cg)],
],[3400,2000,1980,1980]));
body.push(Fuente("*Subconjunto de «alojamiento y comidas» identificado por palabras clave en la razón social —hotel, hostal, hospedaje, posada, cabaña, glamping— con coincidencia de palabra completa, para no capturar nombres como «Copacabana». No se suma al total: ya está contenido en la primera fila."));

body.push(H2("Trazabilidad y protección de datos"));
body.push(P("El archivo contiene nombres, documentos de identidad, teléfonos, correos, NIT y direcciones. Este informe utiliza exclusivamente agregados municipales y sectoriales; ningún dato personal se reproduce, ni siquiera de forma parcial. La base debe custodiarse conforme a la Ley 1581 de 2012."));


// 4 CALIDAD
body.push(H1("4. Calidad de la base: lo que hay que corregir antes de decidir"));
body.push(P("La revisión detectó cuatro problemas que afectan la interpretación de las cifras. Ninguno invalida el análisis, pero dos exigen acción antes de asignar recursos y uno tiene implicaciones legales."));

body.push(H2("4.1 Datos personales sin consentimiento expreso"));
body.push(Rich([["Es el hallazgo más urgente y no es estadístico, es legal. ","b"],
  [n(D.cal.sin_cons)+" reportes marcaron explícitamente «No» en la autorización de datos personales, y los "+n(D.cal.sin_cons)+" conservan nombre completo y teléfono. Otros "+n(D.cal.sin_resp)+" dejaron la casilla vacía y "+"el 99 % de ellos también trae nombre y teléfono. En conjunto son "+n(D.cal.sin_cons+D.cal.sin_resp)+" registros —el "+pct(100*(D.cal.sin_cons+D.cal.sin_resp)/D.n_reportes)+" de la base— con datos identificables cuyo tratamiento no está amparado por una autorización verificable.",""]]));
body.push(P("La Ley 1581 de 2012 exige autorización previa, expresa e informada del titular. Se recomienda: segregar esos registros del uso operativo, conservarlos únicamente para fines estadísticos anonimizados, y consultar con la oficina jurídica si procede una campaña de saneamiento del consentimiento antes de cualquier contacto comercial o de convocatoria."));

body.push(H2("4.2 Fechas con día y mes invertidos"));
body.push(P(n(D.cal.fechas_mal)+" reportes traen fechas imposibles —8 de noviembre y 8 de diciembre de 2026— posteriores al corte del archivo. Leídas en formato día/mes corresponden al 11 y 12 de agosto, los dos días siguientes al sismo. Corregidas, la curva de llegada de reportes se vuelve coherente: un pico inmediato tras el terremoto."));
body.push(img("fig5_serie.png",600,215));
body.push(Cap("Figura 1. Llegada de reportes por día, con las fechas corregidas destacadas."));
body.push(Fuente("Solo el "+D.cal.fecha+" % de los reportes trae fecha, de modo que la serie describe una fracción de la base y no debe leerse como el volumen real por día."));

body.push(H2("4.3 Campos incompletos y su efecto en los porcentajes"));
body.push(P("Varias columnas tienen vacíos altos. Todos los porcentajes de este informe se calculan sobre quienes respondieron cada pregunta, y cada tabla declara su base; ignorar esto llevaría a subestimar sistemáticamente los fenómenos medidos."));
body.push(tabla(["Campo","Diligenciado","Efecto sobre el análisis"],[
  ["Fecha de reporte",D.cal.fecha+" %","No permite series temporales confiables"],
  ["Documento de identificación",D.cal.doc+" %","Limita el cruce con registros externos"],
  ["Barrio",D.cal.barrio+" %","Impide desagregar por comuna dentro de Cali"],
  ["Continuidad operativa",D.cont.pct_base+" %","Base de los indicadores de operación"],
  ["Empleos en riesgo",D.emp.pct_base+" %","Base del cálculo de empleo expuesto"],
  ["Apoyo financiero",D.apoyo.base>0?"50,7 %":"—","La mitad no expresa preferencia de instrumento"],
],[2600,1700,5060]));
body.push(P("Además, "+n(D.cal.nit_ced)+" de "+n(D.cal.nit_base)+" registros que traen NIT y cédula ("+pct(100*D.cal.nit_ced/D.cal.nit_base)+") tienen el mismo número en ambos campos. Es esperable en personas naturales con establecimiento de comercio, pero impide usar el NIT como identificador de empresa formal sin verificación previa contra el RUES."));

body.push(H2("4.4 Categorías «Otra» que repiten opciones del formulario"));
body.push(P("En el campo de afectaciones, "+D.redundantes+" respuestas seleccionaron «Otra» y escribieron a mano una opción que ya existía en la lista —«Daños en infraestructura, maquinaria o equipos», sobre todo. Este informe las consolida en la categoría correspondiente; sin esa corrección, la afectación de infraestructura aparecería subestimada en unos diez puntos porcentuales. El archivo también presenta errores de codificación de caracteres en el texto libre («Da?os» por «Daños»), señal de una exportación con codificación inconsistente."));


// 5 MAGNITUD
body.push(H1("5. Magnitud y severidad de la afectación"));
body.push(img("fig1_severidad.png",600,242));
body.push(Cap("Figura 2. Distribución de los "+n(D.tur_est)+" establecimientos turísticos por severidad."));
body.push(Fuente("«Nivel de afectación» es un campo derivado que calcula la plataforma a partir de las respuestas, no una autoevaluación del empresario."));
body.push(P("La afectación severa domina el conjunto: "+n(D.cg)+" establecimientos ("+pct(D.pct_cg)+") están en categoría crítica o grave. Otros "+n(K("Sin clasificación"))+" ("+pct(100*K("Sin clasificación")/D.tur_est)+") no tienen clasificación, y ese vacío no es neutro: si se distribuyeran como el resto, sumarían alrededor de "+Math.round(K("Sin clasificación")*D.pct_cg/100)+" casos severos adicionales."));

body.push(H2("La clasificación es coherente con la capacidad de operar"));
body.push(P("Un campo derivado merece verificación antes de construir decisiones sobre él. El cruce con la continuidad operativa —una pregunta directa e independiente— confirma que la clasificación se comporta como debe."));
body.push(img("fig3_continuidad.png",600,258));
body.push(Cap("Figura 3. Continuidad operativa según el nivel de afectación asignado."));
body.push(P("El 79 % de los establecimientos clasificados como críticos no puede operar, mientras que ninguno de los clasificados como moderados o bajos está en esa situación. La gradación es limpia y sostiene el uso del campo para priorizar."));

body.push(H2("Capacidad operativa y exposición económica"));
body.push(tabla(["Indicador","Casos","Base informada","Resultado"],[
  ["Microempresas",n(D.tam.c["Microempresa"]),n(D.tam.base),pct(100*D.tam.c["Microempresa"]/D.tam.base)],
  ["No puede operar",n(D.cont.c["No puede operar"]),n(D.cont.base),pct(100*D.cont.c["No puede operar"]/D.cont.base)],
  ["Opera parcialmente",n(D.cont.c["Sí, pero parcialmente"]),n(D.cont.base),pct(100*D.cont.c["Sí, pero parcialmente"]/D.cont.base)],
  ["Pérdidas superiores a $20 millones",n(D.perd.c["Más de $20 y hasta $100 millones."]+D.perd.c["Más de $100 millones."]),n(D.perd.base),pct(100*(D.perd.c["Más de $20 y hasta $100 millones."]+D.perd.c["Más de $100 millones."])/D.perd.base)],
  ["Algún empleo en riesgo",n(D.empleo.con),n(D.empleo.base),pct(100*D.empleo.con/D.empleo.base)],
],[3600,1600,1900,2260]));
body.push(Fuente("Cada indicador se calcula únicamente sobre los registros con respuesta en esa variable; las bases difieren entre filas y por eso se declaran."));
body.push(P("El perfil es de microempresa: "+pct(100*D.tam.c["Microempresa"]/D.tam.base)+" de los establecimientos que informan tamaño lo son. Esto condiciona el instrumento de apoyo —una microempresa sin operación agota su liquidez en semanas, no en meses— y explica que la preferencia declarada se incline hacia recursos no reembolsables."));

body.push(H2("Cuánto dinero hay en juego"));
body.push(P("Las pérdidas se declaran en rangos, así que solo puede calcularse un intervalo. Sumando el extremo inferior de cada rango, los "+n(D.econ.base)+" establecimientos que responden acumulan al menos $"+n(D.econ.lo)+" millones. Sumando el extremo superior de los rangos cerrados, $"+n(D.econ.hi)+" millones. A eso se añaden "+n(D.econ.abierto)+" establecimientos que declaran «más de $100 millones» sin límite superior."));
body.push(Rich([["Cota inferior defendible: $"+n(D.econ.minimo)+" millones","b"],
  [" —unos 28 mil millones de pesos— considerando el piso de cada rango más el mínimo del rango abierto. La cifra real es mayor, y no puede estimarse con precisión sin pedir el monto exacto.",""]]));


// 6 NECESIDADES
body.push(H1("6. Tipos de afectación y necesidades declaradas"));
body.push(tabla(["Tipo de afectación","Menciones","% de los "+n(D.tur_est)],
  Object.entries(D.afect).map(([k,v])=>[k,n(v),pct(100*v/D.tur_est)]),
  [4900,2200,2260]));
body.push(Fuente("Selección múltiple: las menciones no suman establecimientos únicos. Incluye "+D.redundantes+" respuestas reclasificadas desde «Otra» hacia la categoría que les correspondía."));
body.push(P("La crisis es simultáneamente física y comercial. El daño en infraestructura, maquinaria o equipos es la afectación más frecuente ("+pct(100*D.afect["Daños en infraestructura, maquinaria o equipos"]/D.tur_est)+"), pero la reducción de clientes y ventas la sigue de cerca ("+pct(100*D.afect["Reducción de clientes, pedidos o ventas"]/D.tur_est)+"). Un programa que solo repare edificios dejará sin resolver la mitad del problema: hay establecimientos con la infraestructura intacta y sin clientes."));
body.push(esp(80));
body.push(tabla(["Principal necesidad","Menciones","% de los "+n(D.tur_est)],
  Object.entries(D.nec).map(([k,v])=>[k,n(v),pct(100*v/D.tur_est)]),
  [4900,2200,2260]));
body.push(P("En apoyo financiero, entre los "+n(D.apoyo.base)+" establecimientos que expresan preferencia (el 48 % del universo), la opción más frecuente es capital semilla o recursos no reembolsables ("+n(D.apoyo.c["Capital semilla o recursos no reembolsables"])+" menciones, "+pct(100*D.apoyo.c["Capital semilla o recursos no reembolsables"]/D.apoyo.base)+"), seguida del alivio de obligaciones vigentes ("+n(D.apoyo.c["Alivio de las obligaciones actuales"])+"). El crédito nuevo aparece en tercer lugar: un sector con la operación interrumpida no percibe capacidad de endeudarse más."));

// 7 PRIORIZACION
body.push(H1("7. Priorización municipal"));
body.push(P("Se conserva el puntaje exploratorio del informe anterior para mantener la comparabilidad, con una corrección metodológica que se explica abajo. El puntaje combina la carga absoluta de casos severos con una medida conservadora de intensidad."));
body.push(esp(60));
body.push(caja("Fórmula implementada",[
  "Prioridad = 100 × [0,60 × percentil municipal de la carga crítica/grave + 0,40 × límite inferior de Wilson al 95 % de la proporción crítica/grave].",
  "Corrección respecto al corte anterior: los establecimientos «sin clasificación» se excluyen del denominador de la proporción, en lugar de contar como no severos. Tratarlos como leves premiaba al municipio que peor diligencia el formulario."]));
body.push(esp(140));
body.push(img("fig2_prioridad.png",600,367));
body.push(Cap("Figura 4. Quince municipios con mayor prioridad operativa del sector turismo."));
body.push(esp(60));
body.push(tabla(["#","Municipio","Puntaje","n","C+G","% C+G","Sin clasif.","Afectación oficial"],
  top.map(r=>[String(r["#"]),titulo(r.Municipio),
              String(r.prioridad).replace('.',','),n(r.n),n(r.cg),
              String(r.pct_cg).replace('.',',')+" %",
              String(r.pct_sin_clasif).replace('.',',')+" %", r.nivel_oficial]),
  [500,1900,1000,750,750,1000,1100,2360],{numDesde:2,textoFinal:true}));
body.push(Fuente("C+G = establecimientos críticos más graves. «Afectación oficial» es la clasificación del consolidado departamental del Observatorio GeoRiesgo, calculada sobre daño físico y víctimas, no sobre actividad empresarial."));
body.push(P("Cali encabeza por volumen: "+n(top[0].cg)+" establecimientos severos, casi cinco veces el segundo. Buenaventura y Roldanillo combinan proporciones severas superiores al 71 % con afectación oficial muy alta, lo que los convierte en prioridad tanto por intensidad como por corroboración externa. Sevilla y Caicedonia destacan por intensidad —77,5 % y 83,8 % de casos severos— sobre universos más pequeños pero estadísticamente estables."));
body.push(esp(60));
body.push(caja("Lectura cautelosa de Cartago y Jamundí",[
  "Cartago aparece noveno con 95 establecimientos, pero el 27,4 % no tiene severidad clasificada y su proporción severa observada es apenas 36,8 %, la más baja del grupo alto. Jamundí, decimoctavo, tiene el 33,3 % sin clasificar pese a figurar con afectación oficial muy alta.",
  "En ambos casos la posición depende de datos incompletos y debe revisarse tras el trabajo de campo. No conviene interpretarla como menor impacto definitivo."]),ROJO);

body.push(H1("8. Distribución territorial"));
body.push(img("fig6_mapa.png",470,545));
body.push(Cap("Figura 5. Priorización municipal exploratoria del sector turismo."));
body.push(Fuente("Cartografía: Marco Geoestadístico Nacional (DANE), a través del Observatorio GeoRiesgo. Los 42 municipios tienen al menos un reporte turístico."));

// 9 CRUCE OBSERVATORIO
body.push(H1("9. Contraste con la afectación oficial: dónde puede faltar registro"));
body.push(P("El observatorio de la emergencia clasifica los 42 municipios por daño físico y víctimas, con fuente independiente de esta encuesta empresarial. Cruzar ambas miradas permite una pregunta que ninguna responde por separado: ¿está el registro empresarial llegando a los municipios que más daño sufrieron?"));
body.push(img("fig4_cobertura.png",600,325));
body.push(Cap("Figura 6. Reportes del sector frente al total empresarial y a la afectación oficial del municipio."));
body.push(P("En términos generales sí hay correspondencia: los municipios con afectación oficial muy alta concentran reportes. Pero cinco casos muestran una brecha que conviene verificar en campo antes de concluir que el sector allí está menos afectado."));
body.push(esp(60));
body.push(tabla(["Municipio","Afectación oficial","Turismo","Empresas (total)","Lectura"],[
  ["Bolívar","Muy alta","3","45","Solo 3 reportes turísticos en un municipio de afectación máxima"],
  ["Toro","Muy alta","11","92","Volumen bajo frente a su nivel oficial"],
  ["Dagua","Muy alta","18","122","Corredor turístico hacia el Pacífico, registro escaso"],
  ["Restrepo","Muy alta","24","210","Vocación turística conocida, 11 % de sus empresas"],
  ["Zarzal","Muy alta","28","308","Solo 8 severos pese al nivel oficial muy alto"],
],[1600,1900,1000,1700,3160]));
body.push(Fuente("«Empresas (total)» es el número de reportes de todos los sectores en ese municipio, del mismo archivo."));
body.push(Rich([["Esto no demuestra subregistro: ","b"],
  ["puede que el turismo tenga poco peso en esos municipios, o que el daño se concentrara en vivienda y no en establecimientos comerciales. Lo que sí indica es dónde una verificación de campo tendría más valor, porque un municipio con daño físico severo y pocos reportes empresariales es o bien un lugar sin sector, o bien un lugar donde el sector no supo del registro.",""]]));

// 10 LIMITACIONES
body.push(H1("10. Limitaciones"));
body.push(Bul("El universo es autoseleccionado. Solo aparecen quienes conocieron el registro y decidieron reportar; la ausencia de un establecimiento no significa que esté indemne."));
body.push(Bul("«Turismo» es la clasificación de actividad económica de la fuente, no el Registro Nacional de Turismo. Incluye restaurantes y transportadores que pueden no atender demanda turística."));
body.push(Bul("El nivel de afectación lo calcula la plataforma con una fórmula que este informe no conoce. Su coherencia con la continuidad operativa se verificó (sección 5), pero la fórmula misma no pudo auditarse."));
body.push(Bul("Las pérdidas y los empleos se declaran en rangos, no en cifras exactas; solo pueden acotarse intervalos."));
body.push(Bul("El puntaje de priorización es exploratorio y sus pesos (0,60 / 0,40) son una decisión de diseño, no un resultado empírico. Municipios con mucha información sin clasificar quedan mal representados."));
body.push(Bul("No se dispone del universo empresarial municipal —cuántos establecimientos turísticos existen en cada municipio—, de modo que no puede calcularse una tasa de afectación sobre el total. Todas las cifras son absolutas."));

body.push(H1("11. Recomendaciones"));
body.push(P("Ordenadas por urgencia, no por facilidad:"));
body.push(Bul("Sanear el consentimiento de datos personales de los "+n(D.cal.sin_cons+D.cal.sin_resp)+" registros sin autorización verificable, antes de cualquier contacto derivado de esta base."));
body.push(Bul("Completar la clasificación de severidad de los "+n(K("Sin clasificación"))+" establecimientos turísticos sin nivel, priorizando Cartago, Jamundí, Palmira y Ansermanuevo, donde el vacío supera el 25 %."));
body.push(Bul("Corregir en origen el formato de fecha y la codificación de caracteres del formulario, y añadir validación que impida fechas futuras."));
body.push(Bul("Verificar en campo los cinco municipios con posible subregistro identificados en la sección 9."));
body.push(Bul("Diseñar el instrumento de apoyo alrededor de dos necesidades simultáneas —reparación física y capital de trabajo—, con predominio de recursos no reembolsables sobre crédito nuevo, dada la composición microempresarial del sector."));
body.push(Bul("Cruzar el universo con el Registro Nacional de Turismo para separar prestadores certificados del resto, y con el RUES para validar los NIT."));

body.push(new Paragraph({children:[new PageBreak()]}));
body.push(H1("Anexo. Los 42 municipios"));
body.push(P("Ordenados por puntaje de prioridad. «C+G» son los establecimientos críticos o graves."));
body.push(tabla(["#","Municipio","Punt.","n","C+G","% C+G","Sin clas.","Oficial"],
  pri.map(r=>[String(r["#"]),titulo(r.Municipio),
              String(r.prioridad).replace('.',','),n(r.n),n(r.cg),
              String(r.pct_cg).replace('.',',')+" %",
              String(r.pct_sin_clasif).replace('.',',')+" %",r.nivel_oficial]),
  [500,2100,900,700,700,950,1050,2460],{numDesde:2,textoFinal:true}));
body.push(Fuente("Fuente: elaboración propia sobre reportes_emergencia_2026-09-01.xlsx y el consolidado municipal del Observatorio GeoRiesgo. Corte: 1 de septiembre de 2026."));

const doc = new Document({
  creator:"Observatorio de Turismo · Valle del Cauca",
  title:"Sector turismo: afectación empresarial y priorización municipal",
  description:"Análisis de "+D.n_reportes+" reportes empresariales tras el terremoto del 10 de agosto de 2026",
  numbering:{config:[{reference:"vinetas",levels:[{level:0,format:LevelFormat.BULLET,text:"•",
    alignment:AlignmentType.LEFT,style:{paragraph:{indent:{left:convertInchesToTwip(0.28),hanging:convertInchesToTwip(0.18)}}}}]}]},
  sections:[{properties:{page:{margin:{top:1080,bottom:1080,left:1080,right:1080}}},children:body}]});

Packer.toBuffer(doc).then(b=>{fs.writeFileSync("Informe_sector_turismo_2026-09-01.docx",b);
  console.log("documento generado:", (b.length/1024).toFixed(0), "KB");});

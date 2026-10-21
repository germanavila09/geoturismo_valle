const fs=require('fs'); const d=require('docx');
const {Document,Packer,Paragraph,TextRun,HeadingLevel,Table,TableRow,TableCell,
 WidthType,ShadingType,AlignmentType,BorderStyle,ImageRun,PageBreak,LevelFormat,
 convertInchesToTwip}=d;
const D=JSON.parse(fs.readFileSync('datos3.json','utf8'));
const AZUL="1F3864",ROJO="B3261E",VERDE="2D6A4F",GRIS="595959",CLARO="F2F5FA",BORDE="D5DBE5";
const n=x=>(x===null||x===undefined||Number.isNaN(x))?"—":Number(x).toLocaleString('es-CO');
const pc=x=>Number(x).toFixed(1).replace('.',',')+" %";
const num=x=>String(x).replace('.',',');
const tit=t=>String(t).toLowerCase().replace(/(^|[\s(])(\w)/g,(m,a,b)=>a+b.toUpperCase())
  .replace(/\bDe\b/g,'de');

const P=(t,o={})=>new Paragraph({spacing:{after:o.after??140,line:300},alignment:o.al,
  children:[new TextRun({text:t,size:o.size??20,bold:o.b,italics:o.i,color:o.c??"1A1A1A",font:"Calibri"})]});
const Rich=(runs,o={})=>new Paragraph({spacing:{after:o.after??140,line:300},
  children:runs.map(r=>new TextRun({text:r[0],bold:r[1]==='b',italics:r[1]==='i',
    size:o.size??20,color:o.c??"1A1A1A",font:"Calibri"}))});
const H1=t=>new Paragraph({heading:HeadingLevel.HEADING_1,spacing:{before:340,after:150},
  keepNext:true,keepLines:true,children:[new TextRun({text:t,size:28,bold:true,color:AZUL,font:"Calibri"})]});
const H2=t=>new Paragraph({heading:HeadingLevel.HEADING_2,spacing:{before:250,after:110},
  keepNext:true,keepLines:true,children:[new TextRun({text:t,size:23,bold:true,color:AZUL,font:"Calibri"})]});
const Bul=t=>new Paragraph({numbering:{reference:"v",level:0},spacing:{after:80,line:290},
  children:[new TextRun({text:t,size:20,font:"Calibri",color:"1A1A1A"})]});
const Fu=t=>new Paragraph({spacing:{after:200},
  children:[new TextRun({text:t,size:16,italics:true,color:GRIS,font:"Calibri"})]});
const Cap=t=>new Paragraph({spacing:{before:60,after:180},
  children:[new TextRun({text:t,size:17,bold:true,color:GRIS,font:"Calibri"})]});
const celda=(t,{b,al,w,sh,c,sz}={})=>new TableCell({width:{size:w,type:WidthType.DXA},
  shading:sh?{type:ShadingType.CLEAR,fill:sh,color:"auto"}:undefined,
  margins:{top:70,bottom:70,left:110,right:110},
  children:[new Paragraph({alignment:al??AlignmentType.LEFT,spacing:{after:0},
    children:[new TextRun({text:String(t),size:sz??17,bold:b,color:c??"1A1A1A",font:"Calibri"})]})]});
function tabla(cab,filas,anchos,o={}){
  const bd={top:{style:BorderStyle.SINGLE,size:2,color:BORDE},
    bottom:{style:BorderStyle.SINGLE,size:2,color:BORDE},
    left:{style:BorderStyle.NONE},right:{style:BorderStyle.NONE},
    insideHorizontal:{style:BorderStyle.SINGLE,size:1,color:"E8ECF2"},
    insideVertical:{style:BorderStyle.NONE}};
  const der=(i,nc)=>i>=(o.numDesde??1)&&!(o.textoFinal&&i===nc-1);
  return new Table({columnWidths:anchos,width:{size:anchos.reduce((a,b)=>a+b,0),type:WidthType.DXA},
    borders:bd,rows:[
      new TableRow({tableHeader:true,children:cab.map((t,i)=>celda(t,{b:true,sh:AZUL,c:"FFFFFF",
        w:anchos[i],al:der(i,cab.length)?AlignmentType.RIGHT:AlignmentType.LEFT}))}),
      ...filas.map((f,j)=>new TableRow({children:f.map((t,i)=>celda(t,{w:anchos[i],
        sh:j%2?CLARO:undefined,al:der(i,f.length)?AlignmentType.RIGHT:AlignmentType.LEFT}))}))]});
}
function ficha(filas,anchos){
  const bd={top:{style:BorderStyle.SINGLE,size:2,color:BORDE},
    bottom:{style:BorderStyle.SINGLE,size:2,color:BORDE},
    left:{style:BorderStyle.NONE},right:{style:BorderStyle.NONE},
    insideHorizontal:{style:BorderStyle.SINGLE,size:1,color:"E8ECF2"},
    insideVertical:{style:BorderStyle.NONE}};
  return new Table({columnWidths:anchos,width:{size:anchos[0]+anchos[1],type:WidthType.DXA},borders:bd,
    rows:filas.map((f,j)=>new TableRow({children:[
      celda(f[0],{w:anchos[0],b:true,c:GRIS,sh:j%2?CLARO:undefined}),
      celda(f[1],{w:anchos[1],sh:j%2?CLARO:undefined})]}))});
}
function caja(t,tx,col=AZUL){
  return new Table({columnWidths:[9360],width:{size:9360,type:WidthType.DXA},
    borders:{top:{style:BorderStyle.NONE},bottom:{style:BorderStyle.NONE},
      left:{style:BorderStyle.SINGLE,size:18,color:col},right:{style:BorderStyle.NONE},
      insideHorizontal:{style:BorderStyle.NONE},insideVertical:{style:BorderStyle.NONE}},
    rows:[new TableRow({children:[new TableCell({width:{size:9360,type:WidthType.DXA},
      shading:{type:ShadingType.CLEAR,fill:CLARO,color:"auto"},
      margins:{top:160,bottom:160,left:220,right:180},
      children:[new Paragraph({spacing:{after:70},children:[new TextRun({text:t,bold:true,size:20,color:col,font:"Calibri"})]}),
        ...tx.map(x=>new Paragraph({spacing:{after:60,line:290},
          children:[new TextRun({text:x,size:19,color:"1A1A1A",font:"Calibri"})]}))]})]})]});
}
const img=(f,w,h)=>new Paragraph({alignment:AlignmentType.CENTER,spacing:{before:120,after:60},
  keepNext:true,children:[new ImageRun({type:"png",data:fs.readFileSync(f),transformation:{width:w,height:h}})]});
const salto=()=>new Paragraph({children:[new PageBreak()]});
const esp=(a=120)=>new Paragraph({spacing:{after:a},children:[]});

const b=[];
const S=D.sev.c, C=D.cont.c, PE=D.perd.c, EM=D.empl.c, DU=D.dup, DE=D.descriptivos;
const sev=S["Crítica"]+S["Grave"], pctSev=100*sev/D.sev.base;
const BN=D.bases["Principal necesidad"], BA=D.bases["Apoyo financiero"];
const M=D.mun, mun=k=>M.find(x=>x.municipio===k);
const cor=(a,c)=>D.correlaciones[a][c];
// Cuantos municipios aparecen entre los doce primeros de varios indicadores.
const IND4=["pct_severo","pct_no_opera","pct_perd_alta","pct_empleo"];
const doce={};
IND4.forEach(c=>M.filter(x=>x[c]!==null).sort((a,z)=>z[c]-a[c]).slice(0,12)
  .forEach(x=>{doce[x.municipio]=(doce[x.municipio]||0)+1;}));
const enTres=Object.values(doce).filter(v=>v>=3).length;
const enCuatro=Object.values(doce).filter(v=>v===4).length;

// ══════════ PORTADA ══════════
b.push(new Paragraph({spacing:{after:60},children:[new TextRun({
  text:"OBSERVATORIO DE TURISMO · VALLE DEL CAUCA",size:17,bold:true,color:GRIS,font:"Calibri",characterSpacing:24})]}));
b.push(new Paragraph({spacing:{after:80},children:[new TextRun({
  text:"Impacto económico del terremoto en el tejido empresarial",size:40,bold:true,color:AZUL,font:"Calibri"})]}));
b.push(new Paragraph({spacing:{after:260},border:{bottom:{style:BorderStyle.SINGLE,size:12,color:ROJO}},
  children:[new TextRun({text:"Análisis geoestadístico descriptivo de "+n(D.n)+" establecimientos únicos en los 42 municipios del Valle del Cauca",
  size:24,color:GRIS,font:"Calibri"})]}));
b.push(ficha([
  ["Corte de información","1 de septiembre de 2026 · sismo del 10 de agosto de 2026"],
  ["Universo",n(DU.n0)+" reportes recibidos → "+n(D.n)+" establecimientos únicos tras depurar la doble notificación"],
  ["Variables analizadas","continuidad operativa, pérdidas económicas, empleos en riesgo, principal necesidad, apoyo financiero y nivel de afectación"],
  ["Datos sensibles","ninguno en los resultados. Nombres, documentos, teléfonos, correos y NIT se usan solo para detectar duplicados y no salen del proceso"],
  ["Método","estadística descriptiva por municipio · contracción bayesiana empírica · correlación de Spearman"],
  ["Contraste externo","DANE, Fundación WWB Colombia, Cámara de Comercio de Cali y Confecámaras"],
],[2300,7060]));
b.push(esp(240));
b.push(caja("Los cuatro resultados que ordenan la decisión",[
  "1. Uno de cada veinte reportes era una doble notificación. "+n(DU.extras)+" registros ("+num(DU.pct)+" %) correspondían a establecimientos que reportaron dos o más veces. Depurarlos sube la severidad departamental "+num((DU.despues.pct_severo-DU.antes.pct_severo).toFixed(2))+" puntos: los duplicados no eran neutros, se concentraban en los menos afectados.",
  "2. La parálisis es mayor que el daño físico. "+pc(D.noop_norm)+" de los establecimientos no opera con normalidad, pero solo el "+num(D.wwb.inutil)+" % de los locales fue declarado inutilizable según el estudio de la Fundación WWB. Un negocio en pie puede haber perdido su capacidad de vender.",
  "3. Severidad y pérdidas van juntas; parálisis y pérdidas, no. La correlación entre el porcentaje de establecimientos críticos y el de pérdidas altas es de "+num(cor("pct_severo","pct_perd_alta").toFixed(2))+"; entre parálisis y pérdidas altas cae a "+num(cor("pct_no_opera","pct_perd_alta").toFixed(2))+". Hay municipios paralizados sin pérdidas grandes y municipios operando con pérdidas enormes: son dos problemas distintos y piden dos instrumentos distintos.",
  "4. El golpe llega al hogar. El "+num(D.wwb.vivienda)+" % de los micronegocios opera dentro de la vivienda y el "+num(D.wwb.hogares)+" % de esos hogares ya tiene dificultad para cubrir gastos básicos. Reparar el negocio y reparar la casa son el mismo problema.",
],ROJO));

// ══════════ 1. RESUMEN ══════════
b.push(H1("1. Resumen ejecutivo"));
b.push(P("Este informe analiza la afectación económica declarada por establecimientos de todos los sectores en los 42 municipios del Valle del Cauca, sobre seis variables de operación y necesidad. Ningún resultado contiene datos que identifiquen a una persona o a una empresa."));
b.push(P("De los "+n(DU.n0)+" reportes recibidos, "+n(DU.extras)+" resultaron ser segundas o terceras notificaciones del mismo establecimiento. El análisis se hace sobre los "+n(D.n)+" establecimientos únicos que quedan, equivalentes al "+num(D.dane.cobertura)+" % de las "+n(D.dane.unidades)+" unidades económicas que el DANE registra en el departamento. La cifra no mide la afectación total del Valle: mide a quienes conocieron el registro y decidieron reportar."));
b.push(H2("Magnitud"));
b.push(Bul(n(sev)+" establecimientos ("+pc(pctSev)+") están en nivel crítico o grave: "+n(S["Crítica"])+" críticos y "+n(S["Grave"])+" graves."));
b.push(Bul(pc(D.noop_norm)+" no opera con normalidad. De los "+n(D.cont.base)+" que responden, "+n(C["No puede operar"])+" ("+pc(100*C["No puede operar"]/D.cont.base)+") no pueden operar en absoluto."));
b.push(Bul("Las pérdidas declaradas suman al menos "+n(D.econ.min)+" millones de pesos —unos "+Math.round(D.econ.min/1000)+" mil millones—, y es un piso: "+n(D.econ.ab)+" establecimientos declaran «más de $100 millones» sin techo."));
b.push(Bul("Entre "+n(D.empleo.lo)+" y "+n(D.empleo.hi)+" empleos están comprometidos. El "+pc(D.empleo.pct)+" de los "+n(D.empl.base)+" que informan tienen al menos un puesto en riesgo."));
b.push(Bul("La necesidad más citada es capital de trabajo ("+n(D.nec["Capital de trabajo o insumos"])+" menciones), apenas por encima de reparar instalaciones ("+n(D.nec["Reparar instalaciones o equipos"])+"). La crisis es de liquidez tanto como de infraestructura."));
b.push(H2("Territorio"));
b.push(Bul("Los diez municipios con mayor índice de afectación ajustado son "+D.top10.slice(0,5).map(tit).join(", ")+", "+D.top10.slice(5).map(tit).join(", ")+"."));
b.push(Bul("El indicador más desigual entre municipios es el de pérdidas altas (coeficiente de variación "+num(DE["Pérdidas superiores a $20 millones"].cv)+"): va de "+num(DE["Pérdidas superiores a $20 millones"].min)+" % en "+tit(DE["Pérdidas superiores a $20 millones"].min_mun)+" a "+num(DE["Pérdidas superiores a $20 millones"].max)+" % en "+tit(DE["Pérdidas superiores a $20 millones"].max_mun)+". El más homogéneo es el de empleo en riesgo (CV "+num(DE["Con algún empleo en riesgo"].cv)+"): golpea parejo en todo el departamento."));
b.push(Bul("El orden de los municipios cambia según el indicador que se mire: de los "+n(Object.keys(doce).length)+" municipios que entran en algún top 12, solo "+n(enTres)+" aparecen en tres o más rankings y "+n(enCuatro)+" en los cuatro. Publicar un solo ranking oculta esa diferencia."));
b.push(Bul("El volumen de reportes de un municipio explica poco de su intensidad de afectación (ρ = "+num(cor("pct_severo","n").toFixed(2))+"), de modo que el ranking no es un artefacto de dónde alcanzó a llegar el registro."));

// ══════════ 2. DUPLICIDAD ══════════
b.push(salto());
b.push(H1("2. Depuración: la doble notificación"));
b.push(P("Este apartado va antes que los resultados porque los condiciona a todos. Si un mismo negocio reporta dos veces, cuenta dos veces en el total, dos veces en su municipio y dos veces en cada porcentaje. Ningún indicador posterior es interpretable sin saber cuánto de esto había."));

b.push(H2("2.1 Dos errores opuestos, y por qué el segundo es peor"));
b.push(P("Detectar duplicados admite equivocarse en dos direcciones, y no cuestan lo mismo."));
b.push(Rich([["Fusionar de menos ","b"],["deja el conteo inflado. Es lo que hacía la depuración inicial, que solo unió 131 registros por NIT o razón social idéntica y dejaba pasar el caso más común: la misma persona que vuelve a llenar el formulario y escribe el nombre distinto.",""]]));
b.push(Rich([["Fusionar de más ","b"],["borra establecimientos reales, y eso no se nota mirando el resultado. Un primer intento con similitud difusa de razón social y cierre transitivo produjo un grupo de 200 reportes con 199 teléfonos distintos repartidos en 13 municipios: el encadenamiento «A se parece a B, B se parece a C» une negocios que no tienen nada que ver. Agrupar por «razón social + municipio» falla por otro lado: los grupos más grandes eran AGROPECUARIA, NINGUNO, VENDEDOR AMBULANTE y COMERCIANTE, personas que describieron su oficio en vez de nombrar un negocio.",""]]));
b.push(P("Por eso el método final solo agrupa por identificadores fuertes —teléfono, correo, NIT y número de documento— y nunca por parecido de nombre."));

b.push(H2("2.2 La guarda de coherencia: distinguir un duplicado de un gestor"));
b.push(P("Compartir un teléfono no basta. Al revisar los grupos aparece un tercer patrón que no es duplicidad:"));
b.push(tabla(["Señal compartida","Reportes","Municipios","Razones sociales","Documentos"],
  DU.gestor_detalle.map(g=>[g.senal,n(g.reportes),n(g.municipios),n(g.razones_sociales),n(g.documentos)]),
  [2200,1700,1700,2100,1660]));
b.push(Fu("Los cinco grupos más grandes que el método rechazó por incoherentes."));
b.push(P("Un correo en "+n(DU.gestor_max)+" reportes de 13 municipios distintos, con 35 razones sociales y 23 documentos, no es un negocio que reportó 35 veces: es alguien que diligenció el formulario para muchos negocios y puso sus propios datos de contacto. Colapsar ese grupo habría borrado 34 establecimientos reales."));
b.push(P("Un grupo se acepta como duplicado solo si además puede ser una sola unidad económica: a lo sumo un número de documento distinto y a lo sumo dos razones sociales. Si no cumple, se marca como patrón de gestor y no se fusiona. Se contaron "+n(DU.gestores)+" grupos así, y quedan registrados aparte porque también dicen algo sobre cómo se levantó el registro."));

b.push(H2("2.3 Resultado"));
b.push(img("f6_duplicados.png",620,194));
b.push(Cap("Figura 1. Duplicados detectados por señal, tamaño de los grupos y efecto sobre los indicadores."));
b.push(esp(40));
b.push(tabla(["","Reportes","Interpretación"],[
  ["Reportes recibidos",n(DU.n0),"lo que muestra el archivo fuente"],
  ["Establecimientos únicos",n(DU.n_unicos),"universo real del análisis"],
  ["Doble notificación",n(DU.extras)+"  ("+num(DU.pct)+" %)","registros de más"],
  ["Grupos duplicados",n(DU.n_grupos_dup),n(DU.tam_grupos["2"])+" pares, "+n(DU.tam_grupos["3"])+" tríos, "+n(DU.tam_grupos["4"])+" cuartetos"],
  ["Grupos de gestor",n(DU.gestores),"detectados y NO fusionados"],
],[2900,1700,4760],{textoFinal:true}));
b.push(Fu("Al colapsar un grupo se conserva el reporte con la severidad más alta: entre dos notificaciones del mismo negocio se asume el peor estado declarado."));
b.push(P("Ningún grupo supera los "+n(DU.max_grupo)+" reportes. Esa es la señal de que la guarda funciona: el problema real es «llené el formulario dos veces», no «un actor cargó cien registros»."));

b.push(H2("2.4 Efecto sobre las métricas"));
b.push(tabla(["Indicador","Con duplicados","Depurado","Diferencia"],[
  ["Establecimientos",n(DU.antes.n),n(DU.despues.n),n(DU.despues.n-DU.antes.n)],
  ["Crítico o grave",num(DU.antes.pct_severo)+" %",num(DU.despues.pct_severo)+" %","+"+num((DU.despues.pct_severo-DU.antes.pct_severo).toFixed(2))+" pp"],
  ["No puede operar",num(DU.antes.pct_no_opera)+" %",num(DU.despues.pct_no_opera)+" %","+"+num((DU.despues.pct_no_opera-DU.antes.pct_no_opera).toFixed(2))+" pp"],
  ["No opera con normalidad",num(DU.antes.pct_no_normal)+" %",num(DU.despues.pct_no_normal)+" %","+"+num((DU.despues.pct_no_normal-DU.antes.pct_no_normal).toFixed(2))+" pp"],
  ["Pérdidas superiores a $20M",num(DU.antes.pct_perd_alta)+" %",num(DU.despues.pct_perd_alta)+" %","+"+num((DU.despues.pct_perd_alta-DU.antes.pct_perd_alta).toFixed(2))+" pp"],
],[3100,2100,2100,2060],{numDesde:1}));
b.push(Rich([["El sesgo tiene dirección. ","b"],
  ["Los cuatro indicadores suben al depurar, entre "+num((DU.despues.pct_perd_alta-DU.antes.pct_perd_alta).toFixed(2))+" y "+num((DU.despues.pct_severo-DU.antes.pct_severo).toFixed(2))+" puntos. Si los duplicados hubieran sido aleatorios, la diferencia sería cercana a cero. Que todos los indicadores suban significa que quien reportó dos veces tendía a estar menos afectado: la duplicidad estaba subestimando la severidad, no exagerándola.",""]]));
b.push(P("La magnitud es modesta —poco más de un punto porcentual en el peor caso— y no cambia ninguna conclusión de fondo. Pero sí cambia el número que se publica, y en un municipio pequeño el efecto es mayor que en el promedio departamental."));

b.push(H2("2.5 Dónde se concentra la doble notificación"));
b.push(tabla(["Municipio","Reportes","Únicos","Duplicados","% duplicado"],
  DU.por_municipio.slice(0,8).map(m=>[tit(m.municipio),n(m.reportes),n(m.unicos),n(m.dup),num(m.pct)+" %"]),
  [2600,1600,1500,1700,1960]));
b.push(Fu("Municipios con al menos 20 reportes, ordenados por proporción de doble notificación."));
b.push(P("Cartago es el caso que más pesa en términos absolutos: "+n(DU.por_municipio.find(x=>x.municipio==="CARTAGO").dup)+" duplicados sobre "+n(DU.por_municipio.find(x=>x.municipio==="CARTAGO").reportes)+" reportes. Guadalajara de Buga y La Cumbre tienen las proporciones más altas. La lectura operativa es que la calidad del registro varía por municipio, probablemente según cómo se difundió el formulario y si hubo jornadas presenciales de diligenciamiento."));
b.push(caja("Recomendación de registro",[
  "El formulario no valida contra reportes previos del mismo teléfono, correo o documento. Añadir esa comprobación en el momento de captura —avisando al usuario «ya existe un reporte con este contacto, ¿desea actualizarlo?»— evita el problema en origen y es mucho más barato que corregirlo después.",
  "Mientras no exista, cualquier corte de esta base debe depurarse antes de publicarse."]));

// ══════════ 3. ALCANCE Y MÉTODO ══════════
b.push(salto());
b.push(H1("3. Alcance, variables y tratamiento de datos"));
b.push(H2("3.1 Las seis variables y su base de respuesta"));
b.push(P("El análisis usa exclusivamente las seis variables solicitadas. Ninguna es de identificación. Los porcentajes se calculan siempre sobre quienes respondieron cada pregunta, y esa base se declara en cada tabla porque difiere de forma importante entre variables."));
b.push(tabla(["Variable","Tipo","Registros con dato","Cobertura"],[
  ["Nivel de afectación","derivada por la plataforma",n(D.bases["Nivel de afectación"]),pc(100*D.bases["Nivel de afectación"]/D.n)],
  ["Principal necesidad","selección múltiple",n(D.bases["Principal necesidad"]),pc(100*D.bases["Principal necesidad"]/D.n)],
  ["Pérdidas económicas","ordinal por rangos",n(D.bases["Pérdidas económicas"]),pc(100*D.bases["Pérdidas económicas"]/D.n)],
  ["Continuidad operativa","categórica ordinal",n(D.bases["Continuidad operativa"]),pc(100*D.bases["Continuidad operativa"]/D.n)],
  ["Empleos afectados o en riesgo","ordinal por rangos",n(D.bases["Empleos afectados o en riesgo"]),pc(100*D.bases["Empleos afectados o en riesgo"]/D.n)],
  ["Apoyo financiero","selección múltiple",n(D.bases["Apoyo financiero"]),pc(100*D.bases["Apoyo financiero"]/D.n)],
],[3100,2400,1980,1880]));
b.push(Rich([["Advertencia sobre «apoyo financiero»: ","b"],
  ["solo la mitad de los establecimientos expresa preferencia de instrumento. Las proporciones de esa variable describen a quien opinó, no al sector, y no deben extrapolarse.",""]]));

b.push(H2("3.2 Datos sensibles"));
b.push(P("El archivo fuente contiene nombre completo, documento de identidad, teléfono, correo electrónico, NIT, dirección y barrio. Esos campos se usan en un solo punto del proceso —la detección de duplicados de la sección 2— y en ninguno más: no se agregan, no se cruzan, no se publican y no aparecen en ningún archivo de resultados. El conjunto depurado que alimenta todas las cifras de este informe conserva únicamente el municipio, el sector, el tamaño de empresa y las seis variables analizadas."));
b.push(P("La restricción no es solo metodológica. En la revisión anterior de esta misma base se detectó que 1.576 registros contienen datos personales sin autorización verificable bajo la Ley 1581 de 2012. Trabajar solo con agregados evita propagar ese problema."));

b.push(H2("3.3 El índice de afectación económica"));
b.push(P("Para comparar municipios con una sola cifra se construye un índice que combina las cuatro variables ordinales. Cada respuesta se convierte a una escala de 0 a 1 —de «sin afectación» a «lo peor declarable»— y se promedia con estos pesos:"));
b.push(esp(60));
b.push(tabla(["Componente","Peso","Justificación"],[
  ["Nivel de afectación",num(D.pesos.i_sev.toFixed(2)),"Síntesis que la plataforma calcula con todas las respuestas"],
  ["Continuidad operativa",num(D.pesos.i_cont.toFixed(2)),"Mide si el negocio produce ingresos hoy"],
  ["Pérdidas económicas",num(D.pesos.i_perd.toFixed(2)),"Magnitud del daño patrimonial"],
  ["Empleos en riesgo",num(D.pesos.i_empl.toFixed(2)),"Menor peso: fuerte sesgo al tamaño de la empresa"],
],[2600,1100,5660]));
b.push(Fu("Los pesos son una decisión de diseño, no un resultado empírico. Se declaran para que puedan discutirse y modificarse."));

b.push(H2("3.4 Corrección por tamaño de muestra"));
b.push(P("El índice crudo premia a los municipios con pocos reportes: basta que unos pocos declaren lo peor para que su promedio se dispare, mientras un municipio con miles de reportes no puede moverse tanto. Comparar directamente a Trujillo, con "+n(mun("TRUJILLO").n)+" establecimientos, con Cali, que tiene "+n(mun("SANTIAGO DE CALI")?mun("SANTIAGO DE CALI").n:D.cali.n)+", es comparar una estimación ruidosa con una firme."));
b.push(P("Se aplicó contracción bayesiana empírica hacia la media departamental, con peso proporcional a la información que aporta cada municipio: w = τ² / (τ² + σ²/n). Un municipio con muchos reportes conserva su valor; uno con pocos se acerca al promedio, que es la mejor apuesta cuando su evidencia propia es débil."));
b.push(tabla(["Parámetro","Valor","Qué significa"],[
  ["τ² (varianza entre municipios)",num(D.shrink.tau2),"cuánto difieren realmente los municipios"],
  ["σ² (varianza dentro del municipio)",num(D.shrink.sigma2),"cuánto varían los establecimientos de un mismo municipio"],
  ["μ (media departamental)",num(D.shrink.mu),"hacia dónde se contrae"],
  ["w (peso conservado)","de "+num(D.shrink.w_min)+" a "+num(D.shrink.w_max),"1 = el municipio conserva íntegro su valor"],
],[3300,2100,3960],{textoFinal:true}));
b.push(Rich([["La corrección importa más de lo que parece. ","b"],
  ["σ² es once veces mayor que τ²: los establecimientos de un mismo municipio difieren entre sí mucho más de lo que difieren los municipios entre ellos. El municipio con menos información conserva solo el "+num((100*D.shrink.w_min).toFixed(0))+" % de su valor propio. En el anexo se publican las dos versiones del índice para que la diferencia sea auditable.",""]]));

// ══════════ 4. MAGNITUD ══════════
b.push(salto());
b.push(H1("4. Magnitud de la afectación en el departamento"));
b.push(img("g1_variables.png",600,395));
b.push(Cap("Figura 2. Las cuatro variables ordinales sobre los "+n(D.n)+" establecimientos únicos."));
b.push(Fu("Cada panel declara su base de respuesta. «Nivel de afectación» es un campo derivado que calcula la plataforma; los otros tres son respuestas directas."));

b.push(H2("4.1 La parálisis excede al daño físico"));
b.push(P("De los "+n(D.cont.base)+" establecimientos que informan continuidad, "+n(C["No puede operar"])+" ("+pc(100*C["No puede operar"]/D.cont.base)+") no pueden operar y "+n(C["Sí, pero parcialmente"])+" ("+pc(100*C["Sí, pero parcialmente"]/D.cont.base)+") lo hacen parcialmente. En conjunto, "+pc(D.noop_norm)+" no opera con normalidad."));
b.push(P("El contraste con el daño estructural es el hallazgo central. El diagnóstico de la Fundación WWB Colombia entre "+n(D.wwb.n)+" emprendedores de "+n(D.wwb.mun)+" municipios encontró que solo el "+num(D.wwb.inutil)+" % de los locales fue considerado inutilizable, mientras el "+num(D.wwb.noop)+" % de los negocios no funcionaba con normalidad. La distancia entre ambas cifras —más de sesenta puntos— mide algo que ningún censo de edificaciones capta: negocios que siguen en pie y han perdido la capacidad de producir, atender clientes o generar ingresos."));
b.push(caja("Implicación para el diseño de la ayuda",[
  "Un programa que solo repare edificios atenderá al "+num(D.wwb.inutil)+" % de los casos y dejará sin resolver la situación del "+Math.round(D.noop_norm-D.wwb.inutil)+" % restante, que necesita inventarios, clientes, proveedores y liquidez. La reparación física es condición necesaria pero no suficiente."]));

b.push(H2("4.2 Exposición económica"));
b.push(P("Las pérdidas se declaran en rangos, de modo que solo puede acotarse un intervalo. Sumando el extremo inferior de cada rango cerrado, los "+n(D.econ.base)+" establecimientos que responden acumulan al menos "+n(D.econ.lo)+" millones de pesos. Sumando el extremo superior de esos mismos rangos, "+n(D.econ.hi)+" millones. A eso se añaden "+n(D.econ.ab)+" establecimientos que declaran «más de $100 millones» sin límite superior."));
b.push(Rich([["Cota inferior defendible: ","b"],[n(D.econ.min)+" millones de pesos","b"],
  [" —del orden de "+Math.round(D.econ.min/1000)+" mil millones—, sumando el piso de cada rango cerrado más $100 millones por cada uno de los "+n(D.econ.ab)+" reportes del tramo abierto. La cifra real es mayor y no puede estimarse con precisión sin pedir el monto exacto.",""]]));
b.push(caja("Corrección respecto de la versión anterior de este informe",[
  "La edición anterior publicó una cota inferior de 184.480 millones. Esa cifra contaba dos veces el tramo abierto: sumaba $100 millones dentro del piso de cada rango y volvía a sumarlos aparte. La cota corregida, sobre la base ya depurada, es de "+n(D.econ.min)+" millones.",
  "La diferencia no se debe a la deduplicación —que explica menos del 4 %— sino al doble conteo. Se deja constancia porque la cifra anterior circuló."],ROJO));
b.push(P("Para dimensionarla: las estimaciones macroeconómicas iniciales situaron el impacto del sismo entre el "+num(D.macro.pib_min)+" % y el "+num(D.macro.pib_max)+" % del PIB nacional, es decir entre US$"+n(D.macro.usd_min)+" y US$"+n(D.macro.usd_max)+" millones. Lo declarado en esta base es una fracción de ese total, y solo del Valle del Cauca."));

b.push(H2("4.3 Empleo comprometido"));
b.push(P("El "+pc(D.empleo.pct)+" de los "+n(D.empl.base)+" establecimientos que informan empleo reportan al menos un puesto en riesgo. Convertidos los rangos a intervalos, la exposición está entre "+n(D.empleo.lo)+" y "+n(D.empleo.hi)+" empleos, más "+n(D.empleo.ab)+" establecimientos que declaran «más de 50» sin techo."));
b.push(P("La concentración en empresas pequeñas explica la forma de la distribución: el "+pc(100*EM["Entre 1 y 5"]/D.empl.base)+" reporta entre uno y cinco empleos en riesgo. Son pocos puestos por establecimiento y muchísimos establecimientos."));

// ══════════ 5. GEOESTADÍSTICA DESCRIPTIVA ══════════
b.push(salto());
b.push(H1("5. Geoestadística descriptiva"));
b.push(P("Esta sección describe cómo se reparte cada indicador entre los 42 municipios, en qué orden quedan y cómo se relacionan entre sí. No busca conglomerados espaciales: con 42 unidades y bases de respuesta muy dispares, las pruebas de autocorrelación resultaron poco informativas y se retiraron. Lo que sí puede decirse con solidez es cuánta dispersión hay, quién está en cada extremo y qué indicadores se mueven juntos."));

b.push(H2("5.1 Cuánto varían los municipios"));
b.push(img("f1_histogramas.png",610,370));
b.push(Cap("Figura 3. Distribución de cada indicador entre los 42 municipios."));
b.push(esp(40));
b.push(tabla(["Indicador","Mín","Q1","Mediana","Q3","Máx","CV"],
  Object.entries(DE).map(([k,v])=>[k,num(v.min),num(v.q1),num(v.mediana),num(v.q3),num(v.max),num(v.cv)]),
  [3000,900,900,1100,900,900,1660]));
b.push(Fu("Cada fila describe la distribución del indicador ENTRE municipios, no entre establecimientos. CV = coeficiente de variación (desviación / media): a mayor CV, más desigual es el reparto territorial."));
b.push(Bul("El reparto más desigual es el de pérdidas altas (CV "+num(DE["Pérdidas superiores a $20 millones"].cv)+"). Va de "+num(DE["Pérdidas superiores a $20 millones"].min)+" % en "+tit(DE["Pérdidas superiores a $20 millones"].min_mun)+" a "+num(DE["Pérdidas superiores a $20 millones"].max)+" % en "+tit(DE["Pérdidas superiores a $20 millones"].max_mun)+": una diferencia de casi cuarenta puntos entre municipios del mismo departamento."));
b.push(Bul("El más parejo es el de empleo en riesgo (CV "+num(DE["Con algún empleo en riesgo"].cv)+"). Incluso el municipio con menor exposición, "+tit(DE["Con algún empleo en riesgo"].min_mun)+", tiene "+num(DE["Con algún empleo en riesgo"].min)+" % de sus establecimientos con al menos un puesto comprometido. El riesgo de empleo no distingue territorio."));
b.push(Bul("La mediana de afectación crítica o grave es "+num(DE["Afectación crítica o grave"].mediana)+" %: en la mitad de los municipios del Valle, uno de cada dos establecimientos que reportó está en los dos niveles más altos."));

b.push(H2("5.2 Rankings por indicador"));
b.push(P("El orden cambia según lo que se mida, y esa es la razón para publicar los cuatro rankings en vez de uno solo."));
b.push(img("f4_rankings.png",640,300));
b.push(Cap("Figura 4. Doce primeros municipios en cada indicador."));
b.push(Fu("Las barras grises corresponden a municipios con menos de 60 respuestas válidas a esa pregunta: el porcentaje es poco estable y no debe leerse como equivalente al de un municipio con base grande."));
// El puesto de cada líder en los demás indicadores se calcula, no se afirma:
// escribirlo a mano fue la fuente de un error en la revisión anterior.
const puesto=(m,c)=>M.filter(x=>x[c]!==null&&x[c]!==undefined)
  .sort((a,z)=>z[c]-a[c]).findIndex(x=>x.municipio===m)+1;
const lider=(k,c)=>{const m=DE[k].max_mun;return {m,t:tit(m),
  sev:puesto(m,"pct_severo"),noop:puesto(m,"pct_no_opera"),
  perd:puesto(m,"pct_perd_alta"),emp:puesto(m,"pct_empleo")};};
const L1=lider("Afectación crítica o grave"),L2=lider("Pérdidas superiores a $20 millones"),
      L3=lider("No puede operar");
b.push(P(L1.t+" encabeza severidad con "+num(DE["Afectación crítica o grave"].max)+" % sobre "+n(DE["Afectación crítica o grave"].top5[0][2])+" reportes, pero cae al puesto "+L1.noop+" de 42 en parálisis. "+L2.t+" encabeza pérdidas con "+num(DE["Pérdidas superiores a $20 millones"].max)+" % y es el puesto "+L2.noop+" en parálisis: casi el último. "+L3.t+" encabeza parálisis con "+num(DE["No puede operar"].max)+" % y es el "+L3.sev+" en severidad. Ningún municipio encabeza los cuatro."));
b.push(Rich([["Advertencia sobre el ranking de empleo. ","b"],
  ["Los tres primeros puestos los ocupan municipios con menos de 45 respuestas válidas. Ese ranking en particular está dominado por bases pequeñas y debe leerse con la reserva que indica la figura, no como evidencia de que allí el empleo esté más comprometido que en el resto.",""]]));

b.push(H2("5.3 Cómo se relacionan los indicadores"));
b.push(img("f2_dispersion.png",620,278));
b.push(Cap("Figura 5. Severidad, parálisis y pérdidas. El tamaño del punto es el número de reportes; el color, el índice ajustado."));
b.push(esp(40));
b.push(img("f5_correlacion.png",340,287));
b.push(Cap("Figura 6. Correlación de Spearman entre los cuatro indicadores."));
b.push(Fu("Se usa Spearman y no Pearson porque las variables de origen son ordinales y la relación no tiene por qué ser lineal. Un coeficiente de 1 significa que los dos rankings coinciden exactamente."));
b.push(P("La estructura que aparece es clara y tiene consecuencias operativas:"));
b.push(Bul("Severidad y pérdidas altas van juntas (ρ = "+num(cor("pct_severo","pct_perd_alta").toFixed(2))+"). El municipio donde más establecimientos se declaran críticos es también donde más se declaran pérdidas grandes. Coherencia interna esperable, y útil como control de calidad de la base."));
b.push(Bul("Parálisis y pérdidas altas casi no se relacionan (ρ = "+num(cor("pct_no_opera","pct_perd_alta").toFixed(2))+"). Este es el hallazgo menos obvio. Hay municipios con muchos establecimientos cerrados y pérdidas declaradas modestas —negocios pequeños que no pueden abrir—, y municipios operando con pérdidas patrimoniales enormes —empresas con activos dañados que siguen funcionando."));
b.push(Bul("Parálisis y empleo en riesgo sí se acompañan (ρ = "+num(cor("pct_no_opera","pct_empleo").toFixed(2))+"): donde el negocio no abre, el puesto de trabajo se pone en juego."));
b.push(caja("Por qué esto cambia el diseño del programa",[
  "Si parálisis y pérdidas midieran lo mismo, un solo instrumento —dimensionado por monto de pérdida— alcanzaría. Con ρ = "+num(cor("pct_no_opera","pct_perd_alta").toFixed(2))+" no alcanza.",
  "Un municipio paralizado con pérdidas bajas necesita liquidez inmediata y pequeña, muchas veces. Un municipio operando con pérdidas altas necesita reposición de activos, pocas veces y de monto grande. Asignar por una sola variable dejará a la mitad mal atendida."]));

b.push(H2("5.4 El volumen de reportes no explica la intensidad"));
b.push(P("Una objeción razonable al ranking es que podría estar midiendo dónde llegó mejor el registro y no dónde golpeó más el sismo. Los datos no la sostienen."));
b.push(img("f3_cobertura.png",620,335));
b.push(Cap("Figura 7. Número de reportes frente a porcentaje de afectación crítica o grave."));
b.push(P("La correlación entre el número de reportes de un municipio y su porcentaje de establecimientos críticos es de "+num(cor("pct_severo","n").toFixed(2))+": débil. Cartago, con "+n(mun("CARTAGO").n)+" reportes, tiene "+num(mun("CARTAGO").pct_severo)+" % de severidad; La Cumbre, con "+n(mun("LA CUMBRE").n)+", tiene "+num(mun("LA CUMBRE").pct_severo)+" %. Municipios de tamaño de muestra parecido ocupan posiciones opuestas del eje vertical, que es exactamente lo que debería ocurrir si el indicador mide afectación y no cobertura."));

// ══════════ 6. MUNICIPIOS Y MAPAS ══════════
b.push(salto());
b.push(H1("6. Los municipios más afectados"));
b.push(img("g3_ranking.png",600,363));
b.push(Cap("Figura 8. Quince municipios con mayor índice de afectación económica ajustado."));
b.push(esp(40));
b.push(tabla(["#","Municipio","Índice","n","% crítico o grave","% no opera","% pérdidas > $20M"],
  M.slice(0,15).map((r,i)=>[String(i+1),tit(r.municipio),num(r.IAE_aj),n(r.n),
    num(r.pct_severo)+" %",num(r.pct_no_opera)+" %",num(r.pct_perd_alta)+" %"]),
  [500,2100,1000,900,1700,1500,1660],{numDesde:2}));
b.push(Fu("Índice ajustado por tamaño de muestra. «n» es el número de establecimientos únicos que reportaron en el municipio."));
b.push(P(tit(M[0].municipio)+" encabeza el índice con una base sólida de "+n(M[0].n)+" reportes: combina "+num(M[0].pct_severo)+" % de severidad, "+num(M[0].pct_no_opera)+" % de parálisis y "+num(M[0].pct_perd_alta)+" % de pérdidas altas, alto en las tres dimensiones a la vez. Le siguen "+tit(M[1].municipio)+" y "+tit(M[2].municipio)+", con intensidades altas sobre universos pequeños que la contracción ya moderó."));
b.push(P("Cali merece lectura aparte: con "+n(D.cali.n)+" establecimientos —el "+num(D.dane.cob_cali)+" % de los "+n(D.dane.cali)+" negocios que el DANE le registra— aporta el mayor número absoluto de casos severos del departamento aunque su intensidad relativa no sea la más alta. En términos de personas atendidas, Cali sigue siendo el mayor problema del departamento."));

b.push(salto());
b.push(H1("7. Mapas por variable"));
b.push(P("Cada mapa rotula los 42 municipios con su nombre y su valor, de modo que puedan leerse sin recurrir a la tabla."));
b.push(img("m1_iae.png",545,645));
b.push(Cap("Figura 9. Índice de afectación económica ajustado, por municipio."));
b.push(salto());
b.push(img("m3_severo.png",545,645));
b.push(Cap("Figura 10. Establecimientos en nivel crítico o grave, por municipio."));
b.push(salto());
b.push(img("m2_nopera.png",545,645));
b.push(Cap("Figura 11. Establecimientos que no pueden operar, por municipio."));
b.push(P(tit(DE["No puede operar"].max_mun)+" ("+num(DE["No puede operar"].max)+" %), "+tit(DE["No puede operar"].top5[1][0])+" y "+tit(DE["No puede operar"].top5[2][0])+" superan el 45 % de establecimientos completamente paralizados, muy por encima del "+pc(100*C["No puede operar"]/D.cont.base)+" departamental. En el otro extremo, "+tit(DE["No puede operar"].min_mun)+" queda por debajo del 10 %."));
b.push(salto());
b.push(img("m4_perdidas.png",545,645));
b.push(Cap("Figura 12. Establecimientos con pérdidas superiores a $20 millones, por municipio."));
b.push(salto());
b.push(img("m5_empleo.png",545,645));
b.push(Cap("Figura 13. Establecimientos con algún empleo en riesgo, por municipio."));
b.push(P("Este último mapa es el más uniforme de los cinco, y esa uniformidad es el dato: el riesgo de empleo no se concentra en unos pocos municipios sino que atraviesa el departamento entero."));

// ══════════ 8. NECESIDADES ══════════
b.push(salto());
b.push(H1("8. Qué necesitan y qué instrumento prefieren"));
b.push(img("g2_necesidades.png",610,235));
b.push(Cap("Figura 14. Necesidad principal y apoyo financiero preferido, departamento frente a los diez municipios más afectados."));
b.push(esp(40));
b.push(tabla(["Principal necesidad","Menciones","% de los "+n(BN)+" que responden"],
  Object.entries(D.nec).filter(([k])=>k!=="Otro").map(([k,v])=>[k,n(v),pc(100*v/BN)])
    .concat([["Otro (texto libre)",n(D.nec["Otro"]),pc(100*D.nec["Otro"]/BN)]]),
  [4900,2200,2260]));
b.push(Fu("Selección múltiple: las menciones no suman establecimientos únicos. «Otro» agrupa respuestas de texto libre que no encajan en las cinco categorías del formulario."));
b.push(P("Capital de trabajo ("+n(D.nec["Capital de trabajo o insumos"])+" menciones) supera por poco a reparar instalaciones ("+n(D.nec["Reparar instalaciones o equipos"])+"), y "+n(D.nec["Recuperar clientes y ventas"])+" establecimientos piden explícitamente recuperar clientes y ventas. Es la misma señal de la sección 4.1 desde el lado de la demanda: el problema no termina cuando el local vuelve a abrir."));
b.push(esp(60));
b.push(tabla(["Apoyo financiero preferido","Menciones","% de los "+n(BA)+" que opinan"],
  Object.entries(D.apo).filter(([k])=>k!=="Otro").map(([k,v])=>[k,n(v),pc(100*v/BA)])
    .concat([["Otro (texto libre)",n(D.apo["Otro"]),pc(100*D.apo["Otro"]/BA)]]),
  [4900,2200,2260]));
b.push(Rich([["El crédito nuevo aparece en tercer lugar, muy por debajo del capital no reembolsable. ","b"],
  ["Un sector con la operación interrumpida y sin flujo de caja no percibe capacidad de asumir más deuda; ofrecer principalmente líneas de crédito puede producir baja colocación aunque las condiciones sean favorables.",""]]));

// ══════════ 9. CONTRASTE ══════════
b.push(H1("9. Contraste con fuentes externas"));
b.push(P("Los resultados de esta base se compararon con tres fuentes independientes para verificar si describen el mismo fenómeno."));
b.push(img("g5_contraste.png",600,229));
b.push(Cap("Figura 15. Comparación con la Cámara de Comercio de Cali y la Fundación WWB Colombia."));
b.push(H2("9.1 El tejido empresarial según el DANE"));
b.push(tabla(["Indicador","Valor","Fuente"],[
  ["Unidades económicas en el Valle",n(D.dane.unidades),"DANE · tercer departamento del país"],
  ["Establecimientos en Cali",n(D.dane.cali),"DANE · 43,5 por mil habitantes"],
  ["Municipio con menos unidades","Ulloa · "+n(D.dane.ulloa),"DANE"],
  ["Participación de microempresas",num(D.dane.micro)+" %","DANE"],
  ["Densidad empresarial","más de "+num(D.dane.dens)+" por mil habitantes","DANE · tercero tras Santander y Bogotá"],
],[3400,2500,3460],{textoFinal:true}));
b.push(P("Los "+n(D.n)+" establecimientos únicos de esta base representan el "+num(D.dane.cobertura)+" % del tejido empresarial del departamento, y en Cali el "+num(D.dane.cob_cali)+" %. Es una fracción, pero de un tamaño que permite inferencia razonable sobre el subconjunto que reportó."));
b.push(H2("9.2 La Cámara de Comercio de Cali y Confecámaras"));
b.push(P("La Línea de Afectación Empresarial reportó más de "+n(D.conf.empresas)+" empresas afectadas en las zonas consultadas. Para Cali informó "+num(D.conf.cali_sev)+" % con daños críticos y "+num(D.conf.cali_noop)+" % sin poder operar."));
b.push(P("Esta base arroja para Cali "+pc(D.cali.sev)+" en nivel crítico o grave —una coincidencia notable con el "+num(D.conf.cali_sev)+" % publicado— pero "+pc(D.cali.noop)+" sin poder operar, casi diez puntos por debajo del "+num(D.conf.cali_noop)+" % reportado."));
b.push(caja("Una hipótesis que conviene verificar, no afirmar",[
  "La diferencia en continuidad operativa podría reflejar recuperación: si la cifra externa corresponde a un corte de agosto y esta base cierra el 1 de septiembre, la caída del "+num(D.conf.cali_noop)+" % al "+num(D.cali.noop)+" % mediría establecimientos que volvieron a abrir.",
  "También podría deberse a universos distintos o a un momento de captura diferente dentro de cada registro. Con los datos disponibles no es posible distinguir entre ambas explicaciones; se recomienda pedir a la Cámara la fecha de corte exacta de su indicador."]));
b.push(H2("9.3 El diagnóstico de la Fundación WWB Colombia"));
b.push(P("El estudio más cercano en objeto es el de la Fundación WWB Colombia, realizado entre "+n(D.wwb.n)+" emprendedores de "+n(D.wwb.mun)+" municipios. Sus resultados coinciden en la dirección y la magnitud con los de esta base:"));
b.push(tabla(["Indicador","WWB Colombia","Esta base"],[
  ["No opera con normalidad",num(D.wwb.noop)+" %",pc(D.noop_norm)],
  ["Caída de ventas / reducción de clientes",num(D.wwb.ventas)+" %",pc(100*D.nec["Recuperar clientes y ventas"]/BN)+" lo pide como necesidad"],
  ["Local inutilizable",num(D.wwb.inutil)+" %","no se pregunta"],
  ["Prioridad: capital para el negocio",num(D.wwb.capital)+" %",pc(100*D.nec["Capital de trabajo o insumos"]/BN)],
],[3400,2700,3260],{textoFinal:true}));

// ══════════ 10. HOGARES ══════════
b.push(salto());
b.push(H1("10. El impacto llega al hogar"));
b.push(P("La pregunta por la afectación a los hogares no puede responderse con esta base, que solo observa establecimientos. Pero la evidencia disponible permite establecer el puente, y el puente es más corto de lo que suele suponerse."));
b.push(caja("El dato que conecta negocio y hogar",[
  "El "+num(D.wwb.vivienda)+" % de los micronegocios estudiados por la Fundación WWB Colombia desarrolla su actividad productiva DENTRO de la vivienda.",
  "La vivienda es también tienda, taller, cocina o salón. Un daño en la casa paraliza simultáneamente el techo y la fuente de ingresos, y recuperar el negocio depende de que primero sea posible volver a usar el inmueble de forma segura."],ROJO));
b.push(H2("10.1 Capacidad de las familias para cubrir gastos básicos"));
b.push(P("El deterioro de los negocios ya se trasladó a las finanzas familiares. Según el mismo estudio:"));
b.push(Bul("El "+num(D.wwb.hogares)+" % de los hogares tiene limitación alta o moderada para cubrir sus gastos básicos."));
b.push(Bul("Para el "+num(D.wwb.no_alcanza)+" %, el emprendimiento dejó de producir ingresos suficientes para lo esencial."));
b.push(Bul("Otro "+num(D.wwb.con_dificultad)+" % logra cubrirlos, pero reduciendo otros gastos."));
b.push(Bul("El "+num(D.wwb.alimento)+" % manifestó necesitar apoyo alimentario y el "+num(D.wwb.comedor)+" % ya accede a alimentos mediante ayudas o comedores comunitarios."));
b.push(Bul("El "+num(D.wwb.emocional)+" % de las personas encuestadas se declaró alterada o muy afectada emocionalmente."));
b.push(H2("10.2 Por qué importa el punto de partida"));
b.push(P("El Valle del Cauca llegaba al sismo con la menor pobreza monetaria de la región Pacífica: "+num(D.dane.pobreza)+" % frente al "+num(D.dane.pobreza_nac)+" % nacional, con pobreza extrema en "+num(D.dane.pobreza_ext)+" % y Cali en "+num(D.dane.pobreza_cali)+" %. El departamento venía además de una reducción de 3,9 puntos porcentuales en un año."));
b.push(Rich([["Ese avance es precisamente lo que está en riesgo. ","b"],
  ["Cuando el "+num(D.wwb.hogares)+" % de los hogares que dependen de un micronegocio reporta dificultad para cubrir gastos básicos, la pregunta relevante no es cuántos cayeron bajo la línea de pobreza —que aún no puede medirse— sino cuánto del descenso reciente puede revertirse si la recuperación productiva se demora.",""]]));
b.push(P("El segmento es además el más vulnerable por composición: las microempresas representan el "+num(D.macro.micro)+" % del tejido empresarial de los cinco departamentos más afectados, y son las que tienen menor capacidad para absorber pérdidas, sostener el empleo y reactivar operaciones. En las zonas más golpeadas del país se estimaron "+n(D.macro.empresas)+" empresas y "+n(D.macro.empleos)+" empleos expuestos."));
b.push(H2("10.3 Qué implica para el diseño de la intervención"));
b.push(Bul("La adecuación de la vivienda es también recuperación productiva cuando el negocio opera dentro de ella. Separar los programas de vivienda y de reactivación económica deja fuera al "+num(D.wwb.vivienda)+" % de los micronegocios."));
b.push(Bul("El acompañamiento psicosocial no es un complemento blando: fue la segunda necesidad más citada en el estudio de la WWB ("+num(D.wwb.psico)+" %), por encima de la adecuación de vivienda."));
b.push(Bul("La ayuda alimentaria y la reactivación productiva se solapan en el tiempo. Mientras el "+num(D.wwb.alimento)+" % requiere apoyo alimentario, tratar la emergencia humanitaria y la recuperación económica como fases sucesivas deja un vacío."));

// ══════════ 11. LIMITACIONES ══════════
b.push(H1("11. Limitaciones"));
b.push(Bul("El universo es autoseleccionado. Solo aparecen quienes conocieron el registro y decidieron reportar; la ausencia de un establecimiento no significa que esté indemne, y el "+num(D.dane.cobertura)+" % de cobertura sobre el tejido empresarial no constituye una muestra probabilística."));
b.push(Bul("La depuración de duplicados es conservadora por diseño. Prefiere dejar pasar un duplicado antes que fusionar dos negocios distintos, de modo que el "+num(DU.pct)+" % detectado es un piso: puede haber doble notificación con datos de contacto diferentes que este método no ve."));
b.push(Bul("«Nivel de afectación» lo calcula la plataforma con una fórmula que este informe no conoce. Se usa por su coherencia observada con la continuidad operativa, pero no pudo auditarse."));
b.push(Bul("Pérdidas y empleos se declaran en rangos: solo pueden acotarse intervalos, nunca cifras puntuales."));
b.push(Bul("Los pesos del índice son una decisión de diseño. Con otros pesos el orden de los primeros puestos cambia poco, pero el de la mitad de la tabla sí."));
b.push(Bul("Los rankings por indicador incluyen municipios con bases muy pequeñas, señalados en gris en la figura 4. Un porcentaje calculado sobre 20 respuestas no es comparable con uno calculado sobre 5.000."));
b.push(Bul("El análisis usa el municipio como unidad. Un municipio grande como Buenaventura o Cali puede contener situaciones internas muy distintas que el promedio municipal esconde."));
b.push(Bul("No se dispone del universo empresarial por municipio —solo el total departamental y el de Cali—, de modo que no puede calcularse una tasa de afectación sobre el total de cada municipio."));
b.push(Bul("Las cifras de hogares provienen de un estudio externo con universo y metodología propios. No son atribuibles a los establecimientos de esta base; se citan como contexto y así deben leerse."));

// ══════════ 12. RECOMENDACIONES ══════════
b.push(H1("12. Recomendaciones"));
b.push(Bul("Validar el formulario contra reportes previos del mismo teléfono, correo o documento. Es la corrección más barata y evita en origen el "+num(DU.pct)+" % de doble notificación que hoy hay que depurar a posteriori."));
b.push(Bul("Depurar duplicados antes de publicar cualquier cifra de esta base. La diferencia es de poco más de un punto porcentual en el agregado departamental, pero llega al "+num(DU.por_municipio[0].pct)+" % en algunos municipios."));
b.push(Bul("Diseñar el instrumento principal como capital no reembolsable, no como crédito. Es la preferencia declarada por el "+pc(100*D.apo["Capital semilla (no reembolsable)"]/BA)+" de quienes opinan, y coincide con la incapacidad de asumir deuda de un sector paralizado."));
b.push(Bul("Separar dos instrumentos, no uno. La correlación de "+num(cor("pct_no_opera","pct_perd_alta").toFixed(2))+" entre parálisis y pérdidas altas indica que son problemas distintos: liquidez rápida y pequeña para lo primero, reposición de activos para lo segundo."));
b.push(Bul("Atender simultáneamente reparación física y capital de trabajo. Las dos necesidades están separadas por "+n(Math.abs(D.nec["Capital de trabajo o insumos"]-D.nec["Reparar instalaciones o equipos"]))+" menciones: no hay una prioridad clara y tratarlas como secuenciales dejará a la mitad esperando."));
b.push(Bul("Priorizar la primera ola en "+M.slice(0,6).map(x=>tit(x.municipio)).join(", ")+", que combinan índice alto con base de reportes suficiente para sostener la estimación."));
b.push(Bul("Integrar vivienda y reactivación en un solo trámite para los micronegocios domiciliarios, que son siete de cada diez."));
b.push(Bul("Incorporar acompañamiento psicosocial al paquete de recuperación económica, con base en la evidencia de la Fundación WWB."));
b.push(Bul("Solicitar al DANE el desagregado municipal de unidades económicas para convertir las cifras absolutas en tasas de afectación, que es la métrica que permitiría comparar municipios de distinto tamaño."));

// ══════════ ANEXO ══════════
b.push(salto());
b.push(H1("Anexo. Los 42 municipios"));
b.push(P("Ordenados por índice ajustado. «n» es el número de establecimientos únicos que reportaron; «w» es el peso que conserva el municipio tras la contracción (1 = sin corrección)."));
b.push(tabla(["#","Municipio","Índ. aj.","Índ. bruto","w","n","% crít./grave","% no opera"],
  M.map((r,i)=>[String(i+1),tit(r.municipio),num(r.IAE_aj),num(r.IAE),
    num(r.peso_w),n(r.n),num(r.pct_severo)+" %",num(r.pct_no_opera)+" %"]),
  [450,2000,1000,1050,750,750,1650,1710],{numDesde:2}));
b.push(Fu("Fuente: elaboración propia sobre reportes_emergencia_2026-09-01.xlsx ("+n(DU.n0)+" reportes recibidos, "+n(D.n)+" establecimientos únicos tras depurar, seis variables no sensibles). Cartografía: Marco Geoestadístico Nacional del DANE. Corte: 1 de septiembre de 2026."));

const doc=new Document({creator:"Observatorio de Turismo · Valle del Cauca",
  title:"Impacto económico del terremoto en el tejido empresarial",
  description:"Análisis geoestadístico descriptivo de "+n(D.n)+" establecimientos únicos · Valle del Cauca · 2026",
  numbering:{config:[{reference:"v",levels:[{level:0,format:LevelFormat.BULLET,text:"•",
    alignment:AlignmentType.LEFT,style:{paragraph:{indent:{left:convertInchesToTwip(0.28),
    hanging:convertInchesToTwip(0.18)}}}}]}]},
  sections:[{properties:{page:{margin:{top:1080,bottom:1080,left:1080,right:1080}}},children:b}]});
Packer.toBuffer(doc).then(x=>{fs.writeFileSync("Informe_impacto_economico_2026-09-01.docx",x);
  console.log("generado:",(x.length/1024).toFixed(0),"KB");});

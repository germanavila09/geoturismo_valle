const fs=require('fs'); const d=require('docx');
const {Document,Packer,Paragraph,TextRun,HeadingLevel,Table,TableRow,TableCell,
 WidthType,ShadingType,AlignmentType,BorderStyle,ImageRun,PageBreak,LevelFormat,
 convertInchesToTwip}=d;
const D=JSON.parse(fs.readFileSync('datos2.json','utf8'));
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
const S=D.sev.c, C=D.cont.c, PE=D.perd.c, EM=D.empl.c;
const sev=S["Crítica"]+S["Grave"], pctSev=100*sev/D.sev.base;

// PORTADA
b.push(new Paragraph({spacing:{after:60},children:[new TextRun({
  text:"OBSERVATORIO DE TURISMO · VALLE DEL CAUCA",size:17,bold:true,color:GRIS,font:"Calibri",characterSpacing:24})]}));
b.push(new Paragraph({spacing:{after:80},children:[new TextRun({
  text:"Impacto económico del terremoto en el tejido empresarial",size:40,bold:true,color:AZUL,font:"Calibri"})]}));
b.push(new Paragraph({spacing:{after:260},border:{bottom:{style:BorderStyle.SINGLE,size:12,color:ROJO}},
  children:[new TextRun({text:"Análisis geoestadístico de "+n(D.n)+" establecimientos en los 42 municipios del Valle del Cauca",
  size:24,color:GRIS,font:"Calibri"})]}));
b.push(ficha([
  ["Corte de información","1 de septiembre de 2026 · sismo del 10 de agosto de 2026"],
  ["Universo","todos los sectores económicos · "+n(D.n)+" establecimientos"],
  ["Variables analizadas","continuidad operativa, pérdidas económicas, empleos en riesgo, principal necesidad, apoyo financiero y nivel de afectación"],
  ["Datos sensibles","ninguno. No se procesan nombres, documentos, teléfonos, correos, NIT ni direcciones"],
  ["Método espacial","I de Moran global y local · contigüidad tipo reina · 1.999 permutaciones"],
  ["Contraste externo","DANE, Fundación WWB Colombia, Cámara de Comercio de Cali y Confecámaras"],
],[2300,7060]));
b.push(esp(240));
b.push(caja("Los tres resultados que ordenan la decisión",[
  "1. La parálisis es mayor que el daño físico. "+pc(D.noop_norm)+" de los establecimientos no opera con normalidad, pero solo el 11 % de los locales fue declarado inutilizable según el estudio de la Fundación WWB. Un negocio en pie puede haber perdido su capacidad de vender.",
  "2. La afectación NO forma conglomerados en el territorio. Seis de siete pruebas de autocorrelación espacial no encuentran agrupamiento significativo: no hay corredores de daño económico que permitan una respuesta por zonas. Hay que ir municipio por municipio.",
  "3. El golpe llega al hogar. El "+num(D.wwb.vivienda)+" % de los micronegocios opera dentro de la vivienda y el "+num(D.wwb.hogares)+" % de esos hogares ya tiene dificultad para cubrir gastos básicos. Reparar el negocio y reparar la casa son el mismo problema.",
],ROJO));

// 1 RESUMEN
b.push(H1("1. Resumen ejecutivo"));
b.push(P("Este informe analiza la afectación económica declarada por "+n(D.n)+" establecimientos de todos los sectores en los 42 municipios del Valle del Cauca, sobre seis variables de operación y necesidad. No utiliza ningún dato que identifique a una persona o a una empresa."));
b.push(P("Los "+n(D.n)+" establecimientos equivalen al "+num(D.dane.cobertura)+" % de las "+n(D.dane.unidades)+" unidades económicas que el DANE registra en el departamento. La cifra no mide la afectación total del Valle: mide a quienes conocieron el registro y decidieron reportar."));
b.push(H2("Magnitud"));
b.push(Bul(n(sev)+" establecimientos ("+pc(pctSev)+") están en nivel crítico o grave: "+n(S["Crítica"])+" críticos y "+n(S["Grave"])+" graves."));
b.push(Bul(pc(D.noop_norm)+" no opera con normalidad. De los "+n(D.cont.base)+" que responden, "+n(C["No puede operar"])+" ("+pc(100*C["No puede operar"]/D.cont.base)+") no pueden operar en absoluto."));
b.push(Bul("Las pérdidas declaradas suman al menos "+n(D.econ.min)+" millones de pesos —unos 184 mil millones—, y es un piso: "+n(D.econ.ab)+" establecimientos declaran «más de $100 millones» sin techo."));
b.push(Bul("Entre "+n(D.empleo.lo)+" y "+n(D.empleo.hi)+" empleos están comprometidos. El "+pc(D.empleo.pct)+" de los "+n(D.empl.base)+" que informan tienen al menos un puesto en riesgo."));
b.push(Bul("La necesidad más citada es capital de trabajo ("+n(D.nec["Capital de trabajo o insumos"])+"), apenas por encima de reparar instalaciones ("+n(D.nec["Reparar instalaciones o equipos"])+"). La crisis es de liquidez tanto como de infraestructura."));
b.push(H2("Territorio"));
b.push(Bul("Los diez municipios con mayor índice de afectación son "+D.top10.slice(0,5).map(tit).join(", ")+", "+D.top10.slice(5).map(tit).join(", ")+"."));
b.push(Bul("El índice no muestra agrupación espacial robusta (I de Moran ajustado = "+num(D.moran_aj.I)+", p = "+num(D.moran_aj.p.toFixed(3))+"). La afectación está dispersa por el departamento."));
b.push(Bul("Solo dos municipios forman conglomerado estadísticamente significativo, y son de afectación BAJA rodeada de afectación baja: El Cerrito y Pradera, en el corredor sur."));

// 2 METODO
b.push(H1("2. Alcance, variables y tratamiento de datos"));
b.push(H2("2.1 Las seis variables y su base de respuesta"));
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
b.push(H2("2.2 Datos sensibles excluidos"));
b.push(P("El archivo fuente contiene nombre completo, documento de identidad, teléfono, correo electrónico, NIT, dirección y barrio. Ninguno de esos campos entra en este análisis: no se leen, no se agregan y no aparecen en ninguna salida. El procesamiento se limita a las seis variables de la sección anterior más el municipio, que es la unidad geográfica."));
b.push(P("La restricción no es solo metodológica. En la revisión anterior de esta misma base se detectó que 1.576 registros contienen datos personales sin autorización verificable bajo la Ley 1581 de 2012. Trabajar solo con agregados evita propagar ese problema."));
b.push(H2("2.3 El índice de afectación económica"));
b.push(P("Para comparar municipios con una sola cifra se construye un índice que combina las cuatro variables ordinales. Cada respuesta se convierte a una escala de 0 a 1 —de «sin afectación» a «lo peor declarable»— y se promedia con estos pesos:"));
b.push(esp(60));
b.push(tabla(["Componente","Peso","Justificación"],[
  ["Nivel de afectación","0,30","Síntesis que la plataforma calcula con todas las respuestas"],
  ["Continuidad operativa","0,30","Mide si el negocio produce ingresos hoy"],
  ["Pérdidas económicas","0,25","Magnitud del daño patrimonial"],
  ["Empleos en riesgo","0,15","Menor peso: fuerte sesgo al tamaño de la empresa"],
],[2600,1100,5660]));
b.push(Fu("Los pesos son una decisión de diseño, no un resultado empírico. Se declaran para que puedan discutirse y modificarse."));

b.push(H2("2.4 Corrección por tamaño de muestra"));
b.push(P("El índice crudo premiaba a los municipios con pocos reportes: Trujillo encabezaba el ranking con 49 establecimientos, porque basta que unos pocos declaren lo peor para que su promedio se dispare, mientras Cali con 6.251 no puede moverse tanto."));
b.push(P("Se aplicó contracción bayesiana empírica hacia la media departamental, con peso proporcional a la información que aporta cada municipio: w = τ² / (τ² + σ²/n). Un municipio con muchos reportes conserva su valor; uno con pocos se acerca al promedio, que es la mejor apuesta cuando su evidencia propia es débil."));
b.push(Rich([["El resultado tranquiliza: ","b"],["los pesos resultantes van de 0,81 a 0,998, de modo que la corrección apenas altera el orden. El ranking es robusto al tamaño de muestra, y la preocupación inicial resultó menor de lo temido. Se publican las dos versiones en el anexo.",""]]));

// 3 MAGNITUD
b.push(H1("3. Magnitud de la afectación en el departamento"));
b.push(img("g1_variables.png",600,395));
b.push(Cap("Figura 1. Las cuatro variables ordinales sobre los "+n(D.n)+" establecimientos."));
b.push(Fu("Cada panel declara su base de respuesta. «Nivel de afectación» es un campo derivado que calcula la plataforma; los otros tres son respuestas directas."));

b.push(H2("3.1 La parálisis excede al daño físico"));
b.push(P("De los "+n(D.cont.base)+" establecimientos que informan continuidad, "+n(C["No puede operar"])+" ("+pc(100*C["No puede operar"]/D.cont.base)+") no pueden operar y "+n(C["Sí, pero parcialmente"])+" ("+pc(100*C["Sí, pero parcialmente"]/D.cont.base)+") lo hacen parcialmente. En conjunto, "+pc(D.noop_norm)+" no opera con normalidad."));
b.push(P("El contraste con el daño estructural es el hallazgo central. El diagnóstico de la Fundación WWB Colombia entre 4.000 emprendedores de 147 municipios encontró que solo el "+num(D.wwb.inutil)+" % de los locales fue considerado inutilizable, mientras el "+num(D.wwb.noop)+" % de los negocios no funcionaba con normalidad. La distancia entre ambas cifras —más de sesenta puntos— mide algo que ningún censo de edificaciones capta: negocios que siguen en pie y han perdido la capacidad de producir, atender clientes o generar ingresos."));
b.push(caja("Implicación para el diseño de la ayuda",[
  "Un programa que solo repare edificios atenderá al 11 % de los casos y dejará sin resolver la situación del 65 % restante, que necesita inventarios, clientes, proveedores y liquidez. La reparación física es condición necesaria pero no suficiente."]));

b.push(H2("3.2 Exposición económica"));
b.push(P("Las pérdidas se declaran en rangos, de modo que solo puede acotarse un intervalo. Sumando el extremo inferior de cada rango, los "+n(D.econ.base)+" establecimientos que responden acumulan al menos "+n(D.econ.lo)+" millones de pesos. Sumando el extremo superior de los rangos cerrados, "+n(D.econ.hi)+" millones. A eso se añaden "+n(D.econ.ab)+" establecimientos que declaran «más de $100 millones» sin límite superior."));
b.push(Rich([["Cota inferior defendible: ","b"],[n(D.econ.min)+" millones de pesos","b"],
  [" —del orden de 184 mil millones—, considerando el piso de cada rango más el mínimo del rango abierto. La cifra real es mayor y no puede estimarse con precisión sin pedir el monto exacto.",""]]));
b.push(P("Para dimensionarla: las estimaciones macroeconómicas iniciales situaron el impacto del sismo entre el "+num(D.macro.pib_min)+" % y el "+num(D.macro.pib_max)+" % del PIB nacional, es decir entre US$"+n(D.macro.usd_min)+" y US$"+n(D.macro.usd_max)+" millones. Lo declarado en esta base es una fracción de ese total, y solo del Valle del Cauca."));

b.push(H2("3.3 Empleo comprometido"));
b.push(P("El "+pc(D.empleo.pct)+" de los "+n(D.empl.base)+" establecimientos que informan empleo reportan al menos un puesto en riesgo. Convertidos los rangos a intervalos, la exposición está entre "+n(D.empleo.lo)+" y "+n(D.empleo.hi)+" empleos, más "+n(D.empleo.ab)+" establecimientos que declaran «más de 50» sin techo."));
b.push(P("La concentración en empresas pequeñas explica la forma de la distribución: el "+pc(100*EM["Entre 1 y 5"]/D.empl.base)+" reporta entre uno y cinco empleos en riesgo. Son pocos puestos por establecimiento y muchísimos establecimientos."));

// 4 MUNICIPIOS
b.push(H1("4. Los municipios más afectados"));
b.push(img("g3_ranking.png",600,363));
b.push(Cap("Figura 2. Quince municipios con mayor índice de afectación económica ajustado."));
b.push(esp(40));
b.push(tabla(["#","Municipio","Índice","n","% crítico o grave","% no opera","% pérdidas > $20M"],
  D.mun.slice(0,15).map((r,i)=>[String(i+1),tit(r.municipio),num(r.IAE_aj),n(r.n),
    num(r.pct_severo)+" %",num(r.pct_no_opera)+" %",num(r.pct_perd_alta)+" %"]),
  [500,2100,1000,900,1700,1500,1660],{numDesde:2}));
b.push(Fu("Índice ajustado por tamaño de muestra. «n» es el número de establecimientos que reportaron en el municipio."));
b.push(P("Argelia, La Cumbre y Trujillo encabezan por intensidad sobre universos pequeños; Roldanillo, Sevilla y Cali combinan intensidad alta con volumen suficiente para que la estimación sea firme. Cali merece lectura aparte: con "+n(D.cali.n)+" establecimientos —el "+num(D.dane.cob_cali)+" % de los 99.208 negocios que el DANE le registra— aporta el mayor número absoluto de casos severos del departamento aunque su intensidad relativa no sea la más alta."));

b.push(img("m1_iae.png",560,663));
b.push(Cap("Figura 3. Índice de afectación económica por municipio."));
b.push(Fu("Cada municipio muestra su nombre y su valor del índice. Geometría: Marco Geoestadístico Nacional del DANE."));

b.push(H1("5. Análisis geoestadístico"));
b.push(P("Un ranking dice quién está peor. La autocorrelación espacial dice si lo que está peor forma conglomerados en el territorio o está disperso, y esa es una pregunta operativa: si el daño se agrupa, la respuesta puede organizarse por corredores; si está disperso, hay que ir municipio por municipio."));
b.push(H2("5.1 Método"));
b.push(P("Se calculó el I de Moran con matriz de vecindad por contigüidad tipo reina —dos municipios son vecinos si comparten al menos un punto de frontera—, con un promedio de "+num(D.vecinos)+" vecinos por municipio. La significancia se estimó por permutación aleatoria (1.999 repeticiones), sin suponer normalidad."));
b.push(H2("5.2 Resultado: la afectación está dispersa"));
b.push(tabla(["Variable","I de Moran","p","Conclusión"],
  Object.entries(D.moran).map(([k,v])=>[k,(v.I>=0?"+":"")+num(v.I.toFixed(4)),
    num(v.p.toFixed(3)),v.p<=0.05?"Agrupada":"Sin patrón espacial"]),
  [3000,1500,1100,3760],{textoFinal:true}));
b.push(Fu("Un I positivo indica tendencia a que municipios parecidos sean vecinos; el valor esperado bajo azar es cercano a −0,024 con 42 unidades."));
b.push(Rich([["Seis de las siete pruebas no encuentran agrupación significativa. ","b"],
  ["El índice crudo alcanza p = 0,045, justo en el límite, pero esa significancia no sobrevive a la corrección por tamaño de muestra: el índice ajustado da I = "+num(D.moran_aj.I)+" con p = "+num(D.moran_aj.p.toFixed(3))+". Todos los valores de I son positivos, lo que sugiere una tendencia débil al agrupamiento, pero ninguna es robusta.",""]]));
b.push(P("Un detalle refuerza la lectura: el número de reportes por municipio tampoco muestra patrón espacial (I = "+num(D.moran["n de reportes"].I.toFixed(4))+", p = "+num(D.moran["n de reportes"].p.toFixed(3))+"). La dispersión de la afectación no es un artefacto de dónde alcanzó a llegar el registro."));
b.push(img("g4_moran.png",440,345));
b.push(Cap("Figura 4. Diagrama de dispersión de Moran del índice ajustado."));

b.push(H2("5.3 Conglomerados locales"));
b.push(P("El estadístico local identifica solo dos municipios con agrupación significativa al 5 %, y ambos son de afectación baja rodeada de afectación baja:"));
b.push(tabla(["Municipio","Tipo","Índice","n","p"],
  D.lisa_sig.map(r=>[tit(r.municipio),r.cluster.replace("-","–"),num(r.IAE_aj),n(r.n),num(r.p_local.toFixed(3))]),
  [2300,2100,1300,1200,2460]));
b.push(P("El Cerrito y Pradera forman una bolsa de menor afectación en el corredor sur del departamento, cerca de Palmira y Candelaria, que también registran índices bajos. No aparece ningún conglomerado Alto–Alto significativo: los municipios más golpeados no son vecinos entre sí."));
b.push(img("m5_lisa.png",560,663));
b.push(Cap("Figura 5. Conglomerados espaciales del índice de afectación."));

b.push(H1("6. Mapas por variable"));
b.push(P("Las tres variables directas —sin construcción de índice— confirman el patrón disperso y permiten leer cada dimensión por separado."));
b.push(img("m2_nopera.png",560,663));
b.push(Cap("Figura 6. Establecimientos que no pueden operar, por municipio."));
b.push(P("Argelia ("+num(D.mun.find(x=>x.municipio==="ARGELIA").pct_no_opera)+" %), Trujillo y Bolívar superan el 45 % de establecimientos completamente paralizados, muy por encima del "+pc(100*C["No puede operar"]/D.cont.base)+" departamental. Guadalajara de Buga, Obando y El Cerrito están por debajo del 11 %."));
b.push(img("m3_severo.png",560,663));
b.push(Cap("Figura 7. Establecimientos en nivel crítico o grave, por municipio."));
b.push(img("m4_perdidas.png",560,663));
b.push(Cap("Figura 8. Establecimientos con pérdidas superiores a $20 millones, por municipio."));

b.push(H1("7. Qué necesitan y qué instrumento prefieren"));
b.push(img("g2_necesidades.png",600,237));
b.push(Cap("Figura 9. Necesidad principal y apoyo financiero preferido."));
b.push(tabla(["Principal necesidad","Menciones","% de los "+n(D.n)],
  Object.entries(D.nec).map(([k,v])=>[k,n(v),pc(100*v/D.n)]),[4900,2200,2260]));
b.push(Fu("Selección múltiple: las menciones no suman establecimientos únicos."));
b.push(P("Capital de trabajo ("+n(D.nec["Capital de trabajo o insumos"])+" menciones) supera por poco a reparar instalaciones ("+n(D.nec["Reparar instalaciones o equipos"])+"), y "+n(D.nec["Recuperar clientes y ventas"])+" establecimientos piden explícitamente recuperar clientes y ventas. Es la misma señal de la sección 3.1 desde el lado de la demanda: el problema no termina cuando el local vuelve a abrir."));
b.push(esp(60));
b.push(tabla(["Apoyo financiero preferido","Menciones","% de los "+n(D.bases["Apoyo financiero"])+" que opinan"],
  Object.entries(D.apo).map(([k,v])=>[k,n(v),pc(100*v/D.bases["Apoyo financiero"])]),[4900,2200,2260]));
b.push(Rich([["El crédito nuevo aparece en tercer lugar, muy por debajo del capital no reembolsable. ","b"],
  ["Un sector con la operación interrumpida y sin flujo de caja no percibe capacidad de asumir más deuda; ofrecer principalmente líneas de crédito puede producir baja colocación aunque las condiciones sean favorables.",""]]));

b.push(H1("8. Contraste con fuentes externas"));
b.push(P("Los resultados de esta base se compararon con tres fuentes independientes para verificar si describen el mismo fenómeno."));
b.push(img("g5_contraste.png",600,229));
b.push(Cap("Figura 10. Comparación con la Cámara de Comercio de Cali y la Fundación WWB Colombia."));
b.push(H2("8.1 El tejido empresarial según el DANE"));
b.push(tabla(["Indicador","Valor","Fuente"],[
  ["Unidades económicas en el Valle",n(D.dane.unidades),"DANE · tercer departamento del país"],
  ["Establecimientos en Cali",n(D.dane.cali),"DANE · 43,5 por mil habitantes"],
  ["Municipio con menos unidades","Ulloa · "+n(D.dane.ulloa),"DANE"],
  ["Participación de microempresas",num(D.dane.micro)+" %","DANE"],
  ["Densidad empresarial","más de "+num(D.dane.dens)+" por mil habitantes","DANE · tercero tras Santander y Bogotá"],
],[3400,2500,3460],{textoFinal:true}));
b.push(P("Los "+n(D.n)+" establecimientos de esta base representan el "+num(D.dane.cobertura)+" % del tejido empresarial del departamento, y en Cali el "+num(D.dane.cob_cali)+" %. Es una fracción, pero de un tamaño que permite inferencia razonable sobre el subconjunto que reportó."));
b.push(H2("8.2 La Cámara de Comercio de Cali y Confecámaras"));
b.push(P("La Línea de Afectación Empresarial reportó más de "+n(D.conf.empresas)+" empresas afectadas en las zonas consultadas. Para Cali informó "+num(D.conf.cali_sev)+" % con daños críticos y "+num(D.conf.cali_noop)+" % sin poder operar."));
b.push(P("Esta base arroja para Cali "+pc(D.cali.sev)+" en nivel crítico o grave —una coincidencia notable con el "+num(D.conf.cali_sev)+" % publicado— pero "+pc(D.cali.noop)+" sin poder operar, diez puntos por debajo del "+num(D.conf.cali_noop)+" % reportado."));
b.push(caja("Una hipótesis que conviene verificar, no afirmar",[
  "La diferencia en continuidad operativa podría reflejar recuperación: si la cifra externa corresponde a un corte de agosto y esta base cierra el 1 de septiembre, la caída del 39 % al 28,7 % mediría establecimientos que volvieron a abrir.",
  "También podría deberse a universos distintos o a un momento de captura diferente dentro de cada registro. Con los datos disponibles no es posible distinguir entre ambas explicaciones; se recomienda pedir a la Cámara la fecha de corte exacta de su indicador."]));
b.push(H2("8.3 El diagnóstico de la Fundación WWB Colombia"));
b.push(P("El estudio más cercano en objeto es el de la Fundación WWB Colombia, realizado entre "+n(D.wwb.n)+" emprendedores de "+n(D.wwb.mun)+" municipios. Sus resultados coinciden en la dirección y la magnitud con los de esta base:"));
b.push(tabla(["Indicador","WWB Colombia","Esta base"],[
  ["No opera con normalidad",num(D.wwb.noop)+" %",pc(D.noop_norm)],
  ["Caída de ventas / reducción de clientes",num(D.wwb.ventas)+" %",pc(100*D.nec["Recuperar clientes y ventas"]/D.n)+" lo pide como necesidad"],
  ["Local inutilizable",num(D.wwb.inutil)+" %","no se pregunta"],
  ["Prioridad: capital para el negocio",num(D.wwb.capital)+" %",pc(100*D.nec["Capital de trabajo o insumos"]/D.n)],
],[3400,2700,3260],{textoFinal:true}));

b.push(H1("9. El impacto llega al hogar"));
b.push(P("La pregunta por la afectación a los hogares no puede responderse con esta base, que solo observa establecimientos. Pero la evidencia disponible permite establecer el puente, y el puente es más corto de lo que suele suponerse."));
b.push(caja("El dato que conecta negocio y hogar",[
  "El "+num(D.wwb.vivienda)+" % de los micronegocios estudiados por la Fundación WWB Colombia desarrolla su actividad productiva DENTRO de la vivienda.",
  "La vivienda es también tienda, taller, cocina o salón. Un daño en la casa paraliza simultáneamente el techo y la fuente de ingresos, y recuperar el negocio depende de que primero sea posible volver a usar el inmueble de forma segura."],ROJO));
b.push(H2("9.1 Capacidad de las familias para cubrir gastos básicos"));
b.push(P("El deterioro de los negocios ya se trasladó a las finanzas familiares. Según el mismo estudio:"));
b.push(Bul("El "+num(D.wwb.hogares)+" % de los hogares tiene limitación alta o moderada para cubrir sus gastos básicos."));
b.push(Bul("Para el "+num(D.wwb.no_alcanza)+" %, el emprendimiento dejó de producir ingresos suficientes para lo esencial."));
b.push(Bul("Otro "+num(D.wwb.con_dificultad)+" % logra cubrirlos, pero reduciendo otros gastos."));
b.push(Bul("El "+num(D.wwb.alimento)+" % manifestó necesitar apoyo alimentario y el "+num(D.wwb.comedor)+" % ya accede a alimentos mediante ayudas o comedores comunitarios."));
b.push(Bul("El "+num(D.wwb.emocional)+" % de las personas encuestadas se declaró alterada o muy afectada emocionalmente."));
b.push(H2("9.2 Por qué importa el punto de partida"));
b.push(P("El Valle del Cauca llegaba al sismo con la menor pobreza monetaria de la región Pacífica: "+num(D.dane.pobreza)+" % frente al "+num(D.dane.pobreza_nac)+" % nacional, con pobreza extrema en "+num(D.dane.pobreza_ext)+" % y Cali en "+num(D.dane.pobreza_cali)+" %. El departamento venía además de una reducción de 3,9 puntos porcentuales en un año."));
b.push(Rich([["Ese avance es precisamente lo que está en riesgo. ","b"],
  ["Cuando el "+num(D.wwb.hogares)+" % de los hogares que dependen de un micronegocio reporta dificultad para cubrir gastos básicos, la pregunta relevante no es cuántos cayeron bajo la línea de pobreza —que aún no puede medirse— sino cuánto del descenso reciente puede revertirse si la recuperación productiva se demora.",""]]));
b.push(P("El segmento es además el más vulnerable por composición: las microempresas representan el "+num(D.macro.micro)+" % del tejido empresarial de los cinco departamentos más afectados, y son las que tienen menor capacidad para absorber pérdidas, sostener el empleo y reactivar operaciones. En las zonas más golpeadas del país se estimaron "+n(D.macro.empresas)+" empresas y "+n(D.macro.empleos)+" empleos expuestos."));
b.push(H2("9.3 Qué implica para el diseño de la intervención"));
b.push(P("Tres consecuencias se derivan de lo anterior, y ninguna es obvia desde una lectura solo empresarial:"));
b.push(Bul("La adecuación de la vivienda es también recuperación productiva cuando el negocio opera dentro de ella. Separar los programas de vivienda y de reactivación económica deja fuera al "+num(D.wwb.vivienda)+" % de los micronegocios."));
b.push(Bul("El acompañamiento psicosocial no es un complemento blando: fue la segunda necesidad más citada en el estudio de la WWB ("+num(D.wwb.psico)+" %), por encima de la adecuación de vivienda."));
b.push(Bul("La ayuda alimentaria y la reactivación productiva se solapan en el tiempo. Mientras el "+num(D.wwb.alimento)+" % requiere apoyo alimentario, tratar la emergencia humanitaria y la recuperación económica como fases sucesivas deja un vacío."));

b.push(H1("10. Limitaciones"));
b.push(Bul("El universo es autoseleccionado. Solo aparecen quienes conocieron el registro y decidieron reportar; la ausencia de un establecimiento no significa que esté indemne, y los "+num(D.dane.cobertura)+" % de cobertura sobre el tejido empresarial no son una muestra probabilística."));
b.push(Bul("«Nivel de afectación» lo calcula la plataforma con una fórmula que este informe no conoce. Se usa por su coherencia observada con la continuidad operativa, pero no pudo auditarse."));
b.push(Bul("Pérdidas y empleos se declaran en rangos: solo pueden acotarse intervalos, nunca cifras puntuales."));
b.push(Bul("Los pesos del índice son una decisión de diseño. Con otros pesos el orden de los primeros puestos cambia poco, pero el de la mitad de la tabla sí."));
b.push(Bul("El análisis espacial usa el municipio como unidad. Un municipio grande como Buenaventura o Cali puede contener situaciones internas muy distintas que el promedio municipal esconde."));
b.push(Bul("No se dispone del universo empresarial por municipio —solo el total departamental y el de Cali—, de modo que no puede calcularse una tasa de afectación sobre el total de cada municipio. Todas las cifras municipales son absolutas o proporciones internas."));
b.push(Bul("Las cifras de hogares provienen de un estudio externo con universo y metodología propios. No son atribuibles a los establecimientos de esta base; se citan como contexto y así deben leerse."));

b.push(H1("11. Recomendaciones"));
b.push(Bul("Diseñar el instrumento principal como capital no reembolsable, no como crédito. Es la preferencia declarada por el "+pc(100*D.apo["Capital semilla (no reembolsable)"]/D.bases["Apoyo financiero"])+" de quienes opinan, y coincide con la incapacidad de asumir deuda de un sector paralizado."));
b.push(Bul("Atender simultáneamente reparación física y capital de trabajo. Las dos necesidades están separadas por 48 menciones en un universo de 14.241: no hay una prioridad clara y tratarlas como secuenciales dejará a la mitad esperando."));
b.push(Bul("Organizar la respuesta municipio por municipio y no por corredores. El análisis espacial no encuentra conglomerados de daño económico que justifiquen una intervención zonal."));
b.push(Bul("Integrar vivienda y reactivación en un solo trámite para los micronegocios domiciliarios, que son siete de cada diez."));
b.push(Bul("Incorporar acompañamiento psicosocial al paquete de recuperación económica, con base en la evidencia de la Fundación WWB."));
b.push(Bul("Priorizar la primera ola en "+D.top10.slice(0,6).map(tit).join(", ")+", que combinan índice alto con base de reportes suficiente para sostener la estimación."));
b.push(Bul("Solicitar al DANE el desagregado municipal de unidades económicas para convertir las cifras absolutas en tasas de afectación, que es la métrica que permitiría comparar municipios de distinto tamaño."));

b.push(salto());
b.push(H1("Anexo. Los 42 municipios"));
b.push(P("Ordenados por índice ajustado. «n» es el número de establecimientos que reportaron; «w» es el peso que conserva el municipio tras la contracción (1 = sin corrección)."));
b.push(tabla(["#","Municipio","Índ. aj.","Índ. bruto","w","n","% crít./grave","% no opera"],
  D.mun.map((r,i)=>[String(i+1),tit(r.municipio),num(r.IAE_aj),num(r.IAE),
    num(r.peso_w),n(r.n),num(r.pct_severo)+" %",num(r.pct_no_opera)+" %"]),
  [450,2000,1000,1050,750,750,1650,1710],{numDesde:2}));
b.push(Fu("Fuente: elaboración propia sobre reportes_emergencia_2026-09-01.xlsx (14.241 establecimientos, seis variables no sensibles). Cartografía: Marco Geoestadístico Nacional del DANE. Corte: 1 de septiembre de 2026."));

const doc=new Document({creator:"Observatorio de Turismo · Valle del Cauca",
  title:"Impacto económico del terremoto en el tejido empresarial",
  description:"Análisis geoestadístico de 14.241 establecimientos · Valle del Cauca · 2026",
  numbering:{config:[{reference:"v",levels:[{level:0,format:LevelFormat.BULLET,text:"•",
    alignment:AlignmentType.LEFT,style:{paragraph:{indent:{left:convertInchesToTwip(0.28),
    hanging:convertInchesToTwip(0.18)}}}}]}]},
  sections:[{properties:{page:{margin:{top:1080,bottom:1080,left:1080,right:1080}}},children:b}]});
Packer.toBuffer(doc).then(x=>{fs.writeFileSync("Informe_impacto_economico_2026-09-01.docx",x);
  console.log("generado:",(x.length/1024).toFixed(0),"KB");});

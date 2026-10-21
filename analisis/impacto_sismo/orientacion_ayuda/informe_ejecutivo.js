const fs=require('fs'); const d=require('docx');
const {Document,Packer,Paragraph,TextRun,HeadingLevel,Table,TableRow,TableCell,
 WidthType,ShadingType,AlignmentType,BorderStyle,ImageRun,PageBreak,LevelFormat,
 convertInchesToTwip}=d;
const B=JSON.parse(fs.readFileSync('brecha.json','utf8'));
const D=JSON.parse(fs.readFileSync('datos3.json','utf8'));
const AZUL="1F3864",ROJO="B3261E",NARA="A8560A",GRIS="595959",CLARO="F2F5FA",BORDE="D5DBE5";
const n=x=>(x===null||x===undefined||Number.isNaN(x))?"—":Number(x).toLocaleString('es-CO');
const pc=x=>Number(x).toFixed(1).replace('.',',')+" %";
const num=x=>String(x).replace('.',',');
// Un decimal fijo: JSON entrega 4.0 y String() lo imprime como «4».
const un=x=>(x===null||x===undefined)?"—":Number(x).toFixed(1).replace('.',',');
const M=B.municipios, K=B.grd, A=B.ayuda;
const mun=k=>M.find(x=>x.municipio===k);
const MES=["enero","febrero","marzo","abril","mayo","junio","julio","agosto",
  "septiembre","octubre","noviembre","diciembre"];
const fecha=s=>{const [a,m,d]=s.slice(0,10).split('-').map(Number);
  return `${d} de ${MES[m-1]} de ${a}`;};
// Cuanto de lo despachado es subsistencia inmediata, calculado, no escrito a mano.
const SUB=["Aseo personal","Alimentos","Líquidos e hidratación","Bebé",
  "Aseo del hogar","Salud"];
const pctSub=Math.round(SUB.reduce((s,k)=>s+(A.composicion[k]||0),0));

const P=(t,o={})=>new Paragraph({spacing:{after:o.after??120,line:280},alignment:o.al,
  children:[new TextRun({text:t,size:o.size??19,bold:o.b,italics:o.i,color:o.c??"1A1A1A",font:"Calibri"})]});
const Rich=(runs,o={})=>new Paragraph({spacing:{after:o.after??120,line:280},
  children:runs.map(r=>new TextRun({text:r[0],bold:r[1]==='b',italics:r[1]==='i',
    size:o.size??19,color:r[2]??o.c??"1A1A1A",font:"Calibri"}))});
const H1=t=>new Paragraph({heading:HeadingLevel.HEADING_1,spacing:{before:250,after:110},
  keepNext:true,keepLines:true,children:[new TextRun({text:t,size:25,bold:true,color:AZUL,font:"Calibri"})]});
const H2=t=>new Paragraph({heading:HeadingLevel.HEADING_2,spacing:{before:170,after:80},
  keepNext:true,keepLines:true,children:[new TextRun({text:t,size:21,bold:true,color:AZUL,font:"Calibri"})]});
const Bul=t=>new Paragraph({numbering:{reference:"v",level:0},spacing:{after:60,line:270},
  children:[new TextRun({text:t,size:19,font:"Calibri",color:"1A1A1A"})]});
const BulR=runs=>new Paragraph({numbering:{reference:"v",level:0},spacing:{after:60,line:270},
  children:runs.map(r=>new TextRun({text:r[0],bold:r[1]==='b',size:19,font:"Calibri",color:"1A1A1A"}))});
const Fu=t=>new Paragraph({spacing:{after:150},
  children:[new TextRun({text:t,size:15,italics:true,color:GRIS,font:"Calibri"})]});
const Cap=t=>new Paragraph({spacing:{before:50,after:140},
  children:[new TextRun({text:t,size:16,bold:true,color:GRIS,font:"Calibri"})]});
const celda=(t,{b,al,w,sh,c,sz}={})=>new TableCell({width:{size:w,type:WidthType.DXA},
  shading:sh?{type:ShadingType.CLEAR,fill:sh,color:"auto"}:undefined,
  margins:{top:55,bottom:55,left:95,right:95},
  children:[new Paragraph({alignment:al??AlignmentType.LEFT,spacing:{after:0},
    children:[new TextRun({text:String(t),size:sz??15,bold:b,color:c??"1A1A1A",font:"Calibri"})]})]});
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
      margins:{top:130,bottom:130,left:200,right:160},
      children:[new Paragraph({spacing:{after:60},children:[new TextRun({text:t,bold:true,size:19,color:col,font:"Calibri"})]}),
        ...tx.map(x=>new Paragraph({spacing:{after:50,line:275},
          children:[new TextRun({text:x,size:18,color:"1A1A1A",font:"Calibri"})]}))]})]})]});
}
const img=(f,w,h)=>new Paragraph({alignment:AlignmentType.CENTER,spacing:{before:100,after:40},
  keepNext:true,children:[new ImageRun({type:"png",data:fs.readFileSync(f),transformation:{width:w,height:h}})]});
const salto=()=>new Paragraph({children:[new PageBreak()]});
const esp=(a=100)=>new Paragraph({spacing:{after:a},children:[]});

// ── priorizacion: necesidad, penalizada por el rezago en ayuda ───────────
const conPrio=M.map(m=>({...m, prio:m.r_nec + 0.5*Math.max(0,m.brecha)}))
  .sort((a,b)=>a.prio-b.prio);
const TOP=conPrio.slice(0,12);
const bva=mun("Buenaventura");
const totAfec=M.reduce((s,m)=>s+(m.poblacion_afectada||0),0);
const totTon=M.reduce((s,m)=>s+(m.toneladas||0),0);
const shAfecBva=100*bva.poblacion_afectada/totAfec, shTonBva=100*bva.toneladas/totTon;

const b=[];
// ══════════ PORTADA ══════════
b.push(new Paragraph({spacing:{after:50},children:[new TextRun({
  text:"OBSERVATORIO DE TURISMO · VALLE DEL CAUCA",size:16,bold:true,color:GRIS,font:"Calibri",characterSpacing:24})]}));
b.push(new Paragraph({spacing:{after:70},children:[new TextRun({
  text:"Dónde y en qué concentrar la ayuda",size:38,bold:true,color:AZUL,font:"Calibri"})]}));
b.push(new Paragraph({spacing:{after:200},border:{bottom:{style:BorderStyle.SINGLE,size:12,color:ROJO}},
  children:[new TextRun({text:"Informe ejecutivo · cruce de la afectación empresarial, la matriz de criticidad GRD y la Ruta de la Solidaridad",
  size:22,color:GRIS,font:"Calibri"})]}));
b.push(ficha([
  ["Pregunta que responde","a qué municipios dirigir el siguiente esfuerzo y con qué instrumento"],
  ["Fuentes cruzadas","observatorio de turismo ("+n(D.n)+" establecimientos únicos, 1 sep) · matriz GRD pública ("+K.municipios+" municipios, "+fecha(K.fecha_corte)+") · Ruta de la Solidaridad ("+A.despachos+" despachos, "+fecha(A.fecha_corte)+")"],
  ["Cobertura","41 municipios. Santiago de Cali va por canal propio y queda fuera del conteo municipal de ambas plataformas oficiales"],
  ["Datos sensibles","ninguno. Todas las cifras son agregados municipales"],
],[2100,7260]));
b.push(esp(180));
b.push(caja("Tres decisiones que se desprenden de los datos",[
  "1. DÓNDE · Cuatro municipios están en necesidad alta con ayuda baja: "+B.prioridad.join(", ")+". A ellos se suma Buenaventura, que no aparece rezagada en el conteo de entregas pero concentra el "+pc(shAfecBva)+" de la población afectada del departamento y ha recibido el "+pc(shTonBva)+" de las toneladas.",
  "2. QUÉ FALTA HOY · "+B.sin_entregas.join(" y ")+" no han recibido una sola entrega en 17 días de operación. Ambos están en la zona Sur, la única de las cuatro sin cobertura completa.",
  "3. CON QUÉ · El "+pctSub+" % de lo despachado es subsistencia inmediata y menos del 1 % son herramientas y materiales. El "+num("75,7")+" % de los establecimientos pide capital de trabajo, reparación o ambos. La ruta humanitaria y la recuperación productiva no se tocan: hacen falta dos instrumentos, no uno.",
],ROJO));

// ══════════ 1 ══════════
b.push(H1("1. Qué aporta cruzar las tres fuentes"));
b.push(P("Cada plataforma responde bien una pregunta y ninguna responde la que importa para asignar recursos."));
b.push(tabla(["Fuente","Qué mide","Qué no ve"],[
  ["Matriz GRD (SOCK2)","Criticidad humanitaria: personas, vivienda, conectividad. Índice ICM de 0 a 100 con semáforo y vulnerabilidad estructural","Si el tejido productivo del municipio puede volver a generar ingresos"],
  ["Ruta de la Solidaridad","Ayuda efectivamente despachada: entregas, toneladas, composición y fecha por municipio","Si esa ayuda guarda proporción con la necesidad de cada municipio"],
  ["Observatorio de turismo","Afectación declarada por "+n(D.n)+" establecimientos: continuidad, pérdidas, empleo y necesidad","La afectación a hogares y a infraestructura pública"],
],[2350,4100,2910],{textoFinal:true}));
b.push(Rich([["Las dos miradas de necesidad no son la misma. ","b"],
  ["La correlación de Spearman entre el índice oficial de criticidad y el índice de afectación económica es de "+num(B.corr_icm_iae)+". Coinciden en la dirección general —los municipios golpeados suelen serlo en ambas— pero difieren lo suficiente como para que cada tablero, leído solo, deje fuera municipios que el otro señala.",""]]));
b.push(esp(50));
b.push(tabla(["Solo lo ve la matriz GRD","Puesto GRD / económico","Solo lo ve el observatorio","Puesto GRD / económico"],
  [0,1,2,3,4].map(i=>[
    B.solo_humanitario[i].municipio,
    "p. "+B.solo_humanitario[i].r_icm+" / p. "+B.solo_humanitario[i].r_iae,
    B.solo_economico[i].municipio,
    "p. "+B.solo_economico[i].r_icm+" / p. "+B.solo_economico[i].r_iae]),
  [2500,2180,2500,2180],{numDesde:9}));
b.push(Fu("Puesto entre 41 municipios. Un municipio como El Dovio es noveno en criticidad humanitaria y trigésimo quinto en afectación económica; Yumbo, al revés. Priorizar con un solo índice deja fuera a la mitad de cada lista."));

// ══════════ 2 ══════════
b.push(H1("2. Dónde: la brecha entre necesidad y ayuda"));
b.push(P("Los municipios son de tamaños muy distintos, de modo que comparar toneladas contra toneladas no informa. Se comparan posiciones: el puesto de cada municipio por necesidad —promedio de su puesto en criticidad GRD y en afectación económica— frente a su puesto por toneladas recibidas."));
b.push(img("e1_matriz.png",600,395));
b.push(Cap("Figura 1. Necesidad frente a ayuda recibida, 41 municipios."));
b.push(Rich([["Una brecha positiva no prueba mala asignación. ","b"],
  ["Puede reflejar que el municipio recibió por otra ruta, que tenía vías cerradas o que la ayuda pertinente no era la que despacha esta operación. Es una señal para revisar, no un veredicto.",""]]));

b.push(H2("2.1 Los doce municipios a priorizar"));
b.push(tabla(["#","Municipio","Zona","ICM","Vulnerab.","Índ. econ.","No opera","Ton.","kg/afec.","Brecha"],
  TOP.map((m,i)=>[String(i+1),m.municipio,m.zona,un(m.icm),m.semaforo_vuln,
    m.IAE_aj===null?"—":num(m.IAE_aj),m.pct_no_opera===null?"—":num(m.pct_no_opera)+" %",
    n(m.toneladas),un(m.kg_por_afectado),(m.brecha>0?"+":"")+num(m.brecha)]),
  [380,1500,900,700,1150,900,880,620,830,900],{numDesde:3}));
b.push(Fu("Orden por necesidad, penalizado por el rezago en ayuda. ICM: índice de criticidad municipal de la matriz GRD (0–100). Índ. econ.: índice de afectación económica del observatorio (0–100). kg/afec.: kilogramos entregados por persona afectada declarada."));
b.push(P("Trujillo y Roldanillo encabezan por acumulación: máxima criticidad oficial, máxima afectación económica y, en el caso de Roldanillo, "+n(mun("Roldanillo").viv_destruidas)+" viviendas destruidas —la cifra más alta del departamento— con "+un(mun("Roldanillo").kg_por_afectado)+" kg por persona afectada, por debajo de la mediana de "+un(B.mediana_kg)+" kg."));

// ══════════ 3 ══════════
b.push(H1("3. Tres situaciones que exigen respuesta esta semana"));
b.push(H2("3.1 Buenaventura: un quinto de los afectados, menos de un veinteavo de la ayuda"));
b.push(P("Buenaventura declara "+n(bva.poblacion_afectada)+" personas afectadas, el "+pc(shAfecBva)+" del total departamental, y ha recibido "+n(bva.toneladas)+" toneladas, el "+pc(shTonBva)+". Son "+un(bva.kg_por_afectado)+" kilogramos por persona afectada frente a una mediana departamental de "+un(B.mediana_kg)+": el municipio recibe una séptima parte de lo que recibe el municipio típico, por persona."));
b.push(P("En el conteo de entregas no aparece rezagado —está entre los diez primeros por número de despachos— y por eso el tablero de la Ruta no lo señala. La distorsión aparece solo al dividir por población afectada. Buenaventura concentra además "+n(bva.viv_destruidas)+" viviendas destruidas y "+n(bva.fallecidos)+" de los "+n(K.fallecidos)+" fallecidos del departamento."));
b.push(H2("3.2 Florida y Candelaria: cero entregas en diecisiete días"));
b.push(P("Ninguno de los dos ha recibido una entrega. La zona Sur es la única de las cuatro sin cobertura completa: 5 de 7 municipios. Son municipios de criticidad media y baja —ICM "+un(mun("Florida").icm)+" y "+un(mun("Candelaria").icm)+"— con poblaciones afectadas pequeñas, "+n(mun("Florida").poblacion_afectada)+" y "+n(mun("Candelaria").poblacion_afectada)+" personas. La pregunta no es si merecen prioridad sobre Trujillo; es por qué en diecisiete días no hubo una sola entrega, y si la razón es logística, de registro o de decisión."));
b.push(H2("3.3 Los municipios con menor intensidad de ayuda"));
b.push(img("e2_intensidad.png",600,276));
b.push(Cap("Figura 2. Kilogramos entregados por persona afectada declarada."));
b.push(P("Cinco municipios están por debajo de 2 kg por persona afectada. Tres de ellos —Toro, El Dovio y el propio Buenaventura— están en el tercio superior de criticidad oficial. Toro es el segundo municipio más crítico del departamento y recibe "+un(mun("Toro").kg_por_afectado)+" kg por afectado, la mitad de la mediana."));

// ══════════ 4 ══════════
b.push(H1("4. Con qué: falta un segundo instrumento"));
b.push(img("e3_brecha_tipo.png",610,266));
b.push(Cap("Figura 3. Composición de la ayuda despachada frente a la necesidad declarada por los establecimientos."));
b.push(P("La Ruta de la Solidaridad hace bien lo que se propuso hacer: cubrir subsistencia en emergencia. Aseo personal, alimentos, protección y líquidos suman el "+(A.composicion["Aseo personal"]+A.composicion["Alimentos"]+A.composicion["Protección y seguridad"]+A.composicion["Líquidos e hidratación"])+" % de lo despachado y cada una llegó a 38 o 39 de los 41 municipios. A tres semanas del sismo, sin embargo, la necesidad declarada por el tejido productivo es de otra naturaleza y ningún instrumento la está atendiendo."));
b.push(esp(50));
b.push(tabla(["Necesidad","Cuántos la piden","Instrumento que hoy existe","Vacío"],[
  ["Capital de trabajo o insumos",pc(100*D.nec["Capital de trabajo o insumos"]/D.bases["Principal necesidad"]),"ninguno en la Ruta","total"],
  ["Reparar instalaciones o equipos",pc(100*D.nec["Reparar instalaciones o equipos"]/D.bases["Principal necesidad"]),"< 1 % herramientas y materiales","casi total"],
  ["Recuperar clientes y ventas",pc(100*D.nec["Recuperar clientes y ventas"]/D.bases["Principal necesidad"]),"ninguno","total"],
  ["Subsistencia del hogar","—",pctSub+" % de lo despachado","cubierto"],
],[2900,1500,2900,2060],{numDesde:1,textoFinal:true}));
b.push(Rich([["Sobre la forma del instrumento. ","b"],
  ["Entre los "+n(D.bases["Apoyo financiero"])+" establecimientos que expresan preferencia, el "+pc(100*D.apo["Capital semilla (no reembolsable)"]/D.bases["Apoyo financiero"])+" pide capital no reembolsable y solo el "+pc(100*D.apo["Nuevo crédito"]/D.bases["Apoyo financiero"])+" pide crédito nuevo. Un sector con la operación interrumpida no percibe capacidad de asumir deuda: una línea de crédito, aun en condiciones favorables, arriesga baja colocación.",""]]));
b.push(P("Un dato adicional del observatorio orienta el diseño: la correlación entre el porcentaje de establecimientos paralizados y el de pérdidas superiores a $20 millones es de solo "+num(D.correlaciones.pct_no_opera.pct_perd_alta.toFixed(2))+". Parálisis y pérdida patrimonial son problemas distintos. El municipio paralizado con pérdidas pequeñas necesita liquidez inmediata en montos bajos y muchas operaciones; el municipio que opera con pérdidas altas necesita reposición de activos en pocas operaciones de monto grande. Un instrumento único mal atenderá a uno de los dos."));

// ══════════ 5 ══════════
b.push(H1("5. Qué no dicen estos datos"));
b.push(Bul("Las toneladas de la Ruta son una estimación a partir del número de entregas, no un pesaje. Sirven para comparar municipios entre sí, no para auditar volumen."));
b.push(Bul("Los cortes no coinciden: la ayuda está al "+fecha(A.fecha_corte)+", la matriz GRD al "+fecha(K.fecha_corte)+" y el observatorio al 1 de septiembre. Un municipio puede haber recibido entregas después del corte de la Ruta."));
b.push(Bul("Santiago de Cali queda fuera de ambos conteos municipales oficiales. Va por canal propio, con "+n(A.cali_entregas)+" entregas y "+n(A.cali_unidades)+" unidades. Cualquier lectura departamental de este informe excluye a la capital."));
b.push(Bul("El observatorio recoge reportes voluntarios: cubre el "+num(D.dane.cobertura)+" % del tejido empresarial del departamento y no es una muestra probabilística. Un municipio con pocos reportes tiene un índice económico menos firme, y por eso el orden se calcula con contracción hacia la media departamental."));
b.push(Bul("La población afectada es la declarada por cada municipio a la matriz GRD. Diferencias en el criterio de registro entre municipios afectan directamente el indicador de kilogramos por afectado."));

// ══════════ 6 ══════════
b.push(H1("6. Recomendaciones"));
b.push(BulR([["Enviar la próxima rotación a "+B.prioridad.join(", ")+" y Buenaventura. ","b"],
  ["Los cuatro primeros están en necesidad alta con ayuda baja; Buenaventura por intensidad, no por conteo.",""]]));
b.push(BulR([["Verificar por qué Florida y Candelaria no registran entregas. ","b"],
  ["Diecisiete días sin una sola entrega en la única zona sin cobertura completa exige una explicación operativa antes que una asignación.",""]]));
b.push(BulR([["Abrir una segunda línea de recuperación productiva, separada de la humanitaria. ","b"],
  ["Capital no reembolsable en montos bajos para los municipios paralizados y reposición de activos para los de pérdida patrimonial alta. Son dos instrumentos, no dos tramos del mismo.",""]]));
b.push(BulR([["Publicar el indicador de kilogramos por persona afectada en el tablero de la Ruta. ","b"],
  ["Es la métrica que reveló el caso de Buenaventura y hoy no está a la vista de quien decide.",""]]));
b.push(BulR([["Unificar el corte de las tres plataformas. ","b"],
  ["Con seis días de diferencia entre la ayuda y la criticidad, parte de la brecha medida puede ser desfase y no desatención.",""]]));
b.push(BulR([["Incorporar el ICM y la vulnerabilidad al observatorio de turismo. ","b"],
  ["De los "+B.n_criticos+" municipios con mayor afectación económica, "+B.fuera_econ.length+" no figuran entre los críticos de la matriz GRD ("+B.fuera_econ.join(", ")+"), y "+B.fuera_hum.length+" críticos de la matriz no están entre los peores económicamente ("+B.fuera_hum.join(", ")+"). Ninguna de las dos lecturas es prescindible.",""]]));
b.push(esp(60));
b.push(Fu("Fuentes: Matriz GRD pública, Gobernación del Valle del Cauca y K2 Digital (sock2.k2digital.co/grd-publico), corte "+fecha(K.fecha_corte)+". Ruta de la Solidaridad, Valle Humanitario, Gobernación del Valle del Cauca (sigesi.valledelcauca.gov.co/valle-humanitario), corte "+fecha(A.fecha_corte)+". Observatorio de Turismo del Valle del Cauca sobre reportes_emergencia_2026-09-01.xlsx, "+n(D.n)+" establecimientos únicos. El detalle municipal completo se entrega en brecha_municipal.csv."));

const doc=new Document({creator:"Observatorio de Turismo · Valle del Cauca",
  title:"Dónde y en qué concentrar la ayuda",
  description:"Informe ejecutivo · cruce de afectación empresarial, criticidad GRD y ayuda entregada",
  numbering:{config:[{reference:"v",levels:[{level:0,format:LevelFormat.BULLET,text:"•",
    alignment:AlignmentType.LEFT,style:{paragraph:{indent:{left:convertInchesToTwip(0.26),
    hanging:convertInchesToTwip(0.16)}}}}]}]},
  sections:[{properties:{page:{margin:{top:1000,bottom:1000,left:1000,right:1000}}},children:b}]});
Packer.toBuffer(doc).then(x=>{fs.writeFileSync("Informe_ejecutivo_orientacion_ayuda_2026-09-02.docx",x);
  console.log("generado:",(x.length/1024).toFixed(0),"KB");});

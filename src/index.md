---
title: Obras
---

```js
import {fechaTexto, fechaLarga, millones, tieneDato, plural, ESTADO_OBRA, ordenar, razonesCortas, unirFrase, iconoEstado, chipEstado, leyendaObra, leyendaEstados, mapaObras, asegurarRayado, esReal, pulso, miniatura} from "./components/lupia.js";
asegurarRayado();
const senales = await FileAttachment("data/senales.csv").csv({typed: true});
const semanal = await FileAttachment("data/matriz_semanal.csv").csv({typed: true});
const fotos = await FileAttachment("data/fotos.csv").csv({typed: true});
const pais = await FileAttachment("data/costa-rica.json").json();
const resumen = await FileAttachment("data/resumen.json").json();
// Foto real de la cámara del piloto (personas difuminadas), para la obra con datos de dIAra
const fotoPiloto = await FileAttachment("data/fotos-piloto/20240319-090439.jpg").url();
```

<section class="portada" aria-labelledby="titulo">
  <p class="antetitulo">Seguimiento ciudadano de obras públicas con las cámaras de dIAra</p>
  <h1 id="titulo">¿Cómo va la obra de su comunidad?</h1>
  <p class="bajada">Vea si la cámara vio trabajo, qué tan confiable es ese dato y la evidencia, en menos de un minuto.</p>
</section>

```js
// El buscador y cuatro cifras que también sirven de filtro (llegan con los datos)
const lista = ordenar(senales, resumen.pesos);
const busqueda = Inputs.text({label: "Buscar una obra", placeholder: "Nombre de la obra, cantón o provincia", width: "100%"});
const texto = Generators.input(busqueda);
const provinciasLista = [...new Set(lista.map((o) => o.provincia))].sort((a, b) => a.localeCompare(b, "es"));
const filtroProvincia = Inputs.select(["Todas", ...provinciasLista], {label: "Provincia"});
const provinciaElegida = Generators.input(filtroProvincia);
const filtroEstado = Inputs.select(["Todos", ...Object.keys(ESTADO_OBRA)], {label: "Estado", format: (k) => (k === "Todos" ? k : ESTADO_OBRA[k].label)});
const estadoElegido = Generators.input(filtroEstado);
const cuenta = (k) => lista.filter((o) => o.estado === k).length;
function cifra(estado, etiqueta, valor, tono) {
  const boton = html`<button type="button" class=${`cifra-tarjeta ${tono}`}><span class="cifra-etiqueta">${etiqueta}</span><span class="cifra-valor">${valor}</span><span class="cifra-ver">${estado === "Todos" ? "Ver todas" : "Ver cuáles"}</span></button>`;
  boton.onclick = () => {
    filtroEstado.value = estado;
    filtroEstado.dispatchEvent(new Event("input", {bubbles: true}));
    document.getElementById("obras")?.scrollIntoView({behavior: "smooth", block: "start"});
  };
  return boton;
}
display(html`<div class="portada-controles">
  <div class="portada-buscador">${busqueda}${filtroProvincia}${filtroEstado}</div>
  <p class="portada-nota">Datos al ${fechaTexto(resumen.fecha_corte)}. Prototipo académico: una obra usa datos reales del piloto de dIAra y las demás son simuladas a partir de ellos. <a href="./datos.html">De dónde salen los datos</a></p>
</div>
<div class="cifras-fila" role="group" aria-label="Resumen de las obras (cada cifra filtra la lista)">
  ${cifra("Todos", "Obras en seguimiento", lista.filter((o) => !o.historica).length, "")}
  ${cifra("revisar", "Necesitan revisión", cuenta("revisar"), "alerta")}
  ${cifra("sin_alertas", "Sin alertas", cuenta("sin_alertas"), "ok")}
  ${cifra("sin_datos", "Cámara sin datos", cuenta("sin_datos"), "gris")}
</div>`);
```

```js
// Qué obras se ven según la búsqueda y los filtros
const sinTildes = (s) => String(s ?? "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
const consulta = sinTildes(texto).trim();
const coincide = (o) => (!consulta || [o.nombre, o.canton, o.provincia, o.institucion_ejecutora, o.tipo].some((v) => sinTildes(v).includes(consulta)))
  && (provinciaElegida === "Todas" || o.provincia === provinciaElegida) && (estadoElegido === "Todos" || o.estado === estadoElegido);
const visibles = lista.filter(coincide);
const activo = visibles.length < lista.length ? new Set(visibles.map((o) => o.obra_id)) : null;
```

```js
// La foto más reciente de cada obra (registro, pestaña fotos) y sus últimas 8 semanas de actividad
const ultimaFoto = new Map(d3.rollups(fotos, (v) => [...v].sort((a, b) => b.fecha - a.fecha)[0], (d) => d.obra_id));
function fotoDe(o) {
  if (esReal(o)) return html`<img src=${fotoPiloto} alt="" loading="lazy">`;
  const f = ultimaFoto.get(o.obra_id);
  if (!f) return html`<span class="obra-sinfoto">Sin foto</span>`;
  const img = html`<img src=${miniatura(f.enlace)} alt="" loading="lazy">`;
  img.onerror = () => { img.onerror = null; img.src = f.enlace; };
  return img;
}
// Costo y fecha de entrega: las dos cifras que la gente busca primero en una obra pública
const datosClave = (o) => [tieneDato(o.monto_vigente_crc) ? millones(o.monto_vigente_crc) : null, o.fecha_fin_vigente ? `entrega: ${fechaLarga(o.fecha_fin_vigente)}` : null].filter(Boolean).join(" · ");
const semanasDe = (id) => semanal.filter((d) => d.obra_id === id).sort((a, b) => a.semana - b.semana).slice(-8);
function tarjetaObra(o) {
  const semanas = semanasDe(o.obra_id);
  return html`<li class=${`obra-tarjeta ${o.estado}`} data-obra=${o.obra_id}>
    <a href=${`./ficha.html?id=${o.obra_id}`}>
      <span class="obra-foto">${fotoDe(o)}</span>
      <span class="obra-cuerpo">
        <span class="obra-titulo">${iconoEstado(o.estado, o.orden, 22)}<span class="obra-nombre">${o.nombre}</span>${esReal(o) ? html`<span class="etiqueta-real">Datos reales</span>` : ""}</span>
        <span class="obra-lugar">${o.canton}, ${o.provincia}${datosClave(o) ? html`<span class="obra-clave"> · ${datosClave(o)}</span>` : ""}</span>
        <span class="obra-estado">${chipEstado(o.estado)}<span class="obra-porque">${unirFrase(razonesCortas(o))}</span></span>
        ${semanas.length ? html`<span class="obra-semanas">${pulso(semanas, {celda: 14, alto: 14, sep: 3})}<span>últimas ${plural(semanas.length, "semana", "semanas")}</span></span>` : ""}
      </span>
    </a>
  </li>`;
}
const NOTA_GRUPO = {
  sin_datos: "Primero hay que reparar la cámara: mientras tanto no se puede concluir nada sobre la obra.",
  historico: "La cámara ya no está en estas obras. Se conservan para consulta."
};
function listaObras() {
  if (!visibles.length) return html`<p class="vacio">Ninguna obra coincide con la búsqueda o los filtros. Borre la búsqueda o elija «Todas» y «Todos» para ver todas.</p>`;
  return html`${Object.keys(ESTADO_OBRA).map((k) => {
    const grupo = visibles.filter((o) => o.estado === k);
    if (!grupo.length) return "";
    return html`<section class="grupo-obras" aria-labelledby=${`g-${k}`}>
      <h2 id=${`g-${k}`}>${ESTADO_OBRA[k].grupo} <span>${grupo.length}</span></h2>
      ${NOTA_GRUPO[k] ? html`<p class="nota-grupo">${NOTA_GRUPO[k]}</p>` : ""}
      <ol class="obras-lista">${grupo.map(tarjetaObra)}</ol>
    </section>`;
  })}`;
}
display(html`<div class="inicio-cuerpo" id="obras">
  <aside class="tarjeta caja-mapa" aria-label="Mapa de las obras">
    <h2 class="tarjeta-titulo">Dónde están</h2>
    ${resize((width) => mapaObras(pais, lista, {width: Math.min(width, 520), activo}))}
    ${leyendaObra()}
    <p class="mapa-nota">En cada tarjeta, un cuadro por semana:</p>
    ${leyendaEstados(["actividad", "sin_actividad", "sin_datos", "terminada"])}
  </aside>
  <div class="caja-lista">${listaObras()}</div>
</div>`);
```

```js
// Al pasar por una obra en la lista se resalta su punto en el mapa, y al revés
{
  const marcar = (id) => document.querySelectorAll("[data-obra]").forEach((el) => el.classList.toggle("activo", el.dataset.obra === id));
  const sobre = (e) => marcar(e.target.closest?.("[data-obra]")?.dataset.obra ?? null);
  document.addEventListener("pointerover", sobre);
  document.addEventListener("focusin", sobre);
  invalidation.then(() => {
    document.removeEventListener("pointerover", sobre);
    document.removeEventListener("focusin", sobre);
  });
}
```

```js
// Cómo sabe LupIA si hubo trabajo: tres pasos con las cifras del método (salen de radar/config.py, no se escriben a mano)
const metodo = resumen.metodo ?? {};
const horario = metodo.horario_laboral ? ` (de ${metodo.horario_laboral[0]}:00 a ${metodo.horario_laboral[1]}:59)` : "";
display(html`<section class="como" aria-labelledby="t-como">
  <h2 id="t-como">¿Cómo sabe LupIA si hubo trabajo?</h2>
  <ol class="como-pasos">
    <li><span class="como-num" aria-hidden="true">1</span><div><b>La cámara toma fotos de la obra</b><p>${metodo.intervalo_seg ? `Una cada ${metodo.intervalo_seg} segundos, más o menos, durante el día.` : "Varias por hora durante el día."} Las personas salen difuminadas.</p></div></li>
    <li><span class="como-num" aria-hidden="true">2</span><div><b>La IA de dIAra busca personas y máquinas</b><p>No ve todo: ${metodo.sensibilidad_modelo ? `en el piloto encontró unas ${Math.round(100 * metodo.sensibilidad_modelo)} de cada 100 que se veían en las fotos.` : "puede pasar por alto a alguien."}</p></div></li>
    <li><span class="como-num" aria-hidden="true">3</span><div><b>LupIA resume cada día</b><p>${metodo.umbral_actividad ? `Hubo trabajo si en ${Math.round(100 * metodo.umbral_actividad)} % o más de las fotos de la jornada${horario} aparece alguien o alguna máquina.` : "Hubo trabajo si aparece alguien o alguna máquina en buena parte de las fotos."} Si no llegan fotos, el día queda «sin datos».</p></div></li>
  </ol>
  <p class="como-mas">Ver personas o máquinas no mide cuánto avanzó la obra: eso lo informa la ejecutora. <a href="./metodologia.html">Cómo funciona, paso a paso</a></p>
</section>`);
```

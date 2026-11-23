---
title: Obras
---

```js
import {fechaTexto, plural, ESTADO_OBRA, ordenar, razonesCortas, unirFrase, iconoEstado, chipEstado, leyendaObra, leyendaEstados, mapaObras, asegurarRayado, esReal, pulso, miniatura} from "./components/lupia.js";
asegurarRayado();
const senales = await FileAttachment("data/senales.csv").csv({typed: true});
const semanal = await FileAttachment("data/matriz_semanal.csv").csv({typed: true});
const fotos = await FileAttachment("data/fotos.csv").csv({typed: true});
const pais = await FileAttachment("data/costa-rica.json").json();
const resumen = await FileAttachment("data/resumen.json").json();
// Foto real de la cámara del piloto (personas difuminadas), para la obra con datos de dIAra
const fotoPiloto = await FileAttachment("data/fotos-piloto/20240319-090439.jpg").url();
```

```js
// Portada: la pregunta de la ciudadana, el buscador y cuatro cifras que también sirven de filtro
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
display(html`<section class="portada" aria-labelledby="titulo">
  <p class="antetitulo">Seguimiento ciudadano de obras públicas con las cámaras de dIAra</p>
  <h1 id="titulo">¿Cómo va la obra de su comunidad?</h1>
  <p class="bajada">Vea si la cámara vio trabajo, qué tan confiable es ese dato y la evidencia, en menos de un minuto.</p>
  <div class="portada-buscador">${busqueda}${filtroProvincia}${filtroEstado}</div>
  <p class="portada-nota">Datos al ${fechaTexto(resumen.fecha_corte)}. Prototipo académico: una obra usa datos reales del piloto de dIAra y las demás son simuladas a partir de ellos. <a href="./datos.html">De dónde salen los datos</a></p>
</section>
<div class="cifras-fila" role="group" aria-label="Resumen de las obras (cada cifra filtra la lista)">
  ${cifra("Todos", "Obras en seguimiento", lista.filter((o) => !o.historica).length, "")}
  ${cifra("revisar", "Con alertas", cuenta("revisar"), "alerta")}
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
const semanasDe = (id) => semanal.filter((d) => d.obra_id === id).sort((a, b) => a.semana - b.semana).slice(-8);
function tarjetaObra(o) {
  const semanas = semanasDe(o.obra_id);
  return html`<li class=${`obra-tarjeta ${o.estado}`} data-obra=${o.obra_id}>
    <a href=${`./ficha.html?id=${o.obra_id}`}>
      <span class="obra-foto">${fotoDe(o)}</span>
      <span class="obra-cuerpo">
        <span class="obra-titulo">${iconoEstado(o.estado, o.orden, 22)}<span class="obra-nombre">${o.nombre}</span>${esReal(o) ? html`<span class="etiqueta-real">Datos reales</span>` : ""}</span>
        <span class="obra-lugar">${o.canton}, ${o.provincia}</span>
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

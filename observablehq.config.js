// Configuración del sitio LupIA (Observable Framework). Documentación: https://observablehq.com/framework/config

const lupa = `<svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true"><circle cx="8.5" cy="8.5" r="6" fill="none" stroke="currentColor" stroke-width="2.2"/><path d="M13 13l5 5" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"/><circle cx="8.5" cy="8.5" r="2" fill="#ffe45c"/></svg>`;

const paginas = [
  {nombre: "Qué revisar", href: "./index.html", rutas: ["/", "/obra", "/index"]},
  {nombre: "Ver una obra", href: "./ficha.html", rutas: ["/ficha"]},
  {nombre: "Datos", href: "./datos.html", rutas: ["/datos"]},
  {nombre: "Cómo funciona", href: "./metodologia.html", rutas: ["/metodologia"]}
];

export default {
  title: "LupIA",
  root: "src",
  lang: "es",
  pages: [{name: "Ficha de la obra", path: "/ficha"}, {name: "Qué revisar", path: "/index"}, {name: "Análisis de obra", path: "/obra"}, {name: "Datos", path: "/datos"}, {name: "Cómo funciona", path: "/metodologia"}, {name: "Mantenimiento del registro", path: "/mantenimiento"}],
  sidebar: false,
  toc: false,
  pager: false,
  search: false,
  preserveExtension: true,
  preserveIndex: true,
  style: "style.css",
  // Idioma del documento y zoom permitido en celulares (accesibilidad)
  head: `<script>document.documentElement.lang = "es"; document.querySelector('meta[name="viewport"]')?.setAttribute("content", "width=device-width, initial-scale=1");</script>`,
  header: ({path}) =>
    `<a class="lupia-marca" href="./index.html">${lupa}<span>LupIA</span></a>` +
    `<nav class="lupia-nav" aria-label="Secciones">${paginas
      .map((p) => `<a href="${p.href}"${p.rutas.includes(path) ? ' aria-current="page"' : ""}>${p.nombre}</a>`)
      .join("")}</nav>`,
  footer:
    "LupIA es un prototipo académico de LEAD University (Visualización de datos, 2026) y no es una herramienta oficial de la Contraloría General de la República. " +
    "Usa datos reales del piloto de dIAra (CGR, CENFOTEC y GIZ) y obras simuladas a partir de ellos, con nombres seudonimizados. Lluvia: Open-Meteo (CC BY 4.0). Límites de provincias: daticos-geotec (UCR), vía CR_distritos_geojson (Apache 2.0). Fotos de referencia: Wikimedia Commons (autor y licencia en cada foto). Tipografía: Public Sans (OFL). " +
    '<a href="./mantenimiento.html">Mantenimiento del registro</a> (gerencia y encargados).',
  // En Windows el intérprete se llama "python"; en Mac, Linux y GitHub Actions, "python3".
  interpreters: {".py": [process.platform === "win32" ? "python" : "python3"]}
};

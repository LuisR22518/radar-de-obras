// Configuración del sitio LupIA (Observable Framework). Documentación: https://observablehq.com/framework/config

const lupa = `<svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true"><circle cx="8.5" cy="8.5" r="6" fill="none" stroke="currentColor" stroke-width="2.2"/><path d="M13 13l5 5" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"/><circle cx="8.5" cy="8.5" r="2.2" fill="#f2b33d"/></svg>`;

// Para la vista previa al compartir: la imagen vive en el repositorio (las redes piden una dirección completa)
const descripcion = "Vea si la cámara de dIAra vio trabajo en una obra pública, qué tan confiable es ese dato y la evidencia. Prototipo académico de LEAD University.";
const imagenCompartir = "https://raw.githubusercontent.com/LuisR22518/radar-de-obras/main/recursos/compartir.png";
const icono = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><rect width="20" height="20" rx="4" fill="#0f2235"/><circle cx="8.5" cy="8.5" r="4.6" fill="none" stroke="#fff" stroke-width="1.9"/><path d="M12 12l4 4" stroke="#fff" stroke-width="2.2" stroke-linecap="round"/><circle cx="8.5" cy="8.5" r="1.7" fill="#f2b33d"/></svg>`;

const paginas = [
  {nombre: "Obras", href: "./index.html", rutas: ["/", "/index", "/ficha"]},
  {nombre: "Cómo funciona", href: "./metodologia.html", rutas: ["/metodologia"]},
  {nombre: "Datos", href: "./datos.html", rutas: ["/datos"]},
  {nombre: "Para la Contraloría", href: "./contraloria.html", rutas: ["/contraloria", "/obra", "/mantenimiento"]}
];

export default {
  title: "LupIA",
  root: "src",
  lang: "es",
  pages: [{name: "Obras", path: "/index"}, {name: "Ficha de la obra", path: "/ficha"}, {name: "Para la Contraloría", path: "/contraloria"}, {name: "Análisis de obra", path: "/obra"}, {name: "Datos", path: "/datos"}, {name: "Cómo funciona", path: "/metodologia"}, {name: "Mantenimiento del registro", path: "/mantenimiento"}],
  sidebar: false,
  toc: false,
  pager: false,
  search: false,
  preserveExtension: true,
  preserveIndex: true,
  style: "style.css",
  // Sin la fuente de Google que Framework agrega por defecto: LupIA usa Public Sans incluida en style.css
  // (una petición menos que bloquea la primera pintura, sobre todo en celular, y nada se envía a terceros)
  globalStylesheets: [],
  // Idioma, zoom permitido en celulares (accesibilidad), ícono y vista previa al compartir por WhatsApp o redes
  head: [
    `<script>document.documentElement.lang = "es"; document.querySelector('meta[name="viewport"]')?.setAttribute("content", "width=device-width, initial-scale=1");</script>`,
    `<meta name="description" content="${descripcion}">`,
    `<meta name="theme-color" content="#0f2235">`,
    `<link rel="icon" href="data:image/svg+xml,${encodeURIComponent(icono)}">`,
    `<meta property="og:type" content="website">`,
    `<meta property="og:site_name" content="LupIA">`,
    `<meta property="og:title" content="LupIA: ¿cómo va la obra de su comunidad?">`,
    `<meta property="og:description" content="${descripcion}">`,
    `<meta property="og:image" content="${imagenCompartir}">`,
    `<meta property="og:image:width" content="1200">`,
    `<meta property="og:image:height" content="630">`,
    `<meta property="og:locale" content="es_CR">`,
    `<meta name="twitter:card" content="summary_large_image">`
  ].join("\n"),
  header: ({path}) =>
    `<a class="lupia-marca" href="./index.html">${lupa}<span>LupIA</span></a>` +
    `<nav class="lupia-nav" aria-label="Secciones">${paginas
      .map((p) => `<a href="${p.href}"${p.rutas.includes(path) ? ' aria-current="page"' : ""}>${p.nombre}</a>`)
      .join("")}</nav>` +
    `<span class="lupia-prototipo">Prototipo académico</span>`,
  footer:
    `<div class="pie-enlaces" role="navigation" aria-label="Más de LupIA"><a href="./metodologia.html">Cómo funciona</a><a href="./datos.html">De dónde salen los datos</a><a href="./contraloria.html">Para la Contraloría</a><a href="./mantenimiento.html">Mantenimiento del registro</a><a href="https://github.com/LuisR22518/radar-de-obras" target="_blank" rel="noopener">Código y datos abiertos ↗</a></div>` +
    "<p>LupIA es un prototipo académico de LEAD University (Visualización de datos, 2026) y no es una herramienta oficial de la Contraloría General de la República. " +
    "Usa datos reales del piloto de dIAra (CGR, CENFOTEC y GIZ) y obras simuladas a partir de ellos, con nombres seudonimizados. Lluvia: Open-Meteo (CC BY 4.0). Fotos de referencia: Wikimedia Commons (autor y licencia en cada foto). Tipografía: Public Sans (OFL).</p>",
  // En Windows el intérprete se llama "python"; en Mac, Linux y GitHub Actions, "python3".
  interpreters: {".py": [process.platform === "win32" ? "python" : "python3"]}
};

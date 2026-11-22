// Configuración del sitio (Observable Framework). Documentación: https://observablehq.com/framework/config
export default {
  title: "Radar de Obras",
  root: "src",
  lang: "es",
  pages: [
    {name: "Cartera", path: "/"},
    {name: "Análisis de obra", path: "/obra"},
    {name: "Metodología y datos", path: "/metodologia"}
  ],
  style: "style.css",
  toc: false,
  pager: false,
  footer:
    "Prototipo académico de LEAD University (Visualización de datos, 2026). No es una herramienta oficial de la CGR. " +
    "Detecciones simuladas con el formato de dIAra; obras seudonimizadas. Lluvia: Open-Meteo (CC BY 4.0).",
  // En Windows el intérprete se llama "python"; en Mac, Linux y GitHub Actions, "python3".
  interpreters: {".py": [process.platform === "win32" ? "python" : "python3"]}
};

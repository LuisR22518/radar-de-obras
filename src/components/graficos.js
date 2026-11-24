// Gráficos con Plot. Solo los importan las páginas que los dibujan (la ficha y el análisis de obra),
// para que el inicio, la lista de la Contraloría y las páginas de lectura no descarguen Plot.
import * as Plot from "npm:@observablehq/plot";

export {Plot};

// Gráfico de Plot sin las etiquetas ARIA inválidas que Plot pone en sus grupos internos.
export function grafico(opciones) {
  const figura = Plot.plot(opciones);
  figura.querySelectorAll("g[aria-label]").forEach((g) => g.removeAttribute("aria-label"));
  figura.querySelectorAll("svg").forEach((s) => s.setAttribute("aria-hidden", "true"));
  return figura;
}

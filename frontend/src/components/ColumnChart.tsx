import { useEffect, useRef, useState } from "react";

export interface Series {
  key: string;
  label: string;
  /** Variable CSS de la série, ex. "var(--series-1)". */
  color: string;
}

interface ColumnChartProps {
  title: string;
  categories: string[];
  /** Libellé long d'une catégorie (info-bulle et tableau). */
  categoryLabel?: (index: number) => string;
  series: Series[];
  /** values[i][série] pour la catégorie i. */
  values: Record<string, number>[];
  formatValue?: (value: number) => string;
  /** Plafond imposé de l'axe (ex. 1 pour un taux). */
  max?: number;
  height?: number;
}

const MARGIN = { top: 12, right: 8, bottom: 28, left: 44 };
const GAP = 2; // espace entre segments empilés

function useWidth<T extends HTMLElement>(): [React.RefObject<T | null>, number] {
  const ref = useRef<T>(null);
  const [width, setWidth] = useState(600);
  useEffect(() => {
    if (!ref.current) return;
    const observer = new ResizeObserver(([entry]) => setWidth(entry.contentRect.width));
    observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);
  return [ref, width];
}

function niceMax(value: number): number {
  if (value <= 0) return 1;
  const magnitude = 10 ** Math.floor(Math.log10(value));
  const step = [1, 2, 2.5, 5, 10].find((s) => s * magnitude >= value / 4) ?? 10;
  return Math.ceil(value / (step * magnitude)) * step * magnitude;
}

/** Path d'une colonne arrondie (4 px) en haut seulement, posée sur la ligne de base. */
function roundedTop(x: number, y: number, w: number, h: number): string {
  const r = Math.min(4, w / 2, h);
  return `M${x},${y + h} V${y + r} Q${x},${y} ${x + r},${y} H${x + w - r} Q${x + w},${y} ${x + w},${y + r} V${y + h} Z`;
}

/**
 * Histogramme (empilé si plusieurs séries) en SVG, avec info-bulle au survol,
 * légende et vue tableau. Une seule échelle verticale.
 */
export default function ColumnChart({
  title,
  categories,
  categoryLabel = (i) => categories[i],
  series,
  values,
  formatValue = (v) => v.toLocaleString("fr-FR"),
  max,
  height = 240,
}: ColumnChartProps) {
  const [containerRef, width] = useWidth<HTMLDivElement>();
  const [hovered, setHovered] = useState<number | null>(null);
  const [showTable, setShowTable] = useState(false);

  const totals = values.map((row) => series.reduce((sum, s) => sum + (row[s.key] ?? 0), 0));
  const yMax = max ?? niceMax(Math.max(0, ...totals));
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((t) => t * yMax);

  const plotW = Math.max(0, width - MARGIN.left - MARGIN.right);
  const plotH = height - MARGIN.top - MARGIN.bottom;
  const band = categories.length ? plotW / categories.length : 0;
  const barW = Math.max(2, Math.min(28, band * 0.62));
  const y = (v: number) => MARGIN.top + plotH - (v / yMax) * plotH;
  const labelStep = Math.max(1, Math.ceil(categories.length / Math.max(1, plotW / 64)));

  return (
    <figure className="chart">
      <figcaption className="chart__header">
        <span className="chart__title">{title}</span>
        <button type="button" className="link-button" onClick={() => setShowTable(!showTable)}>
          {showTable ? "Voir le graphique" : "Voir le tableau"}
        </button>
      </figcaption>
      {series.length > 1 && (
        <ul className="chart__legend">
          {series.map((s) => (
            <li key={s.key}>
              <span className="chart__swatch" style={{ background: s.color }} aria-hidden="true" />
              {s.label}
            </li>
          ))}
        </ul>
      )}

      {showTable ? (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th scope="col">Période</th>
                {series.map((s) => (
                  <th key={s.key} scope="col">
                    {s.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {values.map((row, i) => (
                <tr key={categories[i]}>
                  <th scope="row">{categoryLabel(i)}</th>
                  {series.map((s) => (
                    <td key={s.key}>{formatValue(row[s.key] ?? 0)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="chart__plot" ref={containerRef}>
          <svg width={width} height={height} role="img" aria-label={title}>
            {ticks.map((tick) => (
              <g key={tick}>
                <line
                  className="chart__grid"
                  x1={MARGIN.left}
                  x2={MARGIN.left + plotW}
                  y1={y(tick)}
                  y2={y(tick)}
                />
                <text className="chart__axis" x={MARGIN.left - 6} y={y(tick)} dy="0.32em" textAnchor="end">
                  {formatValue(tick)}
                </text>
              </g>
            ))}
            {values.map((row, i) => {
              const x = MARGIN.left + i * band + (band - barW) / 2;
              let base = 0;
              const visible = series.filter((s) => (row[s.key] ?? 0) > 0);
              return (
                <g key={categories[i]} opacity={hovered === null || hovered === i ? 1 : 0.45}>
                  {visible.map((s, index) => {
                    const value = row[s.key];
                    const top = y(base + value);
                    const bottom = y(base);
                    base += value;
                    const isTop = index === visible.length - 1;
                    // Espace de 2 px au-dessus de chaque segment recouvert par un autre.
                    const h = Math.max(0, bottom - top - (isTop ? 0 : GAP));
                    const yTop = isTop ? top : top + GAP;
                    return isTop ? (
                      <path key={s.key} d={roundedTop(x, yTop, barW, h)} fill={s.color} />
                    ) : (
                      <rect key={s.key} x={x} y={yTop} width={barW} height={h} fill={s.color} />
                    );
                  })}
                  {i % labelStep === 0 && (
                    <text
                      className="chart__axis"
                      x={x + barW / 2}
                      y={MARGIN.top + plotH + 18}
                      textAnchor="middle"
                    >
                      {categories[i]}
                    </text>
                  )}
                  {/* Zone de survol plus large que la colonne. */}
                  <rect
                    x={MARGIN.left + i * band}
                    y={MARGIN.top}
                    width={band}
                    height={plotH}
                    fill="transparent"
                    onMouseEnter={() => setHovered(i)}
                    onMouseLeave={() => setHovered(null)}
                  />
                </g>
              );
            })}
            <line
              className="chart__baseline"
              x1={MARGIN.left}
              x2={MARGIN.left + plotW}
              y1={y(0)}
              y2={y(0)}
            />
          </svg>
          {hovered !== null && (
            <div
              className="chart__tooltip"
              style={{
                left: Math.min(MARGIN.left + hovered * band + band / 2, width - 90),
                top: MARGIN.top,
              }}
            >
              <strong>{categoryLabel(hovered)}</strong>
              {series.map((s) => (
                <span key={s.key}>
                  <span className="chart__swatch" style={{ background: s.color }} aria-hidden="true" />
                  {s.label} : {formatValue(values[hovered][s.key] ?? 0)}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </figure>
  );
}

import { useCallback, useState } from "react";
import { getStatistiques } from "../../api/admin";
import ColumnChart from "../../components/ColumnChart";
import { ErrorMessage, Loading } from "../../components/Feedback";
import { useApi } from "../../hooks/useApi";
import { useZonesIndex } from "../../hooks/useZonesIndex";
import { formatDay, formatPercent, toDateInput } from "../../utils/format";

const SERIES_RESERVATIONS = [
  { key: "honorees", label: "Honorées", color: "var(--series-1)" },
  { key: "annulees", label: "Annulées", color: "var(--series-2)" },
  { key: "no_show", label: "No-show", color: "var(--series-3)" },
];

function defaultPeriode() {
  const au = new Date();
  const du = new Date(au.getTime() - 29 * 24 * 60 * 60 * 1000);
  return { du: toDateInput(du), au: toDateInput(au) };
}

function StatTile({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="stat-tile">
      <span className="stat-tile__label">{label}</span>
      <span className="stat-tile__value">{value}</span>
      {hint && <span className="stat-tile__hint">{hint}</span>}
    </div>
  );
}

export default function DashboardPage() {
  const [periode, setPeriode] = useState(defaultPeriode);
  const [idParking, setIdParking] = useState<number | "">("");
  const { parkings } = useZonesIndex();

  const loader = useCallback(
    () =>
      getStatistiques({
        du: periode.du,
        au: periode.au,
        id_parking: idParking === "" ? undefined : idParking,
      }),
    [periode, idParking],
  );
  const { data: stats, error, loading, reload } = useApi(loader, "Statistiques indisponibles");

  return (
    <div>
      <h1>Tableau de bord</h1>
      <form className="filters" onSubmit={(e) => e.preventDefault()}>
        <label>
          Du
          <input
            type="date"
            value={periode.du}
            max={periode.au}
            onChange={(e) => setPeriode({ ...periode, du: e.target.value })}
          />
        </label>
        <label>
          Au
          <input
            type="date"
            value={periode.au}
            min={periode.du}
            onChange={(e) => setPeriode({ ...periode, au: e.target.value })}
          />
        </label>
        <label>
          Parking
          <select
            value={idParking}
            onChange={(e) => setIdParking(e.target.value === "" ? "" : Number(e.target.value))}
          >
            <option value="">Tous les parkings</option>
            {parkings.map((p) => (
              <option key={p.id_parking} value={p.id_parking}>
                {p.nom_parking}
              </option>
            ))}
          </select>
        </label>
      </form>

      <ErrorMessage message={error} onRetry={reload} />
      {loading && !stats && <Loading />}

      {stats && (
        <div className={loading ? "is-refreshing" : undefined}>
          <section className="stat-grid" aria-label="Indicateurs de la période">
            <StatTile
              label="Taux d'occupation"
              value={formatPercent(stats.totaux.taux_occupation)}
              hint="heures honorées / heures d'ouverture"
            />
            <StatTile label="Réservations" value={stats.totaux.reservations.toLocaleString("fr-FR")} />
            <StatTile
              label="Annulations"
              value={stats.totaux.annulees.toLocaleString("fr-FR")}
              hint={formatPercent(stats.totaux.taux_annulation)}
            />
            <StatTile
              label="No-show"
              value={stats.totaux.no_show.toLocaleString("fr-FR")}
              hint={formatPercent(stats.totaux.taux_no_show)}
            />
          </section>

          <section className="panel">
            <ColumnChart
              title="Réservations par jour"
              categories={stats.par_jour.map((j) => formatDay(j.jour))}
              series={SERIES_RESERVATIONS}
              values={stats.par_jour.map((j) => ({
                honorees: j.honorees,
                annulees: j.annulees,
                no_show: j.no_show,
              }))}
            />
          </section>

          <section className="panel">
            <ColumnChart
              title="Taux d'occupation par jour"
              categories={stats.par_jour.map((j) => formatDay(j.jour))}
              series={[{ key: "taux", label: "Taux d'occupation", color: "var(--series-1)" }]}
              values={stats.par_jour.map((j) => ({ taux: j.taux_occupation }))}
              formatValue={formatPercent}
              max={1}
            />
          </section>

          <section className="panel">
            <h2 className="chart__title">Par zone</h2>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th scope="col">Zone</th>
                    <th scope="col">Places</th>
                    <th scope="col">Occupation</th>
                    <th scope="col">Réservations</th>
                    <th scope="col">Annulations</th>
                    <th scope="col">No-show</th>
                  </tr>
                </thead>
                <tbody>
                  {stats.par_zone.map((zone) => (
                    <tr key={zone.id_zone}>
                      <th scope="row">
                        {zone.nom_parking}
                        <span className="muted"> · {zone.nom_zone}</span>
                      </th>
                      <td>{zone.nombre_places}</td>
                      <td className="cell-nowrap">
                        <span className="meter" aria-hidden="true">
                          <span
                            className="meter__fill"
                            style={{ width: `${Math.round(zone.taux_occupation * 100)}%` }}
                          />
                        </span>
                        {formatPercent(zone.taux_occupation)}
                      </td>
                      <td>{zone.reservations.toLocaleString("fr-FR")}</td>
                      <td>{formatPercent(zone.taux_annulation)}</td>
                      <td>{formatPercent(zone.taux_no_show)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}

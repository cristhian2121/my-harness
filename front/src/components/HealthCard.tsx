import type { HealthStatus } from "@/lib/types";

type HealthCardProps = {
  status: HealthStatus | null;
  onRefresh: () => void;
};

export function HealthCard({ status, onRefresh }: HealthCardProps) {
  return (
    <section className="surface-panel">
      <div className="section-header">
        <div>
          <h2>Service health</h2>
          <p>Estado del backend y del adaptador del agente.</p>
        </div>
        <button type="button" className="button button--outline" onClick={onRefresh}>
          Refresh
        </button>
      </div>

      {!status ? <p className="muted-copy">No health data yet.</p> : null}
      {status ? (
        <dl className="health-grid">
          <div>
            <dt>Overall</dt>
            <dd>{status.status}</dd>
          </div>
          <div>
            <dt>Database</dt>
            <dd>{status.database}</dd>
          </div>
          <div>
            <dt>Agent</dt>
            <dd>{status.agent}</dd>
          </div>
          <div>
            <dt>Detail</dt>
            <dd>{status.agent_detail}</dd>
          </div>
        </dl>
      ) : null}
    </section>
  );
}

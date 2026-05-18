import type { HistoryItem } from "@/lib/types";

type HistoryPanelProps = {
  items: HistoryItem[];
  isLoading: boolean;
};

export function HistoryPanel({ items, isLoading }: HistoryPanelProps) {
  return (
    <section className="surface-panel">
      <div className="section-header">
        <div>
          <h2>Historial</h2>
          <p>Registro persistido desde SQLite.</p>
        </div>
      </div>
      {isLoading ? <p className="muted-copy">Cargando historial...</p> : null}
      {!isLoading && items.length === 0 ? (
        <p className="muted-copy">Todavía no hay interacciones guardadas.</p>
      ) : null}
      <div className="history-list">
        {items.map((item, index) => (
          <article key={`${item.created_at ?? "no-date"}-${index}`} className="history-item">
            <div className="history-item__meta">
              <span>{item.status}</span>
              <span>{item.created_at ? new Date(item.created_at).toLocaleString() : "Pending"}</span>
            </div>
            <p className="history-item__question">{item.message}</p>
            <p className="history-item__answer">{item.response}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

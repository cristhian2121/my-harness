import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getHealth, getHistory } from "@/api/client";
import { AssistantChat } from "@/components/AssistantChat";
import { HealthCard } from "@/components/HealthCard";
import { HistoryPanel } from "@/components/HistoryPanel";
import { useUser } from "@/context/UserContext";
import type { HealthStatus, HistoryItem } from "@/lib/types";

export default function ChatPage() {
  const { currentUser } = useUser();
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const loadHistory = useCallback(async () => {
    if (!currentUser) {
      setHistory([]);
      return;
    }

    try {
      setErrorMessage(null);
      setIsLoadingHistory(true);
      const items = await getHistory(currentUser.username);
      setHistory(items);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "No se pudo cargar el historial.");
    } finally {
      setIsLoadingHistory(false);
    }
  }, [currentUser]);

  const loadHealth = useCallback(async () => {
    try {
      const payload = await getHealth();
      setHealth(payload);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "No se pudo consultar health.");
    }
  }, []);

  useEffect(() => {
    void loadHistory();
  }, [loadHistory]);

  useEffect(() => {
    void loadHealth();
  }, [loadHealth]);

  if (!currentUser) {
    return (
      <section className="empty-panel">
        <h1>No active user</h1>
        <p>Primero registra un usuario para poder consumir la API de chat.</p>
        <Link to="/" className="button button--primary">
          Ir a registro
        </Link>
      </section>
    );
  }

  return (
    <section className="chat-grid">
      <div className="chat-column">
        <div className="section-header">
          <div>
            <span className="eyebrow">Chat</span>
            <h1>Conversa con el agente</h1>
            <p>Usuario activo: {currentUser.username}</p>
          </div>
        </div>

        {errorMessage ? <div className="error-banner">{errorMessage}</div> : null}

        <AssistantChat username={currentUser.username} onInteractionSaved={loadHistory} />
      </div>

      <aside className="sidebar-column">
        <HealthCard status={health} onRefresh={() => void loadHealth()} />
        <HistoryPanel items={history} isLoading={isLoadingHistory} />
      </aside>
    </section>
  );
}

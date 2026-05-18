import { useCallback, useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";
import { getHealth, getHistory, validateUser } from "@/api/client";
import { AssistantChat } from "@/components/AssistantChat";
import { HealthCard } from "@/components/HealthCard";
import { HistoryPanel } from "@/components/HistoryPanel";
import { useUser } from "@/context/UserContext";
import type { HealthStatus, HistoryItem } from "@/lib/types";

type LoginFormValues = {
  username: string;
  role: string;
};

export default function ChatPage() {
  const { currentUser, setCurrentUser } = useUser();
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    defaultValues: {
      username: "",
      role: "viewer",
    },
  });

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

  const onSubmit = handleSubmit(async (values) => {
    try {
      setErrorMessage(null);
      const user = await validateUser(values);
      setCurrentUser(user);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "No se pudo validar el usuario.";
      setErrorMessage(message);
    }
  });

  if (!currentUser) {
    return (
      <section className="register-grid">
        <div className="empty-panel">
          <span className="eyebrow">Acceso</span>
          <h1>No active user</h1>
          <p>
            Si el usuario ya existe, autentícalo con su <code>username</code> y
            <code> role</code>. Si no existe, crea uno antes de abrir el chat.
          </p>
          <Link to="/" className="button button--primary">
            Ir a registro
          </Link>
        </div>

        <form className="surface-panel form-panel" onSubmit={onSubmit}>
          <div className="field-group">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              className="text-field"
              placeholder="ana"
              {...register("username", {
                required: "Username is required.",
                minLength: { value: 3, message: "Use at least 3 characters." },
              })}
            />
            {errors.username ? <span className="field-error">{errors.username.message}</span> : null}
          </div>

          <div className="field-group">
            <label htmlFor="role">Role</label>
            <input
              id="role"
              className="text-field"
              placeholder="viewer"
              {...register("role", {
                required: "Role is required.",
                minLength: { value: 2, message: "Use at least 2 characters." },
              })}
            />
            {errors.role ? <span className="field-error">{errors.role.message}</span> : null}
          </div>

          {errorMessage ? <div className="error-banner">{errorMessage}</div> : null}

          <button type="submit" className="button button--primary" disabled={isSubmitting}>
            {isSubmitting ? "Validating..." : "Iniciar sesión"}
          </button>
        </form>
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

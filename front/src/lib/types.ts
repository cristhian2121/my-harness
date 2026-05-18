export type UserRecord = {
  username: string;
  role: string;
  created_at?: string | null;
};

export type AskResult = {
  username: string;
  message: string;
  response: string;
  status: "answered" | "blocked";
  created_at?: string | null;
};

export type HistoryItem = {
  message: string;
  response: string;
  status: "answered" | "blocked";
  created_at?: string | null;
};

export type HealthStatus = {
  status: "ok" | "degraded";
  database: string;
  agent: string;
  agent_detail: string;
};

import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { UserProvider } from "@/context/UserContext";
import ChatPage from "./ChatPage";
import { getHealth, getHistory } from "@/api/client";

vi.mock("@/api/client", () => ({
  getHealth: vi.fn(),
  getHistory: vi.fn(),
}));

vi.mock("@/components/AssistantChat", () => ({
  AssistantChat: ({ username }: { username: string | null }) => (
    <div>assistant-chat:{username}</div>
  ),
}));

describe("ChatPage", () => {
  beforeEach(() => {
    window.localStorage.setItem(
      "pepe-grillo-user",
      JSON.stringify({ username: "ana", role: "viewer" }),
    );
  });

  afterEach(() => {
    window.localStorage.clear();
  });

  it("loads health and history for the active user", async () => {
    vi.mocked(getHealth).mockResolvedValue({
      status: "ok",
      database: "ok",
      agent: "ok",
      agent_detail: "fake-agent",
    });
    vi.mocked(getHistory).mockResolvedValue([
      {
        message: "Hola",
        response: "Respuesta",
        status: "answered",
        created_at: "2026-05-17T10:00:00Z",
      },
    ]);

    render(
      <MemoryRouter>
        <UserProvider>
          <ChatPage />
        </UserProvider>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(getHistory).toHaveBeenCalledWith("ana");
    });

    expect(await screen.findByText("assistant-chat:ana")).toBeInTheDocument();
    expect(await screen.findByText("Respuesta")).toBeInTheDocument();
    expect(await screen.findByText("fake-agent")).toBeInTheDocument();
  });
});

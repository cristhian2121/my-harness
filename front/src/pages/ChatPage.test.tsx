import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { UserProvider } from "@/context/UserContext";
import ChatPage from "./ChatPage";
import { getHealth, getHistory, validateUser } from "@/api/client";

vi.mock("@/api/client", () => ({
  getHealth: vi.fn(),
  getHistory: vi.fn(),
  validateUser: vi.fn(),
}));

vi.mock("@/components/AssistantChat", () => ({
  AssistantChat: ({ username }: { username: string | null }) => (
    <div>assistant-chat:{username}</div>
  ),
}));

describe("ChatPage", () => {
  beforeEach(() => {
    vi.mocked(getHealth).mockResolvedValue({
      status: "ok",
      database: "ok",
      agent: "ok",
      agent_detail: "fake-agent",
    });
  });

  afterEach(() => {
    window.localStorage.clear();
  });

  it("loads health and history for the active user", async () => {
    window.localStorage.setItem(
      "pepe-grillo-user",
      JSON.stringify({ username: "ana", role: "viewer" }),
    );
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

  it("shows register link and validates an existing user from chat", async () => {
    vi.mocked(getHistory).mockResolvedValue([]);
    vi.mocked(validateUser).mockResolvedValue({
      username: "ana",
      role: "viewer",
    });

    render(
      <MemoryRouter>
        <UserProvider>
          <ChatPage />
        </UserProvider>
      </MemoryRouter>,
    );

    expect(screen.getByRole("link", { name: /ir a registro/i })).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText(/username/i), {
      target: { value: "ana" },
    });
    fireEvent.change(screen.getByLabelText(/role/i), {
      target: { value: "viewer" },
    });
    fireEvent.click(screen.getByRole("button", { name: /iniciar sesión/i }));

    await waitFor(() => {
      expect(validateUser).toHaveBeenCalledWith({
        username: "ana",
        role: "viewer",
      });
    });

    expect(await screen.findByText("assistant-chat:ana")).toBeInTheDocument();
  });

  it("shows a visible error when existing-user validation fails", async () => {
    vi.mocked(validateUser).mockRejectedValue(new Error("The provided username and role do not match."));

    render(
      <MemoryRouter>
        <UserProvider>
          <ChatPage />
        </UserProvider>
      </MemoryRouter>,
    );

    fireEvent.change(screen.getByLabelText(/username/i), {
      target: { value: "ana" },
    });
    fireEvent.change(screen.getByLabelText(/role/i), {
      target: { value: "admin" },
    });
    fireEvent.click(screen.getByRole("button", { name: /iniciar sesión/i }));

    expect(
      await screen.findByText("The provided username and role do not match."),
    ).toBeInTheDocument();
  });
});

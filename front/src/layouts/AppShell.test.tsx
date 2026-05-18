import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { UserProvider } from "@/context/UserContext";
import { AppShell } from "./AppShell";

describe("AppShell", () => {
  afterEach(() => {
    window.localStorage.clear();
  });

  it("logs out the active user and redirects to register", async () => {
    window.localStorage.setItem(
      "pepe-grillo-user",
      JSON.stringify({ username: "ana", role: "viewer" }),
    );

    render(
      <MemoryRouter initialEntries={["/chat"]}>
        <UserProvider>
          <AppShell>
            <Routes>
              <Route path="/" element={<div>register-page</div>} />
              <Route path="/chat" element={<div>chat-page</div>} />
            </Routes>
          </AppShell>
        </UserProvider>
      </MemoryRouter>,
    );

    expect(await screen.findByText("ana · viewer")).toBeInTheDocument();
    expect(screen.getByText("chat-page")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /cerrar sesion/i }));

    expect(await screen.findByText("register-page")).toBeInTheDocument();
    expect(screen.getByText("No user selected")).toBeInTheDocument();
    expect(window.localStorage.getItem("pepe-grillo-user")).toBeNull();
  });
});

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { UserProvider } from "@/context/UserContext";
import RegisterPage from "./RegisterPage";
import { registerUser } from "@/api/client";

vi.mock("@/api/client", () => ({
  registerUser: vi.fn(),
}));

describe("RegisterPage", () => {
  it("submits the register form and redirects to chat", async () => {
    vi.mocked(registerUser).mockResolvedValue({
      username: "ana",
      role: "viewer",
    });

    render(
      <MemoryRouter initialEntries={["/"]}>
        <UserProvider>
          <Routes>
            <Route path="/" element={<RegisterPage />} />
            <Route path="/chat" element={<div>chat-ready</div>} />
          </Routes>
        </UserProvider>
      </MemoryRouter>,
    );

    fireEvent.change(screen.getByLabelText(/username/i), {
      target: { value: "ana" },
    });
    fireEvent.change(screen.getByLabelText(/role/i), {
      target: { value: "viewer" },
    });
    fireEvent.click(screen.getByRole("button", { name: /create user/i }));

    await waitFor(() => {
      expect(registerUser).toHaveBeenCalledWith({
        username: "ana",
        role: "viewer",
      });
    });

    expect(await screen.findByText("chat-ready")).toBeInTheDocument();
  });
});

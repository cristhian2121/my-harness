import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { AssistantChat } from "./AssistantChat";
import { askQuestion } from "@/api/client";

vi.mock("@/api/client", () => ({
  askQuestion: vi.fn(),
}));

const originalGetComputedStyle = window.getComputedStyle;

class ResizeObserverMock {
  observe(target: Element) {
    this.callback(
      [
        {
          target,
          contentRect: DOMRectReadOnly.fromRect(),
        } as ResizeObserverEntry,
      ],
      this as unknown as ResizeObserver,
    );
  }

  unobserve() {}

  disconnect() {}

  constructor(private readonly callback: ResizeObserverCallback) {}
}

describe("AssistantChat", () => {
  beforeAll(() => {
    vi.stubGlobal("ResizeObserver", ResizeObserverMock);
    Object.defineProperty(Element.prototype, "scrollTo", {
      configurable: true,
      value: vi.fn(),
    });
    vi.spyOn(window, "getComputedStyle").mockImplementation((element) => {
      const style = originalGetComputedStyle(element);

      if (!(element instanceof HTMLTextAreaElement)) {
        return style;
      }

      return {
        ...style,
        borderBottomWidth: "1px",
        borderLeftWidth: "1px",
        borderRightWidth: "1px",
        borderTopWidth: "1px",
        boxSizing: "border-box",
        fontFamily: "sans-serif",
        fontSize: "16px",
        fontStyle: "normal",
        fontWeight: "400",
        letterSpacing: "normal",
        lineHeight: "20px",
        paddingBottom: "0px",
        paddingLeft: "0px",
        paddingRight: "0px",
        paddingTop: "0px",
        scrollbarGutter: "auto",
        tabSize: "8",
        textIndent: "0px",
        textRendering: "auto",
        textTransform: "none",
        width: "400px",
        wordBreak: "normal",
        wordSpacing: "0px",
      } as CSSStyleDeclaration;
    });

    Object.defineProperty(HTMLTextAreaElement.prototype, "scrollHeight", {
      configurable: true,
      get() {
        const value = this.value || this.placeholder || "x";
        const lineCount = Math.max(1, value.split("\n").length);
        return lineCount * 24;
      },
    });
  });

  afterAll(() => {
    vi.restoreAllMocks();
  });

  beforeEach(() => {
    vi.mocked(askQuestion)
      .mockResolvedValueOnce({
        username: "ana",
        message: "Primera linea\nSegunda linea\nTercera linea",
        response: "Respuesta 1",
        status: "answered",
      })
      .mockResolvedValueOnce({
        username: "ana",
        message: "Cuarta linea\nQuinta linea",
        response: "Respuesta 2",
        status: "answered",
      });
  });

  it("resets composer height after multiple submitted questions", async () => {
    const onInteractionSaved = vi.fn();

    render(
      <AssistantChat username="ana" onInteractionSaved={onInteractionSaved} />,
    );

    const composerInput = screen.getByPlaceholderText(
      "Escribe tu pregunta",
    ) as HTMLTextAreaElement;
    const sendButton = screen.getByRole("button", { name: "Enviar" });

    const firstQuestion = "Primera linea\nSegunda linea\nTercera linea";
    fireEvent.change(composerInput, { target: { value: firstQuestion } });

    const expandedHeight = Number.parseFloat(composerInput.style.height);
    expect(expandedHeight).toBeGreaterThan(26);

    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(askQuestion).toHaveBeenCalledWith(
        { username: "ana", message: firstQuestion },
        expect.any(AbortSignal),
      );
    });

    expect(await screen.findByText("Respuesta 1")).toBeInTheDocument();

    await waitFor(() => {
      expect(composerInput).toHaveValue("");
    });

    const firstResetHeight = Number.parseFloat(composerInput.style.height);
    expect(firstResetHeight).toBeGreaterThan(0);
    expect(firstResetHeight).toBeLessThan(expandedHeight);

    const secondQuestion = "Cuarta linea\nQuinta linea";
    fireEvent.change(composerInput, { target: { value: secondQuestion } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(askQuestion).toHaveBeenNthCalledWith(
        2,
        { username: "ana", message: secondQuestion },
        expect.any(AbortSignal),
      );
    });

    expect(await screen.findByText("Respuesta 2")).toBeInTheDocument();

    await waitFor(() => {
      expect(composerInput).toHaveValue("");
    });

    const secondResetHeight = Number.parseFloat(composerInput.style.height);
    expect(secondResetHeight).toBe(firstResetHeight);
    expect(document.querySelector("[data-aui-top-anchor-reserve]")).toBeNull();
    expect(onInteractionSaved).toHaveBeenCalledTimes(2);
  });
});

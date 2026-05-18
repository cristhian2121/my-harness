import {
  AssistantRuntimeProvider,
  AuiIf,
  ComposerPrimitive,
  MessagePrimitive,
  ThreadPrimitive,
  useLocalRuntime,
  type ChatModelAdapter,
} from "@assistant-ui/react";
import { useMemo } from "react";
import { askQuestion } from "@/api/client";

type AssistantChatProps = {
  username: string | null;
  onInteractionSaved: () => void | Promise<void>;
};

function RuntimeThread() {
  return (
    <ThreadPrimitive.Root className="chat-thread">
      <ThreadPrimitive.Viewport className="chat-thread__viewport">
        <AuiIf condition={(state) => state.thread.isEmpty}>
          <div className="chat-empty-state">
            <h2>Haz tu primera pregunta</h2>
            <p>El backend validará el mensaje antes de consultar al agente.</p>
          </div>
        </AuiIf>

        <ThreadPrimitive.Messages>
          {({ message }) =>
            message.role === "user" ? <UserMessage /> : <AssistantMessage />
          }
        </ThreadPrimitive.Messages>

        <ThreadPrimitive.ViewportFooter className="chat-thread__footer">
          <Composer />
        </ThreadPrimitive.ViewportFooter>
      </ThreadPrimitive.Viewport>
    </ThreadPrimitive.Root>
  );
}

function UserMessage() {
  return (
    <MessagePrimitive.Root className="message-row message-row--user">
      <div className="message-bubble message-bubble--user">
        <MessagePrimitive.Parts />
      </div>
    </MessagePrimitive.Root>
  );
}

function AssistantMessage() {
  return (
    <MessagePrimitive.Root className="message-row">
      <div className="message-bubble">
        <MessagePrimitive.Parts />
      </div>
    </MessagePrimitive.Root>
  );
}

function Composer() {
  return (
    <ComposerPrimitive.Root className="composer">
      <ComposerPrimitive.Input
        className="composer__input"
        placeholder="Escribe tu pregunta"
        rows={1}
      />
      <div className="composer__actions">
        <ComposerPrimitive.Send className="composer__send">Enviar</ComposerPrimitive.Send>
      </div>
    </ComposerPrimitive.Root>
  );
}

export function AssistantChat({ username, onInteractionSaved }: AssistantChatProps) {
  const adapter = useMemo<ChatModelAdapter>(
    () => ({
      async run({ messages, abortSignal }) {
        if (!username) {
          throw new Error("A registered user is required.");
        }

        const latestMessage = [...messages]
          .reverse()
          .find((item) => item.role === "user");
        const prompt =
          latestMessage?.content
            .filter((part) => part.type === "text")
            .map((part) => part.text)
            .join("\n")
            .trim() ?? "";

        const result = await askQuestion({ username, message: prompt }, abortSignal);
        await onInteractionSaved();

        return {
          content: [{ type: "text", text: result.response }],
        };
      },
    }),
    [onInteractionSaved, username],
  );

  const runtime = useLocalRuntime(adapter);

  if (!username) {
    return (
      <section className="empty-panel">
        <h2>Registra un usuario primero</h2>
        <p>La vista de chat opera con el usuario activo guardado en la aplicación.</p>
      </section>
    );
  }

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <RuntimeThread />
    </AssistantRuntimeProvider>
  );
}

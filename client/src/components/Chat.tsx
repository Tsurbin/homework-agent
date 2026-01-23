import { useState, useEffect, useRef } from "react";

const systemMessage = {
  role: "assistant",
  content: "Hey there! Ask me anything and I'll forward it to the agent.",
};

export default function Chat() {
  const [messages, setMessages] = useState([systemMessage]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [promptErrorMessage, setPromptErrorMessage] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || isSending) return;

    const userMessage = { role: "user", content: input.trim() };
    const optimistic = [...messages, userMessage];
    setMessages(optimistic);
    setInput("");
    setIsSending(true);

    try {
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: userMessage.content, conversation_history: messages }),
      });

      if (!res.ok) {
        const errorData = await res.json();
        const errorMessage = errorData.errors?.map((err: any) => err.msg).join(", ") || "Unknown error";
        setPromptErrorMessage(errorMessage);
        throw new Error(errorMessage);
      }
      setPromptErrorMessage(null);

      const data = await res.json();
      const assistantMessage = {
        role: "assistant",
        content: data.response ?? "(No response provided)",
      };
      setMessages([...optimistic, assistantMessage]);
    } catch (error) {
      console.log(error);
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex h-screen max-h-screen flex-col overflow-hidden bg-slate-950">
      <header className="flex-shrink-0 border-b border-slate-800 bg-slate-900/80 px-4 py-2 backdrop-blur">
        <h1 className="text-lg font-semibold text-white">
          Homework Agent Chat
        </h1>
        <p className="text-xs text-slate-400">
          GPT-like interface powered by your in-house agent
        </p>
      </header>

      <main className="flex flex-1 flex-col gap-4 overflow-y-auto p-6 min-h-0">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${
              msg.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-lg ${
                msg.role === "user"
                  ? "bg-emerald-500/90 text-white"
                  : "bg-slate-800 text-slate-100"
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
        {isSending && (
          <div className="flex justify-start">
            <div className="rounded-2xl bg-slate-800 px-4 py-3 text-sm text-slate-400">
              Thinking…
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </main>

      <footer className="flex-shrink-0 border-t border-slate-800 bg-slate-900/80 p-4">
        <div className="flex gap-3">
          <textarea
            className="h-16 flex-1 resize-none rounded-xl border border-slate-800 bg-slate-950 px-4 py-3 text-slate-100 placeholder:text-slate-500 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            placeholder="Type your prompt and press Enter…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <button
            className="rounded-xl bg-emerald-500 px-6 text-white transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-60"
            onClick={sendMessage}
            disabled={isSending}
          >
            Send
          </button>
        </div>
        {promptErrorMessage && (
          <p className="mt-2 text-sm text-red-500">{promptErrorMessage}</p>
        )}
        <p className="mt-2 text-xs text-slate-500">
          Shift + Enter for new line • Enter to send
        </p>
      </footer>
    </div>
  );
}
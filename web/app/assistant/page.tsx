import { ChatPanel } from "@/components/ChatPanel";

export const metadata = {
  title: "Assistant · Sunday",
  description:
    "Ask Sunday's AI assistant about your portfolio, holdings, market events, and economic indicators.",
};

export default function AssistantPage() {
  return (
    <div className="container-prose space-y-6">
      <header className="space-y-2">
        <p className="label">Assistant</p>
        <h1 className="font-sans text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
          Ask about your money
        </h1>
        <p className="max-w-prose text-base leading-relaxed text-ink-muted">
          Grounded in your portfolio, fluent in the markets. Ask what changed,
          what something means, or how an indicator works — in plain English.
        </p>
      </header>
      <ChatPanel />
    </div>
  );
}

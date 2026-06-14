"use client";

import { useEffect, useRef, useState } from "react";

import { Disclaimer } from "@/components/Disclaimer";
import { sendChat, sendChatStream } from "@/lib/api";
import { formatDateTime, formatPct } from "@/lib/format";
import type { ChatGrounding, ChatMessage } from "@/lib/types";

// Starter prompts grouped by function — grouping aids discovery vs. a flat list.
const SUGGESTION_GROUPS: { label: string; items: string[] }[] = [
  {
    label: "Understand my portfolio",
    items: [
      "What's my biggest concentration risk right now?",
      "Summarise how my portfolio is split across asset classes.",
    ],
  },
  {
    label: "Explain a concept",
    items: [
      "Explain what CPI is and why it matters for my holdings.",
      "What does my unrealised P&L mean?",
    ],
  },
];

// Static follow-ups offered after each answer to lower the articulation barrier.
const FOLLOW_UPS = [
  "Explain that more simply",
  "How is this calculated?",
  "What does this mean for my risk?",
];

type DisplayMessage = ChatMessage & {
  guardrailTriggered?: boolean;
  grounding?: ChatGrounding | null;
};

const FALLBACK_DISCLAIMER =
  "The assistant provides information and education only, never personal investment advice.";

/**
 * Portfolio-grounded AI chat. Holds the conversation in local state, posts the
 * full history to /api/chat each turn, and renders a calm, readable thread.
 * The backend keeps every answer on the information-not-advice side; this UI
 * surfaces the AI disclosure, the per-answer guardrail signal, and the
 * disclaimers the API returns.
 */
export function ChatPanel() {
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [disclaimers, setDisclaimers] = useState<string[]>([]);
  const [streaming, setStreaming] = useState(true);
  const threadRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    threadRef.current?.scrollTo({ top: threadRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, pending]);

  async function submit(text: string) {
    const trimmed = text.trim();
    if (!trimmed || pending) return;

    const history = messages;
    const next: DisplayMessage[] = [...history, { role: "user", content: trimmed }];
    setMessages(next);
    setInput("");
    setError(null);
    setPending(true);
    // Send only the wire shape (role + content) — strip display metadata.
    const wire: ChatMessage[] = next.map((m) => ({ role: m.role, content: m.content }));

    try {
      if (streaming) {
        let acc = "";
        setMessages([...next, { role: "assistant", content: "" }]);
        const patchLast = (patch: Partial<DisplayMessage>) =>
          setMessages((prev) =>
            prev.map((m, i) => (i === prev.length - 1 ? { ...m, ...patch } : m)),
          );
        await sendChatStream(wire, (ev) => {
          if (ev.type === "delta") {
            acc += ev.text;
            patchLast({ content: acc });
          } else if (ev.type === "replace") {
            acc = ev.text;
            patchLast({ content: acc });
          } else if (ev.type === "done") {
            patchLast({ content: acc, guardrailTriggered: ev.guardrail_triggered, grounding: ev.grounding });
          } else if (ev.type === "error") {
            throw new Error(ev.detail);
          }
        });
      } else {
        const res = await sendChat(wire);
        setMessages([
          ...next,
          {
            role: "assistant",
            content: res.reply,
            guardrailTriggered: res.guardrail_triggered,
            grounding: res.grounding,
          },
        ]);
        setDisclaimers(res.disclaimers ?? []);
      }
    } catch (err) {
      // Roll the optimistic user turn back so they can retry.
      setMessages(history);
      setInput(trimmed);
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setPending(false);
    }
  }

  const empty = messages.length === 0;
  const lastRole = messages[messages.length - 1]?.role;
  const lastIsAssistant = !pending && lastRole === "assistant";
  const awaitingFirstToken = pending && lastRole === "user";

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <span aria-hidden className="inline-block h-1.5 w-1.5 rounded-full bg-accent" />
        <p className="label">AI assistant · information, not advice</p>
      </div>

      <div
        ref={threadRef}
        className="card flex max-h-[60vh] min-h-[320px] flex-col gap-4 overflow-y-auto p-5"
      >
        {empty ? (
          <div className="space-y-5">
            <p className="text-sm leading-relaxed text-ink-muted">
              Ask about your portfolio, a holding, a market event, or an economic
              indicator. I explain and contextualise — I don&apos;t give personal
              buy/sell advice.
            </p>
            {SUGGESTION_GROUPS.map((group) => (
              <div key={group.label} className="space-y-2">
                <p className="label">{group.label}</p>
                <div className="grid gap-2 sm:grid-cols-2">
                  {group.items.map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => submit(s)}
                      className="rounded-md border border-rule bg-surface px-3 py-2 text-left text-sm text-ink-muted transition-colors hover:border-accent/40 hover:text-ink"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          messages.map((m, i) => <Bubble key={i} message={m} />)
        )}
        {awaitingFirstToken ? (
          <div className="flex items-center gap-2 text-sm text-ink-subtle">
            <Dots />
            Thinking…
          </div>
        ) : null}

        {lastIsAssistant ? (
          <div className="flex flex-wrap gap-2 pt-1">
            {FOLLOW_UPS.map((f) => (
              <button
                key={f}
                type="button"
                onClick={() => submit(f)}
                className="rounded-full border border-rule bg-surface px-3 py-1 text-xs text-ink-muted transition-colors hover:border-accent/40 hover:text-ink"
              >
                {f}
              </button>
            ))}
          </div>
        ) : null}
      </div>

      {error ? (
        <p className="text-sm text-negative" role="alert">
          {error}
        </p>
      ) : null}

      <form
        onSubmit={(e) => {
          e.preventDefault();
          void submit(input);
        }}
        className="space-y-2"
      >
        <div className="flex items-end gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                void submit(input);
              }
            }}
            rows={2}
            placeholder="Ask about your portfolio or the markets…"
            className="min-h-[44px] flex-1 resize-none rounded-md border border-rule bg-surface px-3 py-2 text-sm text-ink outline-none placeholder:text-ink-subtle focus:border-accent/50"
          />
          <button type="submit" className="btn btn-primary" disabled={pending || !input.trim()}>
            Send
          </button>
        </div>
        <div className="flex items-center justify-between gap-3">
          <p className="text-xs text-ink-subtle">
            Information and education only — never a personal recommendation. Verify figures before acting.
          </p>
          <label className="inline-flex flex-none items-center gap-1.5 text-xs text-ink-subtle">
            <input
              type="checkbox"
              checked={streaming}
              onChange={(e) => setStreaming(e.target.checked)}
              className="accent-accent"
            />
            Stream
          </label>
        </div>
      </form>

      <Disclaimer extra={(disclaimers.length > 0 ? disclaimers : [FALLBACK_DISCLAIMER]).join(" ")} />
    </div>
  );
}

function Bubble({ message }: { message: DisplayMessage }) {
  const isUser = message.role === "user";
  return (
    <div className={`flex flex-col gap-1 ${isUser ? "items-end" : "items-start"}`}>
      <div
        className={
          isUser
            ? "max-w-[85%] rounded-2xl rounded-br-sm bg-ink px-4 py-2.5 text-sm leading-relaxed text-bg"
            : "max-w-[85%] whitespace-pre-line rounded-2xl rounded-bl-sm border border-rule bg-surface px-4 py-2.5 text-sm leading-relaxed text-ink"
        }
      >
        {message.content}
      </div>
      {message.guardrailTriggered ? (
        <span className="inline-flex items-center gap-1.5 text-xs text-ink-subtle">
          <span aria-hidden className="inline-block h-1 w-1 rounded-full bg-warn" />
          Reframed to stay information-only
        </span>
      ) : null}
      {!isUser && message.grounding ? <GroundingPanel grounding={message.grounding} /> : null}
    </div>
  );
}

function GroundingPanel({ grounding }: { grounding: ChatGrounding }) {
  const hasContent = grounding.holdings.length > 0 || grounding.facts.length > 0;
  if (!hasContent) return null;

  const asOf = grounding.as_of ? formatDateTime(grounding.as_of) : null;

  return (
    <details className="max-w-[85%] rounded-md border border-rule bg-surface-2/50 px-3 py-2 text-xs">
      <summary className="cursor-pointer text-ink-muted">
        Based on your portfolio{asOf ? ` · as of ${asOf}` : ""}
      </summary>
      <div className="mt-2 space-y-2 text-ink-muted">
        {grounding.facts.length > 0 ? (
          <ul className="space-y-0.5">
            {grounding.facts.map((f) => (
              <li key={f}>{f}</li>
            ))}
          </ul>
        ) : null}
        {grounding.holdings.length > 0 ? (
          <ul className="flex flex-wrap gap-x-3 gap-y-1">
            {grounding.holdings.map((h) => (
              <li key={h.ticker} className="font-mono tabular-nums">
                <span className="text-ink">{h.ticker}</span>{" "}
                <span className="text-ink-subtle">{formatPct(h.weight_pct)}</span>
              </li>
            ))}
          </ul>
        ) : null}
        <p className="text-ink-subtle">These figures are computed server-side, not by the AI.</p>
      </div>
    </details>
  );
}

function Dots() {
  return (
    <span className="inline-flex gap-1">
      <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-ink-subtle" />
      <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-ink-subtle [animation-delay:150ms]" />
      <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-ink-subtle [animation-delay:300ms]" />
    </span>
  );
}

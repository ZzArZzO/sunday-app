import type { ReactNode } from "react";

/**
 * Renders the narrow markdown subset the briefing generator actually emits
 * (api/app/services/briefing_composer.py): `**bold**`, `_italic_`, `- ` bullet
 * lists, and blank-line paragraph breaks. Builds real React elements rather
 * than injecting HTML, so there's no sanitization to get wrong even though
 * some content (tickers, position data) ultimately traces back to a CSV a
 * user imported.
 */
export function MarkdownLite({ markdown }: { markdown: string }) {
  const blocks = markdown.split(/\n\n+/).filter((b) => b.trim());

  return (
    <>
      {blocks.map((block, i) => {
        const lines = block.split("\n").filter((l) => l.trim());
        const isList = lines.length > 0 && lines.every((l) => l.trim().startsWith("- "));

        if (isList) {
          return (
            <ul key={i} className="list-disc space-y-1 pl-5">
              {lines.map((line, j) => (
                <li key={j}>{renderInline(line.trim().replace(/^- /, ""), `${i}-${j}`)}</li>
              ))}
            </ul>
          );
        }

        return <p key={i}>{renderInline(block, `${i}`)}</p>;
      })}
    </>
  );
}

function renderInline(text: string, keyPrefix: string): ReactNode[] {
  const parts: ReactNode[] = [];
  const pattern = /\*\*(.+?)\*\*|_(.+?)_/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  let idx = 0;

  while ((match = pattern.exec(text)) !== null) {
    if (match.index > lastIndex) parts.push(text.slice(lastIndex, match.index));
    if (match[1] !== undefined) {
      parts.push(<strong key={`${keyPrefix}-${idx++}`}>{match[1]}</strong>);
    } else if (match[2] !== undefined) {
      parts.push(<em key={`${keyPrefix}-${idx++}`}>{match[2]}</em>);
    }
    lastIndex = pattern.lastIndex;
  }
  if (lastIndex < text.length) parts.push(text.slice(lastIndex));
  return parts;
}

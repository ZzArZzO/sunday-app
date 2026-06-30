// Beachhead-set broker export guides. The export paths live deep in each
// broker's menus, so the import wizard holds the user's hand with a short,
// honest step list. Sourced from docs/business/BROKER_IMPORT_RESEARCH.md.

export interface Broker {
  id: string;
  name: string;
  blurb: string; // one-line "what you'll get"
  steps: string[]; // 2–4 export steps
  note?: string; // gotcha (delimiter, what's included)
  primary?: boolean; // beachhead priority — surfaced first
}

export const BROKERS: Broker[] = [
  {
    id: "trade_republic",
    name: "Trade Republic",
    blurb: "One CSV covers stocks, ETFs and crypto — buys, sells and dividends.",
    steps: [
      "Open the app → Profile → Account Statements.",
      "Tap Transaction Export → Share.",
      "Choose All transactions (or a period) → Create, then send the CSV here.",
    ],
    note: "Includes crypto in the same file — no separate entry needed.",
    primary: true,
  },
  {
    id: "scalable",
    name: "Scalable Capital",
    blurb: "Transactions export from a broker (PRIME) account.",
    steps: [
      "Go to Transactions in the web app or mobile.",
      "Use the filter to pick a period (or all).",
      "Click Export CSV and upload it here.",
    ],
    primary: true,
  },
  {
    id: "degiro",
    name: "DEGIRO",
    blurb: "Account transactions, including FX conversions.",
    steps: [
      "Open Inbox → Account Statement (or Transactions).",
      "Pick a date range.",
      "Export as CSV and upload it here.",
    ],
    note: "DEGIRO exports are semicolon-separated — that's handled automatically.",
  },
  {
    id: "trading212",
    name: "Trading 212",
    blurb: "Transaction history including dividends.",
    steps: [
      "Go to History in the app.",
      "Tap Export → choose a date range.",
      "Download the CSV and upload it here.",
    ],
  },
  {
    id: "ibkr",
    name: "Interactive Brokers",
    blurb: "Flex Query export for full control (power users).",
    steps: [
      "In Client Portal: Performance & Reports → Flex Queries.",
      "Create a query including Trades (date, symbol, ISIN, quantity, price, fees).",
      "Run it as CSV and upload the result here.",
    ],
    note: "Make sure your query includes quantity, price and date columns.",
  },
  {
    id: "other",
    name: "Other / generic CSV",
    blurb: "Any export with date, type, ticker, quantity and price columns.",
    steps: [
      "Export your transaction history as CSV from your broker.",
      "Make sure it has date, type, ticker, quantity and price columns.",
      "Drop it in — you'll see exactly what we parsed before importing.",
    ],
  },
];

export function getBroker(id: string): Broker | undefined {
  return BROKERS.find((b) => b.id === id);
}

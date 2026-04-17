"use client";

import { useState, useRef, useEffect } from "react";
import {
  Send,
  Terminal,
  Square,
  Package,
  Sparkles,
  Tag,
  DollarSign,
  Layers,
  Image as ImageIcon,
  ChevronRight,
  Zap,
  SearchX,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type Message = {
  role: "user" | "assistant";
  content: string;
  cypher?: string;
  context?: any[];
};

/* ─────────────────────────────────────────────
 * Extract product cards from the Markdown reply
 * so we can display them visually on the right panel.
 * ──────────────────────────────────────────── */
type ProductCard = {
  name: string;
  description: string;
  price: string;
  image: string;
  features: string[];
};

function parseProductsFromMarkdown(md: string): ProductCard[] {
  const cards: ProductCard[] = [];
  // Split by --- or horizontal rules (also handle lines like "---" with surrounding whitespace)
  const blocks = md.split(/\n-{3,}\n|\n\*{3,}\n|\n_{3,}\n/);

  for (const block of blocks) {
    // Match both formats:
    //   **產品名稱 (Product)：** Value      (colon inside bold)
    //   **產品名稱 (Product)**: Value        (colon outside bold)
    //   - **產品名稱 (Product)**: Value      (with list prefix)
    //   產品名稱 (Product): Value            (no bold at all)
    const nameMatch = block.match(
      /\*{0,2}產品名稱\s*(?:\(Product\))?\s*[：:]\s*\*{0,2}\s*(.+)/
    );
    const descMatch = block.match(
      /\*{0,2}特點描述\s*(?:\(Description\))?\s*[：:]\s*\*{0,2}\s*(.+)/
    );
    const priceMatch = block.match(
      /\*{0,2}價格參考\s*(?:\(Price\))?\s*[：:]\s*\*{0,2}\s*\$?([\d.,]+)/
    );
    // Match both ![alt](url) and ![[alt]](url) patterns
    const imgMatch = block.match(/!\[+.*?\]+\((https?:\/\/[^\s)]+)\)/);

    if (nameMatch) {
      // Extract knowledge-graph features like [Brand], [Feature], etc. from the text
      const features: string[] = [];
      // Try to gather any bullet points as features (but skip the known fields)
      const bulletList = block.match(/[-•]\s+(.+)/g);
      if (bulletList) {
        bulletList
          .filter((b) => !b.match(/產品名稱|特點描述|價格參考/))
          .slice(0, 4)
          .forEach((b) => {
            features.push(b.replace(/^[-•]\s+/, "").trim());
          });
      }

      cards.push({
        name: nameMatch[1].trim().replace(/\*+/g, ""),
        description: descMatch ? descMatch[1].trim().replace(/\*+/g, "") : "",
        price: priceMatch ? priceMatch[1].trim() : "N/A",
        image: imgMatch ? imgMatch[1] : "",
        features,
      });
    }
  }

  return cards;
}

/* ─────────────────────────────────────────────
 * Strip product detail blocks from markdown
 * so the left chat only shows conversational text.
 * ──────────────────────────────────────────── */
function stripProductInfo(md: string): string {
  // Remove lines that contain the product field labels (much simpler and more robust regex)
  let stripped = md.replace(/^.*產品名稱.*$/gm, "");
  stripped = stripped.replace(/^.*特點描述.*$/gm, "");
  stripped = stripped.replace(/^.*價格參考.*$/gm, "");
  // Remove markdown images
  stripped = stripped.replace(/^!\[.*?\].*$/gm, "");
  // Remove horizontal rules
  stripped = stripped.replace(/^-{3,}$/gm, "");
  // Collapse multiple blank lines into one
  stripped = stripped.replace(/\n{3,}/g, "\n\n");
  return stripped.trim();
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        'Welcome to the **Enterprise GraphRAG** debug terminal.\n\nType your semantic query below to invoke the Hybrid Retriever. Examples:\n\n`> find me hiking gear with high durability`\n\n`> 推薦適合旅行的輕量皮革產品`',
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [products, setProducts] = useState<ProductCard[]>([]);
  const [selectedProduct, setSelectedProduct] = useState<number>(0);
  const [queryLabel, setQueryLabel] = useState<string>("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { role: "user" as const, content: input };
    setMessages((prev) => [...prev, userMessage]);
    setQueryLabel(input);
    setInput("");
    setIsLoading(true);
    setProducts([]);
    setSelectedProduct(0);

    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage.content }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) throw new Error("API responded with an error");

      const data = await response.json();
      const assistantMsg: Message = {
        role: "assistant",
        content: data.reply,
        cypher: data.cypher_query,
        context: data.context,
      };
      setMessages((prev) => [...prev, assistantMsg]);

      // Prefer structured product data from backend context; fallback to markdown parsing
      const contextProducts: ProductCard[] = (data.context || [])
        .filter((p: any) => p.name)
        .map((p: any) => ({
          name: p.name,
          description: p.description || "",
          price: p.price != null ? String(p.price) : "N/A",
          image: p.image || "",
          features: (p.knowledge || [])
            .filter((k: any) => k.neighbor)
            .slice(0, 4)
            .map((k: any) => `${k.type || k.relation}: ${k.neighbor}`),
        }));

      const parsed = contextProducts.length > 0
        ? contextProducts
        : parseProductsFromMarkdown(data.reply);
      setProducts(parsed);
      if (parsed.length > 0) setSelectedProduct(0);
    } catch (error: any) {
      if (error.name === "AbortError") {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: "> **Aborted:** Query stopped by user." },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content:
              "> **Error:** Failed to connect to local API backend. Verify Neo4j & FastAPI are live.",
          },
        ]);
      }
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };

  const handleStop = () => {
    if (abortControllerRef.current) abortControllerRef.current.abort();
  };

  return (
    <main className="flex h-[calc(100vh-4rem)] overflow-hidden">
      {/* ═══════════════════════════════════════════════
       *  LEFT PANEL — Chat Interface
       * ═══════════════════════════════════════════════ */}
      <div className="flex flex-col w-full lg:w-[40%] border-r border-[#1E293B] relative">
        {/* Chat Header */}
        <div className="flex items-center gap-3 px-6 py-4 border-b border-[#1E293B] bg-[rgba(11,17,32,0.6)] backdrop-blur-md">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <h2 className="text-sm font-semibold text-[var(--color-text-heading)] tracking-wide">
            Hybrid Retrieval Engine
          </h2>
          <span className="text-[10px] text-[var(--color-text-muted)] font-mono bg-[#1E293B] px-2 py-0.5 rounded-full">
            LIVE
          </span>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6 scrollbar-hide">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[90%] rounded-xl overflow-hidden flex ${
                  msg.role === "user"
                    ? "bg-gradient-to-br from-[#1E293B] to-[#0F172A] border border-slate-700/50"
                    : ""
                }`}
              >
                {msg.role === "assistant" && (
                  <div className="w-0.5 bg-gradient-to-b from-[var(--color-accent)] to-transparent rounded-full mr-4 shrink-0" />
                )}

                <div
                  className={`py-3.5 ${msg.role === "user" ? "px-5" : "pl-0 pr-4"} text-[var(--color-text-body)]`}
                >
                  <div className="prose prose-invert prose-slate prose-a:text-[var(--color-accent)] max-w-none text-sm leading-relaxed">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {msg.role === "assistant" ? stripProductInfo(msg.content) : msg.content}
                    </ReactMarkdown>
                  </div>

                  {msg.cypher && (
                    <div className="mt-4 rounded-lg border border-[#1E293B] bg-[#0B1120] overflow-hidden">
                      <div className="flex items-center px-3 py-1.5 border-b border-[#1E293B] bg-[#0F172A]">
                        <Terminal size={12} className="text-emerald-400 mr-2" />
                        <span className="text-[10px] text-slate-500 font-mono">
                          cypher
                        </span>
                      </div>
                      <pre className="p-3 text-xs font-mono text-emerald-400 overflow-x-auto">
                        <code>{msg.cypher}</code>
                      </pre>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="w-0.5 bg-gradient-to-b from-[var(--color-accent)] to-transparent rounded-full mr-4 shrink-0 animate-pulse" />
              <div className="py-3 text-[var(--color-text-muted)] flex items-center gap-2">
                <div className="flex gap-1">
                  <span className="w-1.5 h-1.5 bg-[var(--color-accent)] rounded-full animate-bounce [animation-delay:0ms]" />
                  <span className="w-1.5 h-1.5 bg-[var(--color-accent)] rounded-full animate-bounce [animation-delay:150ms]" />
                  <span className="w-1.5 h-1.5 bg-[var(--color-accent)] rounded-full animate-bounce [animation-delay:300ms]" />
                </div>
                <span className="text-xs font-mono">
                  Traversing knowledge graph...
                </span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-[#1E293B] bg-[rgba(11,17,32,0.6)] backdrop-blur-md">
          <div className="relative group">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-cyan-500/20 to-sky-500/20 rounded-xl blur opacity-0 group-hover:opacity-100 transition duration-500" />
            <div className="relative flex items-center bg-[#1E293B] border border-slate-700/50 rounded-xl overflow-hidden focus-within:border-[var(--color-accent)] transition-colors">
              <div className="pl-4 text-slate-600 font-mono font-bold text-sm">
                {">"}
              </div>
              <input
                type="text"
                className="flex-1 bg-transparent border-none outline-none px-3 py-3.5 text-sm text-[var(--color-text-heading)] placeholder-slate-600 font-mono"
                placeholder="Query the knowledge graph..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.nativeEvent.isComposing)
                    handleSendMessage();
                }}
              />
              {isLoading ? (
                <button
                  onClick={handleStop}
                  className="mr-2 bg-[#0F172A] hover:bg-red-950/50 text-red-400 p-2 rounded-lg border border-red-900/30 transition-colors"
                >
                  <Square size={14} fill="currentColor" />
                </button>
              ) : (
                <button
                  onClick={handleSendMessage}
                  disabled={!input.trim()}
                  className="mr-2 bg-[#0F172A] hover:bg-[var(--color-accent)]/10 text-slate-400 hover:text-[var(--color-accent)] p-2 rounded-lg border border-[#1E293B] transition-all disabled:opacity-20 disabled:hover:bg-[#0F172A]"
                >
                  <Send size={14} />
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════
       *  RIGHT PANEL — Results Inspector
       * ═══════════════════════════════════════════════ */}
      <div className="hidden lg:flex flex-col w-[60%] bg-[#0B1120] overflow-hidden">
        {/* Panel Header */}
        <div className="flex items-center gap-3 px-6 py-4 border-b border-[#1E293B]">
          <Sparkles size={16} className="text-amber-400" />
          <h2 className="text-sm font-semibold text-[var(--color-text-heading)] tracking-wide">
            Retrieved Products
          </h2>
          {products.length > 0 && (
            <span className="text-[10px] text-emerald-400 font-mono bg-emerald-950/50 border border-emerald-800/30 px-2 py-0.5 rounded-full">
              {products.length} results
            </span>
          )}
        </div>

        {/* Results Content */}
        <div className="flex-1 overflow-y-auto scrollbar-hide">
          {products.length === 0 && !isLoading ? (
            /* Empty State */
            <div className="flex flex-col items-center justify-center h-full text-center px-12 gap-4">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-[#1E293B] to-[#0F172A] border border-slate-700/30 flex items-center justify-center">
                <SearchX size={32} className="text-slate-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-[var(--color-text-heading)] mb-1">
                  No products retrieved
                </p>
                <p className="text-xs text-[var(--color-text-muted)] leading-relaxed max-w-[260px]">
                  Send a query in the chat to search the knowledge graph.
                  Products will appear here with full metadata.
                </p>
              </div>
              <div className="flex flex-wrap gap-2 mt-2 justify-center">
                {[
                  "hiking gear",
                  "皮革產品",
                  "ergonomic office",
                ].map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => {
                      setInput(suggestion);
                    }}
                    className="text-[10px] font-mono text-[var(--color-accent)] bg-[var(--color-accent)]/5 border border-[var(--color-accent)]/20 rounded-full px-3 py-1 hover:bg-[var(--color-accent)]/10 transition-colors"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          ) : isLoading ? (
            /* Loading State */
            <div className="flex flex-col items-center justify-center h-full gap-4">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[#1E293B] to-[#0F172A] border border-slate-700/30 flex items-center justify-center">
                <Zap
                  size={24}
                  className="text-[var(--color-accent)] animate-pulse"
                />
              </div>
              <div className="text-center">
                <p className="text-sm font-medium text-[var(--color-text-heading)] mb-1">
                  Searching knowledge graph
                </p>
                <p className="text-[10px] font-mono text-[var(--color-text-muted)]">
                  Vector KNN + BM25 + Cypher expansion
                </p>
              </div>
              {/* Pulsing skeleton cards */}
              <div className="w-full px-6 space-y-3 mt-2">
                {[1, 2, 3].map((i) => (
                  <div
                    key={i}
                    className="h-24 rounded-xl bg-[#1E293B]/50 border border-slate-700/20 animate-pulse"
                    style={{ animationDelay: `${i * 150}ms` }}
                  />
                ))}
              </div>
            </div>
          ) : (
            /* Product Cards — Full Detail View */
            <div className="p-4 space-y-4">
              {queryLabel && (
                <div className="flex items-center gap-2 px-2 pb-2 mb-1">
                  <ChevronRight size={12} className="text-[var(--color-accent)]" />
                  <span className="text-[11px] font-mono text-[var(--color-text-muted)] truncate">
                    {queryLabel}
                  </span>
                </div>
              )}

              {products.map((product, idx) => (
                <div
                  key={idx}
                  className="rounded-xl border border-slate-700/30 bg-gradient-to-br from-[#1E293B]/60 to-[#0F172A]/80 overflow-hidden transition-all duration-300 hover:border-slate-600/50"
                >
                  {/* Product Image — Full Width */}
                  {product.image ? (
                    <div className="w-full aspect-video overflow-hidden bg-[#0F172A] border-b border-slate-700/20">
                      <img
                        src={product.image}
                        alt={product.name}
                        className="w-full h-full object-cover hover:scale-105 transition-transform duration-700"
                        onError={(e) => {
                          (e.target as HTMLImageElement).parentElement!.style.display = "none";
                        }}
                      />
                    </div>
                  ) : (
                    <div className="w-full h-32 bg-gradient-to-br from-[#1E293B] to-[#0F172A] border-b border-slate-700/20 flex items-center justify-center">
                      <Package size={36} className="text-slate-600" />
                    </div>
                  )}

                  {/* Product Details - Formatted exactly as requested */}
                  <div className="p-5 space-y-4">
                    <p className="text-sm text-[var(--color-text-body)]">
                      <strong className="text-[var(--color-text-heading)]">產品名稱 (Product):</strong> {product.name}
                    </p>
                    
                    {product.description && (
                      <p className="text-sm text-[var(--color-text-body)] leading-relaxed">
                        <strong className="text-[var(--color-text-heading)]">特點描述 (Description):</strong> {product.description}
                      </p>
                    )}
                    
                    {product.price !== "N/A" && (
                      <p className="text-sm text-[var(--color-text-body)]">
                        <strong className="text-[var(--color-text-heading)]">價格參考 (Price):</strong> ${product.price}
                      </p>
                    )}

                    {/* Knowledge Graph Features */}
                    {product.features.length > 0 && (
                      <div className="flex gap-2.5">
                        <Tag size={13} className="text-violet-400 shrink-0 mt-0.5" />
                        <div className="flex flex-wrap gap-1.5">
                          {product.features.map((f, fi) => (
                            <span
                              key={fi}
                              className="text-[10px] font-mono text-violet-300 bg-violet-950/30 border border-violet-800/20 rounded-full px-2 py-0.5"
                            >
                              {f}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Panel Footer Stats */}
        <div className="border-t border-[#1E293B] px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="text-[10px] font-mono text-[var(--color-text-muted)]">
              VECTOR + BM25
            </span>
            <span className="text-[10px] font-mono text-[var(--color-text-muted)]">
              K=3
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            <span className="text-[10px] font-mono text-[var(--color-text-muted)]">
              Neo4j Connected
            </span>
          </div>
        </div>
      </div>
    </main>
  );
}

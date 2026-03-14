"use client";

import React, { useEffect, useRef, useState } from "react";
import { formatDistanceToNow, parseISO } from "date-fns";
import { useAuth } from "@/context/AuthContext";
import QuickPoll from "./QuickPoll";
import "./flyout.css";

// Helper to format numbers like 2800 -> 2.8K
function formatViews(num: number): string {
  if (!num) return "0";
  if (num >= 1000000) return (num / 1000000).toFixed(1).replace(/\.0$/, "") + "M";
  if (num >= 1000) return (num / 1000).toFixed(1).replace(/\.0$/, "") + "K";
  return num.toString();
}

export default function DetailFlyout() {
  const [isOpen, setIsOpen] = useState(false);
  const viewedTopicsRef = useRef<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const [topicData, setTopicData] = useState<any>(null);
  const [seedCounts, setSeedCounts] = useState<{ viewCount?: number; commentCount?: number }>({});
  const [flyoutType, setFlyoutType] = useState<"topic" | "search" | "subscribe" | "login" | "info" | "sponsor">("topic");
  const [infoType, setInfoType] = useState<string>("");

  useEffect(() => {
    // Listen for custom open-flyout events from cards
    const handleOpenFlyout = async (e: Event) => {
      const customEvent = e as CustomEvent;
      const { id, slug, type = "topic", viewCount, commentCount, infoType: iType } = customEvent.detail;
      setSeedCounts({ viewCount, commentCount });
      
      setFlyoutType(type);
      setInfoType(iType || "");
      setIsOpen(true);
      document.body.classList.add("flyout-open");

      // Handle generic utility types instantly without fetching
      if (type !== "topic") {
        // For sponsor ads, the full ad data is in the event detail — store it so SponsorFlyoutContent can render it
        if (type === "sponsor") {
          setTopicData(customEvent.detail);
        }
        setLoading(false);
        window.history.pushState({ flyoutType: type, infoType: iType }, "", `/${type}${iType ? `/${iType}` : ""}`);
        return;
      }

      setLoading(true);
      // Update URL without reload for topics
      if (slug) {
        const currentPath = window.location.pathname;
        const newUrl = `${currentPath}?topic=${encodeURIComponent(slug)}`;
        window.history.pushState({ articleId: id, slug }, "", newUrl);
      }

      // All fetches use relative /api/ paths — proxied by Next.js to localhost:8000

      try {
        let found: any = null;

        // 1. Try direct numeric ID lookup (works for real DB topics)
        const numericId = parseInt(id, 10);
        if (!isNaN(numericId)) {
          const res = await fetch(`/api/topic/${numericId}`);
          if (res.ok) found = await res.json();
        }

        // 2. Try slug lookup (for topics opened by title slug)
        if (!found && slug) {
          const res = await fetch(`/api/topic/slug/${encodeURIComponent(slug)}`);
          if (res.ok) found = await res.json();
        }

        // 3. Fall back to home trending list (catches hero carousel topics)
        if (!found) {
          const homeRes = await fetch(`/api/home`);
          if (homeRes.ok) {
            const homeData = await homeRes.json();
            found = homeData.trending_topics?.find(
              (t: any) => String(t.id) === String(id) || (slug && t.slug === slug)
            ) || null;
          }
        }

        setTopicData(found || null);
      } catch (err) {
        console.error("Failed to fetch topic inside flyout", err);
        setTopicData(null);
      } finally {
        setLoading(false);
      }
    };

    window.addEventListener("open-flyout", handleOpenFlyout);

    // Handle back/forward browser buttons
    const handlePopState = (e: PopStateEvent) => {
      if (e.state && (e.state.articleId || e.state.flyoutType)) {
        document.body.classList.add("flyout-open");
        setIsOpen(true);
        if (e.state.flyoutType) {
          setFlyoutType(e.state.flyoutType);
        }
      } else {
        closeFlyout(false); // false means don't pushState again
      }
    };
    
    window.addEventListener("popstate", handlePopState);
    
    // Handle Escape key
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && document.body.classList.contains("flyout-open")) {
         closeFlyout(true);
      }
    };
    window.addEventListener("keydown", handleKeyDown);

    // Initial check for topic in URL (handles reloads/shared links)
    const urlParams = new URLSearchParams(window.location.search);
    const topicSlug = urlParams.get("topic");
    if (topicSlug) {
      handleOpenFlyout(new CustomEvent("open-flyout", {
        detail: { type: "topic", id: topicSlug, slug: topicSlug }
      }));
    }

    return () => {
      window.removeEventListener("open-flyout", handleOpenFlyout);
      window.removeEventListener("popstate", handlePopState);
      window.removeEventListener("keydown", handleKeyDown);
      document.body.classList.remove("flyout-open");
    };
  }, []);

  const closeFlyout = (updateHistory = true) => {
    setIsOpen(false);
    document.body.classList.remove("flyout-open");
    setTopicData(null);
    
    if (updateHistory) {
      // Clean up only the topic query parameter, preserving the current page
      const url = new URL(window.location.href);
      url.searchParams.delete("topic");
      // Also handle legacy utility paths if they are in the pathname
      const utilityPaths = ["/search", "/subscribe", "/login", "/info", "/sponsor"];
      let newPath = url.pathname;
      if (utilityPaths.some(p => newPath.startsWith(p))) {
        newPath = "/";
      }
      
      const nextUrl = url.searchParams.toString() ? `${newPath}?${url.searchParams.toString()}` : newPath;
      window.history.pushState({}, "", nextUrl);
    }
  };

  if (!isOpen) return null;

  return (
    <div id="detail-flyout" className="detail-flyout">
      <div className="flyout-overlay" onClick={() => closeFlyout(true)}></div>
      <div className="flyout-panel dark-editorial">
        <div className="flyout-header">
          <div className="logo flyout-logo-text">
            Glide<span className="accent">Intelligence</span>
          </div>
          <button className="flyout-close" onClick={() => closeFlyout(true)}>✕</button>
        </div>
        
        <div id="flyout-content" className="flyout-content-scroll">
          {flyoutType === "search" && <SearchFlyoutContent />}
          {flyoutType === "subscribe" && <SubscribeFlyoutContent />}
          {flyoutType === "login" && <LoginFlyoutContent initialIsRegistering={infoType === "register"} />}
          {flyoutType === "info" && <InfoFlyoutContent type={infoType} />}
          {flyoutType === "sponsor" && <SponsorFlyoutContent sponsorAd={topicData} />}
          
          {flyoutType === "topic" && (
            loading ? (
               <div className="flex items-center justify-center p-20 text-white/50 h-full">
                 <div className="animate-pulse flex flex-col items-center gap-4">
                   <div className="w-8 h-8 rounded-full border-t-2 border-accent animate-spin" />
                   <span>Initializing Glide Intelligence Brief...</span>
                 </div>
               </div>
            ) : !topicData ? (
               <div className="flyout-inner-wrapper">
                 <section className="topic-header-section-flyout">
                   <div className="topic-header-container-flyout">
                     <div className="topic-meta-flyout">
                       <div className="topic-badge-flyout">
                         <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="10"/></svg>
                         Intelligence
                       </div>
                     </div>
                     <h1 className="topic-title-flyout" style={{ fontSize: "2rem" }}>Synthesis In Progress</h1>
                     <p style={{ fontSize: "1.05rem", color: "#888", lineHeight: 1.7, maxWidth: "520px" }}>
                       Our Glide pipeline is still aggregating and analysing sources for this topic. 
                       Full intelligence — including sentiment breakdown, regional impacts, and source perspectives — will be available shortly.
                     </p>
                     <div style={{ marginTop: "32px", display: "flex", gap: "16px", flexWrap: "wrap" }}>
                       <button
                         className="btn-flyout btn-primary-flyout"
                         onClick={() => window.dispatchEvent(new CustomEvent("open-flyout", { detail: { type: "subscribe" } }))}
                       >
                         Subscribe for Alerts
                       </button>
                       <button
                         className="btn-flyout"
                         style={{ background: "transparent", border: "1px solid rgba(255,255,255,0.15)", color: "#aaa", padding: "12px 24px", borderRadius: "6px", cursor: "pointer", fontFamily: "var(--sans)" }}
                         onClick={() => window.history.back()}
                       >
                         ← Go Back
                       </button>
                     </div>
                   </div>
                 </section>
               </div>
            ) : (
               <FlyoutInnerContent topicData={topicData} seedViewCount={seedCounts.viewCount} seedCommentCount={seedCounts.commentCount} viewedTopicsRef={viewedTopicsRef} />
            )
          )}
        </div>
      </div>
    </div>
  );
}

// ─── UTILITY FLYOUT COMPONENTS ───

function SearchFlyoutContent() {
  const [query, setQuery] = useState("");
  const [topics, setTopics] = useState<any[]>([]);
  const [articles, setArticles] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const COLORS = ["#e74c3c", "#3498db", "#9b59b6", "#27ae60", "#e67e22", "#2980b9"];

  const doSearch = async (q: string) => {
    if (!q.trim()) return;
    setHasSearched(true);
    setSearching(true);
    try {
      const res = await fetch(`/api/search?q=${encodeURIComponent(q)}&limit=8`);
      if (res.ok) {
        const data = await res.json();
        setTopics(data.topics || []);
        setArticles(data.articles || []);
      } else {
        setTopics([]); setArticles([]);
      }
    } catch {
      setTopics([]); setArticles([]);
    } finally {
      setSearching(false);
    }
  };

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && query.trim()) doSearch(query);
  };

  const openTopic = (t: any) => {
    window.dispatchEvent(new CustomEvent("open-flyout", {
      detail: { id: t.id, slug: t.slug, viewCount: t.view_count, commentCount: t.comment_count }
    }));
  };

  useEffect(() => {
    const handleSync = (e: Event) => {
      const { topicId, viewCount, commentCount } = (e as CustomEvent).detail;
      setTopics(prev => prev.map(t => {
        if (String(t.id) === String(topicId)) {
          return {
            ...t,
            view_count: viewCount !== undefined ? Number(viewCount) : t.view_count,
            comment_count: commentCount !== undefined ? Number(commentCount) : t.comment_count
          };
        }
        return t;
      }));
    };
    window.addEventListener("topic-viewed", handleSync);
    return () => window.removeEventListener("topic-viewed", handleSync);
  }, []);

  return (
    <div className="flyout-inner-wrapper">
      <section className="topic-header-section-flyout">
        <div className="topic-header-container-flyout">
          <div className="topic-meta-flyout">
            <div className="topic-badge-flyout" style={{ background: "rgba(255,255,255,0.1)", color: "#fff" }}>
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
              </svg>
              Intelligence Search
            </div>
          </div>

          <div style={{ position: "relative", marginTop: "16px", marginBottom: "8px" }}>
            <svg style={{ position: "absolute", left: "16px", top: "50%", transform: "translateY(-50%)", width: "22px", height: "22px", color: "#888" }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              placeholder="Search processed topics, stories or keywords..."
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={handleKey}
              style={{
                width: "100%",
                background: "rgba(255,255,255,0.05)",
                border: "1px solid rgba(255,255,255,0.15)",
                color: "#fff",
                fontSize: "1.25rem",
                padding: "16px 20px 16px 52px",
                borderRadius: "8px",
                outline: "none",
                fontFamily: "var(--serif)"
              }}
              autoFocus
            />
          </div>

          {!hasSearched && (
            <div style={{ marginTop: "24px" }}>
              <div style={{ textTransform: "uppercase", fontSize: "0.75rem", fontWeight: 600, color: "#888", marginBottom: "12px", letterSpacing: "0.08em" }}>Trending Searches</div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                {["CBN Policy", "Fuel Subsidy", "Dangote Refinery", "Inflation Rate"].map(term => (
                  <button key={term} onClick={() => { setQuery(term); doSearch(term); }}
                    style={{ padding: "8px 16px", background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "20px", color: "#ccc", cursor: "pointer", fontSize: "0.85rem" }}>
                    {term}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </section>

      {hasSearched && (
        <main className="main-content-flyout" style={{ borderTop: "1px solid rgba(255,255,255,0.08)", display: "block", maxWidth: "900px", margin: "0 auto", padding: "48px 0" }}>

          {searching ? (
            <div style={{ textAlign: "center", padding: "60px", color: "#888" }}>
              <div style={{ width: "32px", height: "32px", borderRadius: "50%", border: "3px solid rgba(255,255,255,0.1)", borderTopColor: "var(--accent)", animation: "spin 0.8s linear infinite", margin: "0 auto 16px" }} />
              Scanning intelligence feed for "{query}"…
            </div>
          ) : (topics.length === 0 && articles.length === 0) ? (
            <section className="intelligence-section-flyout">
              <div className="section-label-flyout">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                No Results
              </div>
              <h2 className="section-title-flyout">No intelligence found for "{query}"</h2>
              <div className="intelligence-content-flyout">
                <p>Try a different keyword or browse trending topics from the main feed.</p>
              </div>
            </section>
          ) : (
            <>
              {/* ── TOPICS FIRST ─────────────────────────────────── */}
              {topics.length > 0 && (
                <section style={{ marginBottom: "48px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "24px" }}>
                    <svg width="18" height="18" fill="none" stroke="var(--accent)" strokeWidth="2" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                    </svg>
                    <span style={{ color: "var(--accent)", fontWeight: 700, fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "0.1em" }}>
                      {topics.length} Intelligence Topic{topics.length !== 1 ? "s" : ""}
                    </span>
                  </div>

                  <div style={{ display: "flex", flexDirection: "column", gap: "0" }}>
                    {topics.map((t: any, i: number) => (
                      <button
                        key={t.id ?? i}
                        onClick={() => openTopic(t)}
                        style={{ all: "unset", cursor: "pointer", display: "block", padding: "20px 0", borderBottom: "1px solid rgba(255,255,255,0.07)", textAlign: "left", transition: "background 0.15s" }}
                        onMouseEnter={e => (e.currentTarget.style.background = "rgba(255,255,255,0.03)")}
                        onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
                      >
                        {/* Category badge + timestamp */}
                        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
                          <span style={{ fontSize: "0.7rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", padding: "2px 10px", borderRadius: "20px", background: "rgba(var(--accent-rgb, 59,130,246),0.15)", color: "var(--accent)" }}>
                            {t.category}
                          </span>
                          <span style={{ fontSize: "0.75rem", color: "rgba(255,255,255,0.4)" }}>{t.updated_at_str}</span>
                        </div>

                        {/* Title */}
                        <div style={{ fontSize: "1.15rem", fontWeight: 700, color: "#fff", lineHeight: 1.35, marginBottom: "8px", fontFamily: "var(--serif)" }}>
                          {t.title}
                        </div>

                        {/* Brief */}
                        {t.brief && (
                          <div style={{ fontSize: "0.88rem", color: "rgba(255,255,255,0.55)", lineHeight: 1.75, marginBottom: "14px", letterSpacing: "0.01em" }}>
                            {t.brief}…
                          </div>
                        )}

                        {/* Engagement */}
                        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                          <span style={{ display: "flex", alignItems: "center", gap: "5px", fontSize: "0.78rem", color: "rgba(255,255,255,0.4)" }}>
                            <svg width="13" height="13" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
                            </svg>
                            {t.view_count.toLocaleString()} views
                          </span>
                          <span style={{ display: "flex", alignItems: "center", gap: "5px", fontSize: "0.78rem", color: "rgba(255,255,255,0.4)" }}>
                            <svg width="13" height="13" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                              <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
                            </svg>
                            {t.comment_count} comments
                          </span>
                          <span style={{ marginLeft: "auto", fontSize: "0.78rem", color: "var(--accent)", fontWeight: 600 }}>Read Full Brief →</span>
                        </div>
                      </button>
                    ))}
                  </div>
                </section>
              )}

              {/* ── DIVIDER ───────────────────────────────────────── */}
              {topics.length > 0 && articles.length > 0 && (
                <div style={{ display: "flex", alignItems: "center", gap: "16px", margin: "0 0 36px" }}>
                  <div style={{ flex: 1, height: "1px", background: "rgba(255,255,255,0.1)" }} />
                  <span style={{ fontSize: "0.72rem", fontWeight: 600, color: "rgba(255,255,255,0.3)", textTransform: "uppercase", letterSpacing: "0.12em", whiteSpace: "nowrap" }}>
                    Also found in source coverage
                  </span>
                  <div style={{ flex: 1, height: "1px", background: "rgba(255,255,255,0.1)" }} />
                </div>
              )}

              {/* ── SOURCE ARTICLES ───────────────────────────────── */}
              {articles.length > 0 && (
                <section>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
                    {articles.map((art: any, i: number) => {
                      const sourceName: string = art.source_name || art.source?.name || "Unknown Source";
                      const initials = sourceName.substring(0, 2).toUpperCase();
                      const bg = COLORS[i % COLORS.length];
                      return (
                        <a href={art.url || "#"} key={i} className="source-article-flyout" target="_blank" rel="noopener noreferrer" style={{ background: "rgba(255,255,255,0.03)" }}>
                          <div className="source-logo-flyout" style={{ background: bg, color: "#fff" }}>{initials}</div>
                          <div className="source-content-flyout">
                            <div className="source-name-flyout">{sourceName}</div>
                            <div className="source-headline-flyout">{art.title}</div>
                            <div className="source-snippet-flyout">{art.content ? art.content.substring(0, 100) + "…" : "No preview available."}</div>
                            <div className="source-time-flyout">{art.published_at ? formatDistanceToNow(new Date(art.published_at), { addSuffix: true }) : "Recently published"}</div>
                          </div>
                        </a>
                      );
                    })}
                  </div>
                </section>
              )}
            </>
          )}
        </main>
      )}
    </div>
  );
}
function SubscribeFlyoutContent() {
  return (
    <div className="flyout-inner-wrapper">
      <div className="bg-accent/10 border-b border-accent/20 py-3 text-center">
        <span className="text-accent text-sm font-bold tracking-tight uppercase">Coming Soon for Premium Users</span>
      </div>
      {/* Header section - mirrors topic-header-section-flyout */}
      <section className="topic-header-section-flyout">
        <div className="topic-header-container-flyout">
          <div className="topic-meta-flyout">
            <div className="topic-badge-flyout">
              <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
              </svg>
              Pricing Plans
            </div>
          </div>
          <h1 className="topic-title-flyout">Get Started for Free</h1>
          <p style={{ fontSize: "1.15rem", color: "#999", lineHeight: 1.6, maxWidth: "560px" }}>
            Join leading policymakers, executives, and analysts who rely on Gl Intel for synthesized clarity from daily noise.
          </p>
        </div>
      </section>

      {/* Single Coming Soon section instead of plan cards */}
      <div style={{ maxWidth: "600px", margin: "0 auto", padding: "48px 48px 80px", textAlign: "center" }}>
        <div className="intelligence-section-flyout" style={{ padding: "48px 32px", border: "1px solid rgba(255,255,255,0.1)", background: "rgba(255,255,255,0.02)" }}>
           <div style={{ display: "inline-flex", alignItems: "center", justifyContent: "center", width: "48px", height: "48px", borderRadius: "50%", background: "rgba(var(--accent-rgb, 59,130,246),0.15)", color: "var(--accent)", marginBottom: "24px" }}>
             <svg width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
           </div>
           <h2 style={{ fontSize: "1.8rem", fontWeight: 700, color: "#fff", marginBottom: "16px", fontFamily: "var(--serif)" }}>Premium Plans in Development</h2>
           <p style={{ fontSize: "1.05rem", color: "#999", lineHeight: 1.6, marginBottom: "32px" }}>
             We are currently refining our Pro and Team intelligence tiers. Join the free waitlist today and you'll be the first to know when advanced AI querying and custom source tracking become available.
           </p>
           <div style={{ display: "flex", gap: "16px", justifyContent: "center", marginTop: "24px" }}>
             <button 
               className="pricing-btn-flyout" 
               style={{ background: "transparent", color: "#fff", border: "1px solid rgba(255,255,255,0.2)", minWidth: "160px" }}
                onClick={() => {
                  window.dispatchEvent(new CustomEvent("open-flyout", { detail: { type: "login", infoType: "register" } }));
               }}
             >
               Sign Up
             </button>
             <button 
               className="pricing-btn-flyout" 
               style={{ background: "var(--accent)", color: "#fff", border: "1px solid var(--accent)", minWidth: "160px" }}
               onClick={() => {
                  const closeBtn = document.querySelector(".flyout-close") as HTMLButtonElement;
                  if (closeBtn) closeBtn.click();
               }}
             >
               Return to Dashboard
             </button>
           </div>
        </div>
        <p style={{ textAlign: "center", color: "#555", fontSize: "0.8rem", marginTop: "32px" }}>
          Basic free access is currently provided to all users.
        </p>
      </div>
    </div>
  );
}

function PricingFeature({ text, accent = false }: { text: string; accent?: boolean }) {
  return (
    <li style={{ display: "flex", alignItems: "flex-start", gap: "12px", padding: "10px 0", borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
      <span style={{
        width: "18px", height: "18px", borderRadius: "50%", display: "flex",
        alignItems: "center", justifyContent: "center", flexShrink: 0, marginTop: "1px",
        background: accent ? "rgba(231, 76, 60, 0.15)" : "rgba(255,255,255,0.07)",
        color: accent ? "#e74c3c" : "#888"
      }}>
        <svg width="10" height="10" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={3}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
      </span>
      <span style={{ fontSize: "0.9rem", color: "#ccc", lineHeight: 1.5 }}>{text}</span>
    </li>
  );
}

function LoginFlyoutContent({ initialIsRegistering = false }: { initialIsRegistering?: boolean }) {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [isRegistering, setIsRegistering] = useState(initialIsRegistering);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    setLoading(true);
    setError("");

    try {
      const payload = {
        email: email,
        full_name: fullName || undefined
      };

      const endpoint = isRegistering ? "/api/auth/magic-register" : "/api/auth/magic-login";

      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        const data = await res.json();
        const userRes = await fetch("/api/auth/me");
        if (userRes.ok) {
          const userData = await userRes.json();
          login(userData, data.access_token);
          const closeBtn = document.querySelector(".flyout-close") as HTMLButtonElement;
          if (closeBtn) closeBtn.click();
        }
      } else {
        if (res.status === 404 && !isRegistering) {
          setIsRegistering(true);
          setError("Account not found. Please provide your name to create one.");
        } else {
          try {
            const err = await res.json();
            setError(err.detail || "Authentication failed");
          } catch {
            setError("Authentication failed");
          }
        }
      }
    } catch (e) {
      setError("An error occurred. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    // This would typically involve a popup or redirect
    // For MVP, we show how we'd handle the callback
    alert("Google Login Integration: Redirecting to Google...");
    // window.location.href = "/api/auth/google/login";
  };

  return (
    <div className="flyout-inner-wrapper">
      {/* Header mirrors topic-header-section-flyout */}
      <section className="topic-header-section-flyout">
        <div className="topic-header-container-flyout">
          <div className="topic-meta-flyout">
            <div className="topic-badge-flyout">
              <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor">
                <path d="M20 12V22H4V12" /><path d="M22 7H2v5h20V7z" /><path d="M12 22V7" />
                <path d="M12 7H7.5a2.5 2.5 0 010-5C11 2 12 7 12 7z" />
                <path d="M12 7h4.5a2.5 2.5 0 000-5C13 2 12 7 12 7z" />
              </svg>
              Account Access
            </div>
          </div>
          <h1 className="topic-title-flyout">{isRegistering ? "Create an Account" : "Welcome Back"}</h1>
          <p style={{ fontSize: "1.1rem", color: "#999", lineHeight: 1.6 }}>
            {isRegistering ? "Already have an account?" : "Don't have an account yet?"}{" "}
            <a href="#" onClick={(e) => { e.preventDefault(); setIsRegistering(!isRegistering); }}
              style={{ color: "#fff", textDecoration: "underline", cursor: "pointer" }}>
              {isRegistering ? "Sign in" : "Subscribe for free"}
            </a>
          </p>
        </div>
      </section>

      {/* Form section */}
      <div style={{ maxWidth: "560px", margin: "48px auto", padding: "0 48px 80px" }}>
        <div className="intelligence-section-flyout" style={{ padding: "48px" }}>
          <div className="section-label-flyout" style={{ marginBottom: "32px" }}>
            <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
            {isRegistering ? "Create your account" : "Sign in to your account"}
          </div>

          <form style={{ display: "grid", gap: "20px" }} onSubmit={handleSubmit}>
            {error && <div style={{ color: "var(--accent)", fontSize: "0.9rem", textAlign: "center", background: "rgba(185,28,28,0.1)", padding: "10px", borderRadius: "4px" }}>{error}</div>}
            
            {/* Email field */}
            <div>
              <label className="login-field-label-flyout">Email Address</label>
              <div className="login-field-wrap-flyout">
                <svg className="login-field-icon-flyout" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                <input 
                  type="email" 
                  placeholder="you@company.com" 
                  className="login-input-flyout" 
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  required
                />
              </div>
            </div>

            {/* Full Name field */}
            {isRegistering && (
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
                  <label className="login-field-label-flyout" style={{ marginBottom: 0 }}>Full Name</label>
                  <span style={{ fontSize: "0.8rem", color: "#888" }}>Required</span>
                </div>
                <div className="login-field-wrap-flyout">
                  <svg className="login-field-icon-flyout" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                  <input 
                    type="text" 
                    placeholder="John Doe" 
                    className="login-input-flyout" 
                    value={fullName}
                    onChange={e => setFullName(e.target.value)}
                    required={isRegistering}
                  />
                </div>
              </div>
            )}

            <button 
              type="submit" 
              disabled={loading}
              className="btn-flyout btn-primary-flyout" 
              style={{ width: "100%", padding: "16px", fontSize: "1rem", marginTop: "8px", borderRadius: "6px" }}
            >
              {loading ? "Authenticating..." : (isRegistering ? "Create Account" : "Sign In")}
            </button>
          </form>

          {/* OR divider */}
          <div className="login-or-divider-flyout">
            <div className="login-or-line-flyout"></div>
            <span className="login-or-text-flyout">OR CONTINUE WITH</span>
            <div className="login-or-line-flyout"></div>
          </div>

          {/* SSO row */}
          <div className="login-sso-row-flyout">
            <button className="login-sso-btn-flyout" onClick={handleGoogleLogin}>
              <svg viewBox="0 0 24 24" width="20" height="20" fill="none">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.17v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                <path d="M5.84 14.1c-.22-.66-.35-1.36-.35-2.1s.13-1.44.35-2.1V7.06H2.17C1.43 8.55 1 10.22 1 12s.43 3.45 1.17 4.94l3.67-2.84z" fill="#FBBC05"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.17 7.06l3.67 2.84c.87-2.6 3.3-4.52 6.16-4.52z" fill="#EA4335"/>
              </svg>
              <span>Google</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Separate component for the actual content rendering
function FlyoutInnerContent({
  topicData,
  seedViewCount,
  seedCommentCount,
  viewedTopicsRef
}: {
  topicData: any;
  seedViewCount?: number;
  seedCommentCount?: number;
  viewedTopicsRef: React.RefObject<Set<string>>;
}) {
  const { user: currentUser } = useAuth();
  const [fetchedComments, setFetchedComments] = useState<any[]>([]);
  const [newComment, setNewComment] = useState("");

  // Seed from card's live state (already correct integer) or DB fallback, then +1 for this view
  const initialViews = Math.max(0, Number(seedViewCount ?? topicData.view_count ?? 0)) + 1;
  const initialComments = Math.max(0, Number(seedCommentCount ?? topicData.comment_count ?? 0));
  const [liveViewCount, setLiveViewCount] = useState<number>(initialViews);
  const [liveCommentCount, setLiveCommentCount] = useState<number>(initialComments);

  // Refs for unmount cleanup so it uses the LATEST numbers, not the mount-time closure numbers
  const liveViewCountRef = useRef(liveViewCount);
  const liveCommentCountRef = useRef(liveCommentCount);

  useEffect(() => {
    liveViewCountRef.current = liveViewCount;
    liveCommentCountRef.current = liveCommentCount;
  }, [liveViewCount, liveCommentCount]);

  // Poll state
  const [activePoll, setActivePoll] = useState<any>(undefined);
  const [userVotedOption, setUserVotedOption] = useState<number | null>(null);
  const [isVoting, setIsVoting] = useState(false);

  // All fetches use relative /api/ paths — proxied by Next.js
  useEffect(() => {
    if (!topicData?.id) return;

    // 1. Persist view immediately (but only once per session/mount to avoid double counting)
    if (topicData?.id && viewedTopicsRef.current && !viewedTopicsRef.current.has(String(topicData.id))) {
      viewedTopicsRef.current.add(String(topicData.id));
      fetch(`/api/topic/${topicData.id}/view`, { method: "POST" })
        .then(res => res.ok ? res.json() : null)
        .then(data => {
          if (data && data.view_count !== undefined) {
            setLiveViewCount(data.view_count);
            // Sync UI cards exactly to DB
            window.dispatchEvent(new CustomEvent("topic-viewed", {
              detail: { topicId: topicData.id, viewCount: data.view_count, commentCount: liveCommentCount }
            }));
          }
        })
        .catch(() => { /* best-effort */ });
    }

    // 2. Notify cards with optimistic +1 view immediately
    window.dispatchEvent(new CustomEvent("topic-viewed", {
      detail: { topicId: topicData.id, viewCount: initialViews, commentCount: initialComments }
    }));

    // 3. Fetch existing comments from DB
    const fetchComments = () => {
      fetch(`/api/interactions/comments/topic/${topicData.id}`)
        .then(r => { if (r.ok) return r.json(); throw new Error(); })
        .then(data => {
          const comments = Array.isArray(data) ? data : [];
          setFetchedComments(comments);
          // Sync comment count with real DB (overrides seed if DB has more)
          const realCount = comments.length;
          setLiveCommentCount(realCount);
          window.dispatchEvent(new CustomEvent("topic-viewed", {
            detail: { topicId: topicData.id, commentCount: realCount }
          }));
        })
        .catch(() => { /* list stays empty on error */ });
    };

    fetchComments();
    
    // Make fetchComments available to other functions
    (window as any)[`__fetchComments_${topicData.id}`] = fetchComments;

    // 4. Fetch Active Polls for this topic (if any)
    const fetchPolls = () => {
      fetch(`/api/interactions/polls/topic/${topicData.id}${currentUser ? `?user_id=${currentUser.id}` : ''}`)
        .then(r => r.ok ? r.json() : null)
        .then(data => {
           if (data && data.poll) {
             setActivePoll(data.poll);
             if (data.user_voted_option_id !== null && data.user_voted_option_id !== undefined) {
                 setUserVotedOption(data.user_voted_option_id);
             }
           } else {
             setActivePoll(null);
           }
        })
        .catch(() => { /* error */ });
    };
    fetchPolls();
    (window as any)[`__fetchPolls_${topicData.id}`] = fetchPolls;

    // 5. On unmount (flyout closed): refresh cards with latest views
    return () => {
      const id = topicData.id;
      window.dispatchEvent(new CustomEvent("topic-viewed", {
        detail: { topicId: id, viewCount: liveViewCountRef.current, commentCount: liveCommentCountRef.current }
      }));
      delete (window as any)[`__fetchComments_${id}`];
      delete (window as any)[`__fetchPolls_${id}`];
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [topicData?.id]);

  // Sync user vote state when user or poll changes
  useEffect(() => {
    // We handle this inside fetchPolls now via user_voted_option_id
  }, [activePoll, currentUser]);

  // No local handleJoin anymore, handled via Login flyout

  const handlePostComment = () => {
    if (!newComment.trim() || !topicData?.id || !currentUser) return;
    const text = newComment.trim();

    // 1. Show comment IMMEDIATELY in the list (optimistic)
    const optimisticComment = {
      id: `opt-${Date.now()}`,
      content: text,
      created_at: new Date().toISOString(),
      user: { full_name: currentUser.full_name, email: currentUser.email }
    };
    setFetchedComments(prev => [...prev, optimisticComment]);

    // 2. Increment count immediately
    const nextCount = liveCommentCount + 1;
    setLiveCommentCount(prev => prev + 1);
    window.dispatchEvent(new CustomEvent("topic-viewed", {
      detail: { topicId: topicData.id, commentCount: nextCount }
    }));

    // 3. Persist explicitly to DB right now
    fetch("/api/interactions/comments", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content: text, topic_id: topicData.id }),
    })
      .then(r => r.ok ? r.json() : null)
      .then(realComment => {
        if (realComment) {
          // Replace the optimistic comment with the real one from DB (seamless)
          setFetchedComments(prev => prev.map(c => 
            c.id === optimisticComment.id ? realComment : c
          ));
        } else {
          // If fail, we might want to remove optimistic or show retry, 
          // but for now we'll just leave it and let next refresh fix it.
        }
      })
      .catch(() => { /* error handling */ });

    setNewComment("");
  };

  const handleVote = async (optionId: number) => {
    if (!activePoll || userVotedOption !== null || isVoting) return;

    if (!currentUser) {
      window.dispatchEvent(new CustomEvent("open-flyout", { detail: { type: "login" } }));
      return;
    }

    setIsVoting(true);
    
    // Optimistic update
    setUserVotedOption(optionId);
    const updatedPoll = { ...activePoll };
    updatedPoll.total_votes = (updatedPoll.total_votes || 0) + 1;
    updatedPoll.options = updatedPoll.options.map((o: any) => 
        o.id === optionId ? { ...o, vote_count: o.vote_count + 1 } : o
    );
    setActivePoll(updatedPoll);

    try {
      const res = await fetch(`/api/interactions/polls/${activePoll.id}/vote`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ poll_option_id: optionId })
      });
      if (res.ok) {
         const fetchPolls = (window as any)[`__fetchPolls_${topicData.id}`];
         if (fetchPolls) fetchPolls();
      } else {
         setUserVotedOption(null); // revert simple
      }
    } catch {
       setUserVotedOption(null);
    } finally {
      setIsVoting(false);
    }
  };

  const title = topicData.title;
  const analysis = topicData.analysis || {};
  
  // Intelligence fields from Agent
  const executiveSummary = analysis.executive_summary || topicData.description || "No analysis available.";
  const whatToKnow = analysis.what_you_need_to_know || [];
  const keyTakeaways = analysis.key_takeaways || [];
  const drivers = analysis.drivers_of_story || [];
  const strategicImplications = analysis.strategic_implications || [];
  const regionalImpactItems = analysis.regional_impact || [];
  const confidenceScore = analysis.confidence_score || topicData.confidence_score || 0;

  const category = topicData.category || "General";
  const views = formatViews(liveViewCount);
  const comments = liveCommentCount;
  const updatedAt = topicData.updated_at ? formatDistanceToNow(new Date(topicData.updated_at), { addSuffix: true }) : "Recently";
  const sourcesCount = topicData.source_count || topicData.article_count || 0;

  return (
    <div className="flyout-inner-wrapper">
      {/* ─── TOPIC HEADER ─── */}
      <section className="topic-header-section-flyout">
        <div className="topic-header-container-flyout">
          <div className="topic-meta-flyout">
            <div className="topic-badge-flyout developing">
              <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor">
                <circle cx="12" cy="12" r="10" />
              </svg>
              Developing Story
            </div>
            <div className="update-badge-flyout">
              <div className="live-dot-flyout"></div>
              Updated {updatedAt}
            </div>
            <div className="topic-badge-flyout category-tag">{category}</div>
          </div>

          <h1 className="topic-title-flyout">
            {title}
          </h1>

          <div className="topic-stats-flyout">
            <div className="stat-flyout">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z"></path>
              </svg>
              {sourcesCount} sources synthesized
            </div>
            <div className="stat-flyout">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
              {Math.round(confidenceScore * 100)}% Confidence
            </div>
            <div className="stat-flyout">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
              </svg>
              {views} views
            </div>
          </div>
        </div>
      </section>

      {/* ─── MAIN CONTENT ─── */}
      <main className="main-content-flyout">
        <div className="content-area-flyout">
          
          {/* PILLAR 2: AI DEEP DIVE */}
          <section className="intelligence-section-flyout">
            <div className="section-label-flyout">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
              </svg>
              Glide Intelligence Overview
            </div>
            
            <div className="intelligence-content-flyout">
              <p className="executive-summary-text">
                {executiveSummary}
              </p>

              {whatToKnow.length > 0 && (
                <>
                  <h3>What You Need to Know</h3>
                  <ul className="knowledge-list-flyout">
                    {whatToKnow.map((item: string, i: number) => (
                      <li key={i}>{item}</li>
                    ))}
                  </ul>
                </>
              )}

              {keyTakeaways.length > 0 && (
                <div className="key-takeaway-flyout">
                  <div className="takeaway-label-flyout">Key Takeaways</div>
                  <ul className="takeaway-list-flyout">
                    {keyTakeaways.map((item: string, i: number) => (
                      <li key={i} className="takeaway-text-flyout">{item}</li>
                    ))}
                  </ul>
                </div>
              )}

              {drivers.length > 0 && (
                <>
                  <h3>What Is Driving The Story?</h3>
                  <ul className="drivers-list-flyout">
                    {drivers.map((item: string, i: number) => (
                      <li key={i}>{item}</li>
                    ))}
                  </ul>
                </>
              )}

              {strategicImplications.length > 0 && (
                <div className="strategic-section-flyout">
                  <h3>Strategic Implications</h3>
                  <ul className="implications-list-flyout">
                    {strategicImplications.map((item: string, i: number) => (
                      <li key={i}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* SENTIMENT & FRAMING FALLBACKS */}
              {(analysis.sentiment_summary || analysis.framing_overview) && (
                <div style={{ marginTop: '2rem' }}>
                  <div className="section-label-flyout">
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                    </svg>
                    Sentiment & Framing Analysis
                  </div>
                  <div className="intelligence-content-flyout">
                    {analysis.sentiment_summary && (
                      <div style={{ marginBottom: '1.5rem', marginTop: '1rem' }}>
                        <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem', color: 'var(--accent)' }}>Overall Sentiment</h3>
                        <p>{analysis.sentiment_summary}</p>
                      </div>
                    )}
                    {analysis.framing_overview && (
                      <div>
                        <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem', color: 'var(--accent)' }}>Framing & Narratives</h3>
                        <p>{analysis.framing_overview}</p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </section>

          {/* PILLAR 3: PERSPECTIVE MAP */}
          <section className="perspective-deep-flyout">
            <div className="section-label-flyout" style={{ color: "var(--accent)" }}>
                <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2-2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                How Different Sources Frame This
            </div>
            <h2 className="section-title-flyout">Source Framing Analysis</h2>
            
            {/* The Bar Chart requested */}
            {topicData.source_perspectives && topicData.source_perspectives.length > 0 && (
              <div className="perspective-grid" style={{ marginBottom: '40px' }}>
                {topicData.source_perspectives.map((p: any, i: number) => {
                  const score = parseFloat(String(p.sentiment_percentage).replace("%", "").replace("+", "")) || 0;
                  return (
                    <div key={i} className="perspective-item" style={{ borderBottom: "1px solid rgba(255,255,255,0.05)", paddingBottom: "12px" }}>
                      <div className="perspective-source" style={{ color: "#fff" }}>{p.source_name || p.frame_label}</div>
                      <div className="perspective-bar">
                        <div
                          className={`perspective-fill ${p.sentiment === 'positive' ? 'positive' : p.sentiment === 'negative' ? 'negative' : 'neutral'}`}
                          style={{ width: `${Math.abs(score)}%` }}
                        ></div>
                      </div>
                      <div className="perspective-score" style={{ color: "#888", minWidth: "45px", textAlign: "right" }}>
                        {score > 0 ? "+" : ""}{score}%
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            <div className="perspective-groups-flyout">
              {topicData.source_perspectives && topicData.source_perspectives.length > 0 ? topicData.source_perspectives.map((p: any, i: number) => {
                let s = p.sentiment === "positive" ? "positive" : p.sentiment === "negative" ? "negative" : "neutral";
                return (
                  <div key={i} className={`perspective-group-flyout ${s}`}>
                    <div className="group-header-flyout">
                      <div className="group-name-flyout">{p.frame_label}</div>
                      <div className={`sentiment-badge-flyout ${s}`}>{p.sentiment_percentage || p.sentiment}</div>
                    </div>
                    <div className="group-summary-flyout">
                      {p.key_narrative}
                    </div>
                    {p.source_name && (
                      <div className="group-quote-flyout">
                        "Perspective synthesis extracted from current intelligence monitoring."
                        <span className="quote-source-flyout">— {p.source_name}</span>
                      </div>
                    )}
                  </div>
                )
              }) : (
                <div className="perspective-group-flyout neutral">
                  <div className="group-header-flyout">
                    <div className="group-name-flyout">General Media Overview</div>
                    <div className="sentiment-badge-flyout neutral">Neutral</div>
                  </div>
                  <div className="group-summary-flyout">
                    Aggregated perspective of the developing story from synthesized sources.
                  </div>
                </div>
              )}
            </div>
          </section>

          {/* PILLAR 4: IMPACT ANALYSIS */}
          <section className="impact-deep-flyout">
            <div className="section-label-flyout">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
              Impact Analysis
            </div>
            <h2 className="section-title-flyout">What This Means for Nigeria & West Africa</h2>

            <div className="impact-categories-flyout">
              {regionalImpactItems.length > 0 ? (
                regionalImpactItems.map((item: string, idx: number) => (
                  <div key={idx} className="impact-category-flyout">
                    <div className="impact-cat-header-flyout">
                      <div className="impact-icon-flyout">🌍</div>
                      <div className="impact-cat-title-flyout">Regional Development</div>
                    </div>
                    <div className="impact-details-flyout">
                      <div className="impact-item-flyout">
                        <div className="impact-item-value-flyout">
                          {item}
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              ) : topicData.regional_impacts && topicData.regional_impacts.length > 0 ? (
                topicData.regional_impacts.map((imp: any, idx: number) => (
                  <div key={idx} className="impact-category-flyout">
                    <div className="impact-cat-header-flyout">
                      <div className="impact-icon-flyout">{imp.icon || "🌍"}</div>
                      <div className="impact-cat-title-flyout">{imp.impact_category || imp.title}</div>
                    </div>
                    <div className="impact-details-flyout">
                      <div className="impact-item-flyout">
                        <div className="impact-item-label-flyout">{imp.title}</div>
                        <div className="impact-item-value-flyout">
                          {imp.context || imp.value}
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="impact-category-flyout">
                  <div className="impact-cat-header-flyout">
                    <div className="impact-icon-flyout">📊</div>
                    <div className="impact-cat-title-flyout">General Impact</div>
                  </div>
                  <div className="impact-details-flyout">
                    <div className="impact-item-flyout">
                      <div className="impact-item-label-flyout">Overview</div>
                      <div className="impact-item-value-flyout">
                        Current coverage maintains standard tracking vectors until deep analysis algorithms finalize.
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </section>

          {/* PILLAR 1: SOURCE ARTICLES */}
          <section className="sources-section-flyout">
            <div className="section-label-flyout">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z"></path>
              </svg>
              Source Articles
            </div>
            <h2 className="section-title-flyout">What the Original Sources Say</h2>

            <div className="source-articles-flyout">
              {topicData.articles && topicData.articles.map((art: any, i: number) => {
                const colors = ["#e74c3c", "#3498db", "#2ecc71", "#f39c12", "#9b59b6"];
                const initials = art.source_name ? art.source_name.substring(0, 2).toUpperCase() : "GN";
                const bg = colors[i % colors.length];
                
                return (
                  <a href={art.url || "#"} key={i} className="source-article-flyout" target="_blank" rel="noopener noreferrer">
                    <div className="source-logo-flyout" style={{ background: bg, color: "#fff" }}>
                      {initials}
                    </div>
                    <div className="source-content-flyout">
                      <div className="source-name-flyout">{art.source_name || "Unknown Source"}</div>
                      <div className="source-headline-flyout">
                        {art.title}
                      </div>
                      <div className="source-snippet-flyout">
                        {art.snippet || art.content?.substring(0, 150) + "..."}
                      </div>
                      <div className="source-time-flyout">Published {art.published_at ? formatDistanceToNow(new Date(art.published_at), { addSuffix: true }) : "recently"}</div>
                    </div>
                  </a>
                )
              })}
            </div>
          </section>

          {/* PILLAR 5: COMMUNITY CONVERSATION */}
          <section className="community-section-flyout">
            <div className="section-label-flyout">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a1.994 1.994 0 01-1.414-.586m0 0L11 14h4a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2v4l.586-.586z"></path>
              </svg>
              Community Discussion
            </div>
            <h2 className="section-title-flyout">{comments} Comments</h2>

            <div className="comment-form-flyout">
              {currentUser ? (
                <>
                  <textarea 
                    placeholder="Share your perspective on this topic..."
                    value={newComment}
                    onChange={e => setNewComment(e.target.value)}
                  ></textarea>
                  <div className="comment-actions-flyout">
                    <div className="char-count-flyout" style={{ color: "rgba(255,255,255,0.4)", fontSize: "0.8rem" }}>
                      Commenting as <strong>{currentUser.full_name || currentUser.username}</strong>
                    </div>
                    <button className="btn-flyout btn-primary-flyout" onClick={handlePostComment}>Post Comment</button>
                  </div>
                </>
              ) : (
                <div style={{ padding: "32px", background: "rgba(255,255,255,0.03)", borderRadius: "8px", border: "1px dotted rgba(255,255,255,0.2)", textAlign: "center" }}>
                  <h3 style={{ margin: "0 0 12px 0", fontSize: "1.1rem", fontFamily: "var(--serif)" }}>Sign in to share your perspective</h3>
                  <p style={{ color: "#888", fontSize: "0.9rem", marginBottom: "20px" }}>Join the conversation with other intelligence readers.</p>
                  <button 
                    onClick={() => window.dispatchEvent(new CustomEvent("open-flyout", { detail: { type: "login" } }))}
                    className="btn-flyout btn-primary-flyout"
                  >
                    Sign In to Comment
                  </button>
                </div>
              )}
            </div>

            <div className="comments-list-flyout">
               {fetchedComments.length === 0 ? (
                 <div style={{ textAlign: "center", padding: "32px 0", color: "rgba(255,255,255,0.3)", fontSize: "0.9rem" }}>
                   Be the first to share your perspective on this topic.
                 </div>
               ) : (
                 fetchedComments.map((c, i) => {
                   const authorName = c.user?.username ? `@${c.user.username}` : (c.user?.email ? `@${c.user.email.split('@')[0].replace(/[^a-zA-Z0-9]/g, '').toLowerCase()}` : "@member");
                   const initials = authorName.startsWith("@") ? authorName.substring(1, 3).toUpperCase() : authorName.substring(0, 2).toUpperCase();
                   return (
                   <div key={c.id ?? i} className="comment-flyout">
                     <div className="comment-header-flyout">
                       <div className="comment-avatar-flyout" style={{ background: '#34495e' }}>{initials}</div>
                       <div className="comment-meta-flyout">
                         <div>
                           <span className="comment-author-flyout">{authorName}</span>
                           <span className="comment-role-flyout">Reader</span>
                         </div>
                         <div className="comment-time-flyout">{c.created_at ? formatDistanceToNow(parseISO(c.created_at), { addSuffix: true }) : "just now"}</div>
                       </div>
                     </div>
                     <div className="comment-text-flyout">
                       {c.content}
                     </div>
                   </div>
                   );
                 })
               )}
            </div>
          </section>
        </div>

        {/* SIDEBAR */}
        <aside className="sidebar-flyout">
          {/* Poll */}
          <div className="sidebar-card-flyout poll-card-flyout">
            <QuickPoll 
              poll={activePoll}
              userVotedOptionId={userVotedOption}
              onVoteSuccess={() => {
                const fetchPolls = (window as any)[`__fetchPolls_${topicData.id}`];
                if (fetchPolls) fetchPolls();
              }} 
            />
          </div>

          {/* AI Insights */}
          <div className="sidebar-card-flyout insights-card-flyout">
            <div className="sidebar-title-flyout">
              <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
              </svg>
              Live Insights
            </div>

            <div className="insight-item-flyout">
              <div className="insight-label-flyout">Sentiment Tracker</div>
              <div className="insight-value-flyout">
                {analysis.sentiment_label || (topicData.perspectives?.[0]?.sentiment ? (topicData.perspectives[0].sentiment.charAt(0).toUpperCase() + topicData.perspectives[0].sentiment.slice(1)) : "Stable")}
              </div>
              <div className="insight-text-flyout">{analysis.sentiment_summary || "Analysis vector normalized"}</div>
            </div>

            <div className="insight-item-flyout">
              <div className="insight-label-flyout">Expert Consensus</div>
              <div className="insight-value-flyout">{analysis.consensus_label || "Synthesizing..."}</div>
              <div className="insight-text-flyout">{analysis.framing_overview || "Awaiting further market data"}</div>
            </div>
          </div>
        </aside>
      </main>
    </div>
  );
}

function InfoFlyoutContent({ type }: { type: string }) {
  const contentMap: Record<string, { title: string; badge: string; content: React.ReactNode }> = {
    about: {
      title: "About Gl Intel",
      badge: "Company",
      content: (
        <div style={{ display: "grid", gap: "24px" }}>
          <p>Gl Intel is a next-generation news intelligence platform designed for decision-makers, analysts, and informed citizens in Nigeria and West Africa.</p>
          <p>We believe the problem today isn&apos;t a lack of information, but an abundance of noise. Our mission is to transform fragmented news reports into synthesized, actionable intelligence using advanced AI and rigorous editorial oversight.</p>
          <h3 style={{ borderBottom: "1px solid rgba(255,255,255,0.1)", paddingBottom: "10px", marginTop: "10px" }}>Our Approach</h3>
          <p>Unlike traditional news aggregators, Gl Intel uses proprietary AI pipelines to extract key facts, analyze sentiment variations across multiple sources, and map regional impacts for every major story.</p>
        </div>
      ),
    },
    "how-it-works": {
      title: "How It Works",
      badge: "Technology",
      content: (
        <div style={{ display: "grid", gap: "24px" }}>
          <p>Our intelligence engine operates in four distinct phases to ensure clarity and accuracy:</p>
          <ul style={{ listStyle: "none", padding: 0, display: "grid", gap: "24px" }}>
            <li>
              <strong style={{ color: "var(--accent)", display: "block", marginBottom: "4px" }}>1. Aggregation</strong>
              We monitor hundreds of verified local and international sources in real-time.
            </li>
            <li>
              <strong style={{ color: "var(--accent)", display: "block", marginBottom: "4px" }}>2. Extraction</strong>
              AI identifies entities, claims, and data points, stripping away sensationalism.
            </li>
            <li>
              <strong style={{ color: "var(--accent)", display: "block", marginBottom: "4px" }}>3. Synthesis</strong>
              Disparate reports are merged into a single &quot;Intelligence Brief&quot; that highlights consensus and conflict.
            </li>
            <li>
              <strong style={{ color: "var(--accent)", display: "block", marginBottom: "4px" }}>4. Verification</strong>
              Our system checks facts across sources and flags developing stories for human editorial review.
            </li>
          </ul>
        </div>
      ),
    },
    transparency: {
      title: "Transparency & AI Ethics",
      badge: "Policy",
      content: (
        <div style={{ display: "grid", gap: "24px" }}>
          <p>Transparency is the foundation of trust in intelligence. We are committed to being open about how our AI systems influence the content you read.</p>
          <h3 style={{ borderBottom: "1px solid rgba(255,255,255,0.1)", paddingBottom: "10px", marginTop: "10px" }}>AI Assistance Disclosure</h3>
          <p>Every &quot;Summary&quot; and &quot;Impact Analysis&quot; on this platform is generated by AI models. These models are strictly constrained by the source material provided in the &quot;Source Perspectives&quot; section.</p>
          <h3 style={{ borderBottom: "1px solid rgba(255,255,255,0.1)", paddingBottom: "10px", marginTop: "10px" }}>Bias Mitigation</h3>
          <p>We deliberately include sources with varying political and economic leanings to ensure the AI-synthesized sentiment breakdown reflects the true breadth of public discourse.</p>
        </div>
      ),
    },
    contact: {
      title: "Contact Us",
      badge: "Support",
      content: (
        <div style={{ display: "grid", gap: "24px" }}>
          <p>Questions, feedback, or enterprise inquiries? We&apos;d love to hear from you.</p>
          <div style={{ background: "rgba(255,255,255,0.05)", padding: "32px", borderRadius: "12px", border: "1px solid rgba(255,255,255,0.1)" }}>
            <div style={{ marginBottom: "24px" }}>
              <strong style={{ display: "block", fontSize: "0.7rem", color: "#888", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: "4px" }}>General Inquiries</strong>
              <span style={{ fontSize: "1.2rem", fontWeight: 600 }}>intel@glideintelligence.com</span>
            </div>
            <div>
              <strong style={{ display: "block", fontSize: "0.7rem", color: "#888", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: "4px" }}>Location</strong>
              <span style={{ fontSize: "1.1rem" }}>Victoria Island, Lagos, Nigeria</span>
            </div>
          </div>
        </div>
      ),
    },
    newsletter: {
      title: "Intelligence Newsletter",
      badge: "Updates",
      content: (
        <div style={{ display: "grid", gap: "24px" }}>
          <p>Stay ahead of the curve with our daily intelligence briefings, delivered straight to your inbox every morning at 6 AM WAT.</p>
          <ul style={{ paddingLeft: "20px", color: "#ccc", display: "grid", gap: "12px" }}>
            <li>Top 5 intelligence briefs of the day</li>
            <li>Sentiment shift alerts</li>
            <li>Curated regional impact reports</li>
          </ul>
          <div style={{ background: "rgba(255,255,255,0.05)", padding: "40px", borderRadius: "16px", textAlign: "center", border: "1px solid rgba(255,255,255,0.1)" }}>
            <h4 style={{ marginBottom: "16px", fontSize: "1.2rem" }}>Subscribe to the Pulse</h4>
            <input 
              type="email" 
              placeholder="Enter your email" 
              style={{ width: "100%", padding: "14px", borderRadius: "8px", background: "rgba(0,0,0,0.3)", border: "1px solid rgba(255,255,255,0.2)", color: "#fff", marginBottom: "16px", outline: "none" }} 
            />
            <button className="btn-flyout btn-primary-flyout" style={{ width: "100%", padding: "14px" }}>Join the Waitlist</button>
          </div>
        </div>
      ),
    },
    privacy: {
      title: "Privacy Policy",
      badge: "Legal",
      content: (
        <div style={{ display: "grid", gap: "24px" }}>
          <p>Your privacy is paramount. This policy outlines how we handle your data.</p>
          <h3 style={{ borderBottom: "1px solid rgba(255,255,255,0.1)", paddingBottom: "10px", marginTop: "10px" }}>Data Collection</h3>
          <p>We collect minimal data: your email for account access, and anonymized interaction metrics to improve AI relevance.</p>
          <h3 style={{ borderBottom: "1px solid rgba(255,255,255,0.1)", paddingBottom: "10px", marginTop: "10px" }}>Data Usage</h3>
          <p>We do not sell your personal data. Your information is used exclusively to provide personalized intelligence and maintain security.</p>
        </div>
      ),
    },
    terms: {
      title: "Terms of Service",
      badge: "Legal",
      content: (
        <div style={{ display: "grid", gap: "24px" }}>
          <p>By using Gl Intel, you agree to the following conditions:</p>
          <h3 style={{ borderBottom: "1px solid rgba(255,255,255,0.1)", paddingBottom: "10px", marginTop: "10px" }}>Acceptable Use</h3>
          <p>Automated scraping of our synthesized intelligence is strictly prohibited without a license. Content is for personal or internal professional use.</p>
          <h3 style={{ borderBottom: "1px solid rgba(255,255,255,0.1)", paddingBottom: "10px", marginTop: "10px" }}>Intellectual Property</h3>
          <p>The synthesis and regional impact mapping are the intellectual property of Gl Intel. Original news headlines belong to their respective publishers.</p>
        </div>
      ),
    },
    editorial: {
      title: "Editorial Standards",
      badge: "Standards",
      content: (
        <div style={{ display: "grid", gap: "24px" }}>
          <p>Our editorial process is defined by two principles: **Objectivity** and **Synthesized Clarity**.</p>
          <h3 style={{ borderBottom: "1px solid rgba(255,255,255,0.1)", paddingBottom: "10px", marginTop: "10px" }}>Neutrality</h3>
          <p>We do not take editorial stances. We report on the landscape of public discourse by highlighting conflicting viewpoints across sources.</p>
          <h3 style={{ borderBottom: "1px solid rgba(255,255,255,0.1)", paddingBottom: "10px", marginTop: "10px" }}>Source Diversity</h3>
          <p>Every Intelligence Brief is required to be synthesized from multiple verified independent sources to minimize single-outlet bias.</p>
        </div>
      ),
    },
    sources: {
      title: "Source Policy",
      badge: "Whitelisting",
      content: (
        <div style={{ display: "grid", gap: "24px" }}>
          <p>We only ingest data from verified, reputable news organizations and official regulatory portals.</p>
          <h3 style={{ borderBottom: "1px solid rgba(255,255,255,0.1)", paddingBottom: "10px", marginTop: "10px" }}>Verification Tiers</h3>
          <ul style={{ paddingLeft: "20px", color: "#ccc", display: "grid", gap: "8px" }}>
            <li><strong>Tier 1:</strong> National dailies and international wire services.</li>
            <li><strong>Tier 2:</strong> Specialized industry journals and financial reports.</li>
            <li><strong>Tier 3:</strong> Official government press releases and gazettes.</li>
          </ul>
          <p>Social media content and unverified blogs are excluded from our intelligence engine to ensure data integrity.</p>
        </div>
      ),
    },
  };

  const info = contentMap[type] || contentMap["about"];

  return (
    <div className="flyout-inner-wrapper">
      <section className="topic-header-section-flyout">
        <div className="topic-header-container-flyout" style={{ borderBottom: "none" }}>
          <div className="topic-meta-flyout">
            <div className="topic-badge-flyout" style={{ background: "rgba(255,255,255,0.1)", color: "#fff" }}>
              <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="10"/></svg>
              {info.badge}
            </div>
          </div>
          <h1 className="topic-title-flyout" style={{ marginBottom: "32px", fontSize: "3rem", borderBottom: "1px solid rgba(255,255,255,0.1)", paddingBottom: "24px" }}>{info.title}</h1>
          <div className="intelligence-content-flyout" style={{ fontSize: "1.05rem", color: "#aaa", lineHeight: 1.8, maxWidth: "780px" }}>
            {info.content}
          </div>
        </div>
      </section>
      
      <div style={{ height: "120px" }} />
    </div>
  );
}

function SponsorFlyoutContent({ sponsorAd }: { sponsorAd: any }) {
  if (!sponsorAd || !sponsorAd.sponsor) return null;

  const sp = sponsorAd.sponsor;

  return (
    <div className="flyout-inner-wrapper">
      <section className="topic-header-section-flyout" style={{ borderBottom: "1px solid rgba(255,255,255,0.1)", paddingBottom: "40px", marginBottom: "40px" }}>
        <div className="topic-header-container-flyout" style={{ borderBottom: "none" }}>
          <div className="topic-meta-flyout">
            <div className="topic-badge-flyout" style={{ background: "rgba(59, 130, 246, 0.2)", color: "#60a5fa", border: "1px solid rgba(59, 130, 246, 0.4)" }}>
              <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="10"/></svg>
              {sp.tagline || "Sponsored Content"}
            </div>
          </div>
          <h1 className="topic-title-flyout" style={{ marginBottom: "16px", fontSize: "2.5rem" }}>
            {sponsorAd.title}
          </h1>
          {sp.summary && (
            <p style={{ fontSize: "1.1rem", color: "#aaa", lineHeight: 1.6, maxWidth: "780px", marginBottom: "24px" }}>
              {sp.summary}
            </p>
          )}

          {sp.website_link && (
            <div style={{ marginTop: "24px" }}>
              <a 
                href={`/api/ads/click/${sponsorAd.id}`}
                target="_blank" 
                rel="noopener noreferrer"
                className="btn-flyout btn-primary-flyout"
                style={{ display: "inline-flex", alignItems: "center", gap: "8px", textDecoration: "none" }}
              >
                {sp.cta_text || "Visit Sponsor"}
                <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </a>
            </div>
          )}
        </div>
      </section>
      
      {sp.image_url && (
         <div style={{ maxWidth: "780px", margin: "0 auto 40px", borderRadius: "12px", overflow: "hidden", border: "1px solid rgba(255,255,255,0.1)" }}>
           {/* eslint-disable-next-line @next/next/no-img-element */}
           <img src={sp.image_url} alt={sponsorAd.title} style={{ width: "100%", height: "auto", display: "block" }} />
         </div>
      )}

      <div className="intelligence-content-flyout" style={{ maxWidth: "780px", margin: "0 auto 120px" }}>
        {/* We use dangerouslySetInnerHTML to render the full markdown/HTML content from the sponsor safely parsed by browser */}
        <div dangerouslySetInnerHTML={{ __html: sp.full_content?.replace(/\n/g, "<br/>") || "No detailed content provided." }} style={{ lineHeight: 1.8, fontSize: "1.05rem", color: "#ccc" }} />
      </div>
    </div>
  );
}

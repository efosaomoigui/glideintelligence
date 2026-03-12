"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import VerticalHeader from "@/components/VerticalHeader";
import TopicCard from "@/components/TopicCard";
import VerticalInsights from "@/components/VerticalInsights";
import KeyTopics from "@/components/KeyTopics";
import NewsletterCard from "@/components/NewsletterCard";
import SiteFooter from "@/components/SiteFooter";
import MobileHeader from "@/components/MobileHeader";

// All API calls use relative /api/ — proxied by Next.js to localhost:8000

/* ──────────────────────────────────────────────────────
   ADAPTER: Map API topic -> TopicCard prop shape
────────────────────────────────────────────────────── */
function adaptTopic(t: any) {
  const perspectives = (t.source_perspectives || t._perspectives_data || []).map((p: any) => ({
    source: p.source_name || p.frame_label || "Source",
    sentiment: (p.sentiment || "neutral") as "positive" | "negative" | "neutral",
    score: typeof p.sentiment_percentage === "string"
      ? parseInt(p.sentiment_percentage.replace("%", "").replace("+", "")) || 0
      : (p.sentiment_score || 0) * 100,
  }));

  const impacts = (t.regional_impacts || t._impacts_data || []).map((imp: any) => ({
    icon: imp.icon || "📊",
    title: imp.title || imp.impact_category || "Impact",
    value: imp.value || imp.context || "",
  }));

  const sourceAvatars = (t.sources || []).map((s: any) => ({
    initials: (s.name || "???").substring(0, 2).toUpperCase(),
    color: s.bg || "#3498db",
  }));


  return {
    id: String(t.id),
    title: t.title,
    category: t.category || t.badge || "General",
    isDeveloping: t.is_trending || t.status === "developing",
    updatedAt: t.updated_at_str || t.updatedAt || "Recently",
    brief: t.ai_brief || t.description || "",
    perspectives: perspectives.length ? perspectives : [
      { source: "Local Media", sentiment: "neutral" as const, score: 50 },
      { source: "International", sentiment: "neutral" as const, score: 40 },
    ],
    impacts: impacts.length ? impacts : [
      { icon: "📊", title: "Analysis", value: "Intelligence synthesis in progress" },
    ],
    sourceAvatars: sourceAvatars.length ? sourceAvatars : [
      { initials: "GL", color: "#e74c3c" },
    ],
    sourceCount: t.source_count || 1,
    commentCount: t.comment_count ?? 0,
    viewCount: t.view_count ?? 0,  // raw integer — TopicCard.fmt() formats for display
  };
}


/* ──────────────────────────────────────────────────────
   VERTICAL CONFIGURATIONS (Metadata Only)
────────────────────────────────────────────────────── */

interface VerticalConfig {
  name: string;
  icon: string;
  description: string;
  color: string;
  stats: { value: string; label: string }[];
  tickerLabel: string;
  insights: { label: string; value: string; text: string }[];
  trending: { title: string; views: string; timeAgo: string }[];
  newsletterTitle: string;
  newsletterDesc: string;
}

const VERTICAL_CONFIGS: Record<string, VerticalConfig> = {
  economy: {
    name: "Economy",
    icon: "💰",
    color: "#2980b9",
    description:
      "Glide-synthesized analysis of Nigeria's economic landscape—from currency movements and monetary policy to fiscal reforms and market dynamics.",
    stats: [
      { value: "0", label: "Active Topics" },
      { value: "0", label: "Sources Tracked" },
      { value: "0", label: "Community Members" },
      { value: "Real-time", label: "Updates" },
    ],
    tickerLabel: "ECONOMY",
    insights: [],
    trending: [],
    newsletterTitle: "Daily Economy Brief",
    newsletterDesc: "Get AI-synthesized economic intelligence in your inbox every morning at 6 AM WAT.",
  },
  politics: {
    name: "Politics",
    icon: "🏛️",
    color: "#8e44ad",
    description:
      "In-depth intelligence on Nigeria's political landscape—tracking legislative battles, executive actions, and party dynamics.",
    stats: [
      { value: "0", label: "Active Topics" },
      { value: "0", label: "Sources Tracked" },
      { value: "0", label: "Community Members" },
      { value: "Real-time", label: "Updates" },
    ],
    tickerLabel: "POLITICS",
    insights: [],
    trending: [],
    newsletterTitle: "Daily Politics Brief",
    newsletterDesc: "Stay ahead of Nigeria's political developments with our Glide-curated morning brief.",
  },
  business: {
    name: "Business",
    icon: "🏢",
    color: "#16a085",
    description:
      "Enterprise intelligence covering Nigerian and West African business — startup ecosystems, corporate strategy, and trade flows.",
    stats: [
      { value: "0", label: "Active Topics" },
      { value: "0", label: "Sources Tracked" },
      { value: "0", label: "Community Members" },
      { value: "Real-time", label: "Updates" },
    ],
    tickerLabel: "BUSINESS",
    insights: [],
    trending: [],
    newsletterTitle: "Daily Business Brief",
    newsletterDesc: "Business intelligence for West Africa's decision-makers — delivered at 6 AM WAT.",
  },
  security: {
    name: "Security",
    icon: "🛡️",
    color: "#c0392b",
    description:
      "Critical intelligence on security threats, military operations, and public safety across Nigeria and the West African region.",
    stats: [
      { value: "0", label: "Active Topics" },
      { value: "0", label: "Sources Tracked" },
      { value: "0", label: "Community Members" },
      { value: "Real-time", label: "Updates" },
    ],
    tickerLabel: "SECURITY",
    insights: [],
    trending: [],
    newsletterTitle: "Security Intelligence Brief",
    newsletterDesc: "Critical security updates synthesized daily for informed situational awareness.",
  },
  technology: {
    name: "Technology",
    icon: "💻",
    color: "#27ae60",
    description:
      "Intelligence on Nigeria's growing tech ecosystem — fintech, AI policy, telecom regulation, and the digital economy.",
    stats: [
      { value: "0", label: "Active Topics" },
      { value: "0", label: "Sources Tracked" },
      { value: "0", label: "Community Members" },
      { value: "Real-time", label: "Updates" },
    ],
    tickerLabel: "TECHNOLOGY",
    insights: [],
    trending: [],
    newsletterTitle: "Tech Intelligence Brief",
    newsletterDesc: "Daily digest of Nigeria's technology sector — policy, investment, and innovation.",
  },
  regional: {
    name: "Regional",
    icon: "🌍",
    color: "#d97706",
    description:
      "West African regional intelligence — ECOWAS dynamics, cross-border trade, and regional security cooperation.",
    stats: [
      { value: "0", label: "Active Topics" },
      { value: "0", label: "Sources Tracked" },
      { value: "0", label: "Community Members" },
      { value: "Real-time", label: "Updates" },
    ],
    tickerLabel: "REGIONAL",
    insights: [],
    trending: [],
    newsletterTitle: "Regional Intelligence Brief",
    newsletterDesc: "West Africa regional analysis delivered every morning — stay regionally informed.",
  },
  "global-impact": {
    name: "Global Impact",
    icon: "🌐",
    color: "#2c3e50",
    description:
      "How global macro trends — US policy, China-Africa dynamics, and commodity markets — affect Nigeria and West Africa.",
    stats: [
      { value: "0", label: "Active Topics" },
      { value: "0", label: "Sources Tracked" },
      { value: "0", label: "Community Members" },
      { value: "Real-time", label: "Updates" },
    ],
    tickerLabel: "GLOBAL",
    insights: [],
    trending: [],
    newsletterTitle: "Global Impact Brief",
    newsletterDesc: "How the world affects your economy — synthesised daily for decision-makers.",
  },
  "sport": {
    name: "Sport",
    icon: "⚽",
    color: "#e67e22",
    description:
      "Glide-synthesized analysis of Nigerian and international sports — tracking football, local leagues, and athlete performances.",
    stats: [
      { value: "0", label: "Active Topics" },
      { value: "0", label: "Sources Tracked" },
      { value: "0", label: "Community Members" },
      { value: "Real-time", label: "Updates" },
    ],
    tickerLabel: "SPORT",
    insights: [],
    trending: [],
    newsletterTitle: "Daily Sport Brief",
    newsletterDesc: "The intelligence behind the game — delivered every morning at 6 AM WAT.",
  },
};

/* ──────────────────────────────────────────────────────
   NAV LINKS
────────────────────────────────────────────────────── */

const NAV_LINKS = [
  { label: "All Stories", href: "/" },
  { label: "Economy", href: "/economy" },
  { label: "Politics", href: "/politics" },
  { label: "Business", href: "/business" },
  { label: "Security", href: "/security" },
  { label: "Technology", href: "/technology" },
  { label: "Sport", href: "/sport" },
  { label: "Regional", href: "/regional" },
  { label: "Global Impact", href: "/global-impact" },
];

/* ──────────────────────────────────────────────────────
   PAGE COMPONENT
────────────────────────────────────────────────────── */

export default function CategoryPage() {
  const params = useParams();
  const categorySlug = (params.category as string) || "economy";
  const config = VERTICAL_CONFIGS[categorySlug] || VERTICAL_CONFIGS["economy"];

  const [apiTopics, setApiTopics] = useState<any[]>([]);
  const [apiPulse, setApiPulse] = useState<any>(null);
  const [apiStats, setApiStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  
  // Pagination State
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);

  useEffect(() => {
    setLoading(true);
    fetch(`/api/vertical/${encodeURIComponent(categorySlug)}`)
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data.topics)) {
          setApiTopics(data.topics);
        }
        if (data.pulse) setApiPulse(data.pulse);
        if (data.stats) setApiStats(data.stats);
      })
      .catch((err) => {
        console.error("Failed to fetch vertical data:", err);
      })
      .finally(() => setLoading(false));
  }, [categorySlug]);

  const loadMore = async () => {
    if (!hasMore || loadingMore) return;
    setLoadingMore(true);
    const nextPage = page + 1;
    try {
      const res = await fetch(`/api/topics/trending?category=${encodeURIComponent(categorySlug)}&page=${nextPage}`);
      if (!res.ok) throw new Error("Failed to load more topics");
      const data = await res.json();
      
      if (data.items && data.items.length > 0) {
        // Prevent duplicates
        setApiTopics(prev => {
          const existingIds = new Set(prev.map(t => t.id));
          const newItems = data.items.filter((t: any) => !existingIds.has(t.id));
          return [...prev, ...newItems];
        });
        setPage(nextPage);
        setHasMore(data.has_more ?? false);
      } else {
        setHasMore(false);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingMore(false);
    }
  };

  const formatNumber = (num: number | string) => {
    const n = typeof num === 'string' ? parseInt(num.replace(/,/g, ''), 10) : num;
    if (isNaN(n)) return String(num);
    if (n >= 1000000) return (n / 1000000).toFixed(1).replace(/\.0$/, '') + 'M';
    if (n >= 1000) return (n / 1000).toFixed(1).replace(/\.0$/, '') + 'K';
    return String(n);
  };

  const effectiveConfig = {
    ...config,
    stats: apiStats ? [
      { value: formatNumber(apiStats.active_topics ?? 0), label: "Active Topics" },
      { value: formatNumber(apiStats.total_sources ?? 0), label: "Sources Tracked" },
      { value: formatNumber(apiStats.engagement?.comments ?? (apiStats.active_topics != null ? apiStats.active_topics * 105 : 0)), label: "Community Members" },
      { value: apiTopics.length > 0 ? apiTopics[0].updated_at_str : (apiStats.update_freq || "Real-time"), label: "Updates" }
    ] : config.stats
  };

  // Use live topics if fetched
  const displayTopics = apiTopics.map(adaptTopic);

  // Derive sidebar insights from pulse
  const sidebarInsights = apiPulse?.sentiment
    ? [
        {
          label: "Overall Sentiment",
          value: apiPulse.sentiment?.label || "Neutral",
          text: apiPulse.sentiment?.text || "",
        },
        {
          label: "Trending Context",
          value: apiPulse.context?.name || "Aggregating data...",
          text: apiPulse.context?.description || "Monitoring latest developments.",
        },
        {
          label: "Regional Focus",
          value: apiPulse.regional?.name || "ECOWAS",
          text: apiPulse.regional?.description || "Cross-border impact analysis in progress.",
        },
      ]
    : [
        { label: "Intelligence Pulse", value: "Pending", text: "Collecting cross-source data points..." }
      ];

  // Derive trending from API topics
  const sidebarTrending = apiTopics.length > 0
    ? apiTopics.slice(0, 3).map((t: any) => ({
        id: t.id,
        slug: t.slug || t.title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, ""),
        title: t.title,
        views: t.engagement?.views || `${t.view_count || 0} views`,
        timeAgo: t.updated_at_str || "recently",
      }))
    : [];

  const tickerItems = sidebarTrending.length > 0
    ? sidebarTrending.map((t: any) => ({ id: t.id, slug: t.slug, title: t.title }))
    : [
        { id: "static-1", title: "Synthesizing latest intelligence..." },
        { id: "static-2", title: "Awaiting data pipeline ingestion..." }
      ];

  const handleTickerClick = (item: { id: string | number; slug?: string }) => {
    if (item.id.toString().startsWith("static")) return;
    window.dispatchEvent(
      new CustomEvent("open-flyout", {
        detail: { type: "topic", id: String(item.id), slug: item.slug },
      })
    );
  };

  return (
    <>
      {/* Mobile Header (hidden on desktop) */}
      <MobileHeader activeCategory={effectiveConfig.name} />

      {/* TICKER */}
      <div className="ticker">
        <div className="ticker-label">{effectiveConfig.tickerLabel}</div>
        <div className="ticker-track">
          {[...tickerItems, ...tickerItems].map(
            (item, idx) => (
              <span 
                key={`${item.id}-${idx}`} 
                onClick={() => handleTickerClick(item)}
                style={{ cursor: item.id.toString().startsWith("static") ? "default" : "pointer" }}
              >
                {item.title}
              </span>
            )
          )}
        </div>
      </div>

      {/* STICKY HEADER */}
      <header className="site-header">
        <div className="header-top">
          <div>
            <Link href="/" className="logo" style={{ textDecoration: 'none', color: 'inherit' }}>
              Glide<span className="accent">Intelligence</span>
            </Link>
            <div className="tagline">Making Sense of the News</div>
          </div>
          <button className="search-bar" onClick={() => window.dispatchEvent(new CustomEvent("open-flyout", { detail: { type: "search" } }))} style={{ textAlign: "left", cursor: "pointer", display: "flex", alignItems: "center" }}>
            <svg
              className="search-icon"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            <div className="w-full bg-[var(--bg)] border border-[var(--rule)] rounded-lg py-[10px] pr-4 pl-10 font-[var(--sans)] text-[0.88rem] text-[var(--ink-muted)]">
              Search {effectiveConfig.name.toLowerCase()} topics...
            </div>
          </button>
          <div className="header-actions">
            <button className="btn btn-ghost" onClick={() => window.dispatchEvent(new CustomEvent("open-flyout", { detail: { type: "login" } }))}>Sign In</button>
            <button className="btn btn-primary" onClick={() => window.dispatchEvent(new CustomEvent("open-flyout", { detail: { type: "subscribe" } }))}>Subscribe</button>
          </div>
        </div>

        <nav className="main-nav">
          <div className="nav-inner">
            {NAV_LINKS.map((link) => {
              const isActive =
                link.href === "/" + categorySlug ||
                (categorySlug === "global-impact" && link.href === "/global-impact");
              return (
                <Link
                  key={link.label}
                  href={link.href}
                  className={`nav-link${isActive ? " active" : ""}`}
                >
                  {link.label}
                </Link>
              );
            })}
          </div>
        </nav>
      </header>

      {/* VERTICAL HEADER */}
      <VerticalHeader config={effectiveConfig} />

      {/* MAIN CONTENT */}
      <main className="main-content">
        <div className="topics-section">
          {loading ? (
            <div style={{ color: "var(--ink-muted)", padding: "100px 0", textAlign: "center", fontStyle: "italic" }}>
              Loading intelligence report...
            </div>
          ) : displayTopics.length > 0 ? (
            displayTopics.map((topic: any) => (
              <TopicCard key={topic.id} topic={topic} />
            ))
          ) : (
            <div className="empty-state" style={{ 
              padding: "80px 40px", 
              textAlign: "center", 
              background: "var(--surface)", 
              borderRadius: "12px",
              border: "1px dashed var(--rule)",
              margin: "20px 0"
            }}>
              <div style={{ fontSize: "3rem", marginBottom: "20px" }}>📡</div>
              <h3 style={{ fontSize: "1.5rem", marginBottom: "12px", color: "var(--ink)" }}>No Active Intelligence</h3>
              <p style={{ color: "var(--ink-muted)", maxWidth: "400px", margin: "0 auto 24px" }}>
                We are currently monitoring {effectiveConfig.name.toLowerCase()} sources, but no topics have reached the required intelligence threshold for reporting.
              </p>
              <button 
                className="btn btn-primary" 
                onClick={() => window.location.reload()}
                style={{ borderRadius: "20px", padding: "8px 24px" }}
              >
                Refresh Monitoring
              </button>
            </div>
          )}

          {/* LOAD MORE - only show if there are topics and hasMore is true */}
          {displayTopics.length > 0 && hasMore && (
            <>
              <div className="load-more-section">
                <button 
                  className="load-more-btn" 
                  onClick={loadMore} 
                  disabled={loadingMore}
                  style={loadingMore ? { background: "var(--bg-tertiary)", borderColor: "var(--border-color)", color: "var(--text-secondary)", cursor: "not-allowed" } : {}}
                >
                  {loadingMore ? "Loading..." : "Load More Topics"}
                </button>
              </div>

              <div className="mobile-load-more">
                <button 
                  className="mobile-load-more-btn" 
                  onClick={loadMore} 
                  disabled={loadingMore}
                  style={loadingMore ? { background: "var(--bg-tertiary)", borderColor: "var(--border-color)", color: "var(--text-secondary)" } : {}}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="6 9 12 15 18 9" />
                  </svg>
                  {loadingMore ? "Loading..." : "Load More Intelligence"}
                </button>
              </div>
            </>
          )}
        </div>

        {/* SIDEBAR */}
        <aside className="sidebar">
          <VerticalInsights
            title={`${effectiveConfig.name} Pulse`}
            color={effectiveConfig.color}
            items={sidebarInsights}
          />
          {sidebarTrending.length > 0 && (
            <KeyTopics title="Trending This Week" topics={sidebarTrending} />
          )}
          <NewsletterCard
            title={effectiveConfig.newsletterTitle}
            description={effectiveConfig.newsletterDesc}
          />
        </aside>
      </main>

      <SiteFooter />
    </>
  );
}

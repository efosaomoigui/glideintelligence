"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import TopicCard from "@/components/TopicCard";
import VerticalInsights from "@/components/VerticalInsights";
import { adaptTopic } from "@/utils/topicAdapter";
import KeyTopics from "@/components/KeyTopics";
import NewsletterCard from "@/components/NewsletterCard";
import SidebarAdCard from "@/components/ads/SidebarAdCard";
import GenericAd, { AdData } from "@/components/ads/GenericAd";
import VerticalHeader from "@/components/VerticalHeader";
import MobileHeader from "@/components/MobileHeader";
import SiteFooter from "@/components/SiteFooter";


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

export default function CategoryClient({ 
  categorySlug, 
  initialData, 
  config 
}: { 
  categorySlug: string; 
  initialData: any;
  config: any;
}) {
  const [apiTopics, setApiTopics] = useState<any[]>(initialData.topics || []);
  const [apiPulse, setApiPulse] = useState<any>(initialData.pulse || null);
  const [apiStats, setApiStats] = useState<any>(initialData.stats || null);
  const [hasMore, setHasMore] = useState(initialData.has_more || false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [page, setPage] = useState(1);
  const [ads, setAds] = useState<AdData[]>([]);

  const fetchAds = async () => {
    try {
      const res = await fetch(`/api/ads/placement/${categorySlug}_feed?limit=3`);
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data)) setAds(data);
      }
    } catch (e) {
      console.error("Ad fetch failed", e);
    }
  };

  useEffect(() => {
    fetchAds();
  }, [categorySlug]);

  const loadMore = async () => {
    if (loadingMore || !hasMore) return;
    setLoadingMore(true);
    const nextPage = page + 1;
    try {
      const res = await fetch(`/api/topics/trending?category=${encodeURIComponent(categorySlug)}&page=${nextPage}`);
      if (res.ok) {
        const data = await res.json();
        setApiTopics(prev => {
          const existingIds = new Set(prev.map(t => t.id));
          const newItems = (data.items || []).filter((t: any) => !existingIds.has(t.id));
          return [...prev, ...newItems];
        });
        setHasMore(data.has_more || false);
        setPage(nextPage);
      }
    } catch (e) {
      console.error("Load more failed", e);
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

  const displayTopics = apiTopics.map(adaptTopic);

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
          id: apiPulse.context?.id,
        },
        {
          label: "Regional Focus",
          value: apiPulse.regional?.name || "ECOWAS",
          text: apiPulse.regional?.description || "Cross-border impact analysis in progress.",
          id: apiPulse.regional?.id,
        },
      ]
    : [
        { label: "Intelligence Pulse", value: "Pending", text: "Collecting cross-source data points..." }
      ];

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
      <MobileHeader activeCategory={effectiveConfig.name} />
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

      <header className="site-header">
        <div className="header-top">
          <div>
            <Link href="/" className="logo" style={{ textDecoration: 'none', fontFamily: '"Playfair Display", Georgia, serif', fontStyle: 'italic', fontWeight: 800 }}>
              <span style={{ color: "#000" }}>PA</span><span style={{ color: "#c0392b" }}>PERLY.</span>
            </Link>
            <div className="tagline">Making Sense of the News</div>
          </div>
          <button className="search-bar" onClick={() => window.dispatchEvent(new CustomEvent("open-flyout", { detail: { type: "search" } }))} style={{ textAlign: "left", cursor: "pointer" }}>
            <svg className="search-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input type="text" placeholder={`Search ${effectiveConfig.name.toLowerCase()} topics...`} readOnly style={{ cursor: "pointer", pointerEvents: "none" }} />
          </button>
          <div className="header-actions">
            <button className="btn btn-ghost" onClick={() => window.dispatchEvent(new CustomEvent("open-flyout", { detail: { type: "login" } }))}>Sign In</button>
            <button className="btn btn-primary" onClick={() => window.dispatchEvent(new CustomEvent("open-flyout", { detail: { type: "subscribe" } }))}>Subscribe</button>
          </div>
        </div>

        <nav className="main-nav">
          <div className="nav-inner">
            {NAV_LINKS.map((link) => {
              const isActive = link.href === "/" + categorySlug || (categorySlug === "global-impact" && link.href === "/global-impact");
              return (
                <Link key={link.label} href={link.href} className={`nav-link${isActive ? " active" : ""}`}>
                  {link.label}
                </Link>
              );
            })}
          </div>
        </nav>
      </header>

      <VerticalHeader config={effectiveConfig} />

      <main className="main-content">
        <div className="topics-section">
          {displayTopics.length > 0 ? (
            displayTopics.map((topic: any, index: number) => {
              const showAd = ads.length > 0 && index > 0 && (index + 1) % 4 === 0;
              const adIndex = (Math.floor((index + 1) / 4) - 1) % ads.length;
              const currentAd = ads[adIndex];

              return (
                <React.Fragment key={topic.id}>
                  <TopicCard topic={topic} />
                  {showAd && currentAd && (
                    <div className="feed-ad-wrapper px-4 md:px-0" style={{ margin: "20px 0" }}>
                      <GenericAd ad={currentAd} />
                    </div>
                  )}
                </React.Fragment>
              );
            })
          ) : (
            <div className="empty-state" style={{ padding: "80px 40px", textAlign: "center", background: "var(--surface)", borderRadius: "12px", border: "1px dashed var(--rule)", margin: "20px 0" }}>
              <div style={{ fontSize: "3rem", marginBottom: "20px" }}>📡</div>
              <h3 style={{ fontSize: "1.5rem", marginBottom: "12px", color: "var(--ink)" }}>No Active Intelligence</h3>
              <p style={{ color: "var(--ink-muted)", maxWidth: "400px", margin: "0 auto 24px" }}>
                We are currently monitoring {effectiveConfig.name.toLowerCase()} sources, but no topics have reached the required intelligence threshold for reporting.
              </p>
              <button className="btn btn-primary" onClick={() => window.location.reload()} style={{ borderRadius: "20px", padding: "8px 24px" }}>Refresh Monitoring</button>
            </div>
          )}

          {displayTopics.length > 0 && hasMore && (
            <>
              <div className="load-more-section">
                <button className="load-more-btn" onClick={loadMore} disabled={loadingMore}>
                  {loadingMore ? "Loading..." : "Load More Topics"}
                </button>
              </div>
            </>
          )}
        </div>

        <aside className="sidebar">
          <VerticalInsights title={`${effectiveConfig.name} Pulse`} color={effectiveConfig.color} items={sidebarInsights} />
          <SidebarAdCard placement={`${categorySlug}_sidebar`} fallbackPlacement="vertical_sidebar" />
          {sidebarTrending.length > 0 && (
            <KeyTopics title="Trending This Week" topics={sidebarTrending} />
          )}
          <NewsletterCard title={effectiveConfig.newsletterTitle} description={effectiveConfig.newsletterDesc} />
        </aside>
      </main>

      <SiteFooter />
    </>
  );
}

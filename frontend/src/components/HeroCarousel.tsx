"use client";

import React, { useState } from "react";

interface Topic {
  id: string | number;
  title: string;
  summary: string;
  bullets: string[];
  sourceCount: number;
  updatedAt: string;
  commentCount: number;
  sources: string[];
  slug: string;
  status: string;
  isPremium: boolean;
  intelligenceLevel: string;
  analysisStatus: string;
  wyntk: string[];
}

interface SponsorAd {
  id: string;
  title: string;
  ad_type: string;
  sponsor?: {
    tagline?: string;
    summary?: string;
    full_content?: string;
    image_url?: string;
    cta_text: string;
    website_link?: string;
  };
}

const SPONSOR_COLORS = ["#3498db", "#2ecc71", "#e74c3c", "#f39c12", "#9b59b6"];

function SponsoredSpotlight() {
  const [sponsorAds, setSponsorAds] = React.useState<SponsorAd[]>([]);
  const [loaded, setLoaded] = React.useState(false);

  React.useEffect(() => {
    const fetchPool = async () => {
      const seen = new Set<string>();
      const pool: SponsorAd[] = [];
      for (let i = 0; i < 4 && pool.length < 2; i++) {
        try {
          const res = await fetch("/api/ads/placement/hero_spotlight");
          // Guard against HTML 404/500 responses — only parse if JSON
          if (!res.ok || !res.headers.get("content-type")?.includes("application/json")) break;
          const ad: SponsorAd = await res.json();
          if (ad && !seen.has(ad.id) && ad.ad_type === "sponsor") {
            seen.add(ad.id);
            pool.push(ad);
          }
        } catch { break; }
      }
      setSponsorAds(pool);
      setLoaded(true);
    };
    fetchPool();
  }, []);

  const openSponsorFlyout = (ad: SponsorAd) => {
    fetch(`/api/ads/render/${ad.id}`, { method: "POST" }).catch(() => {});
    window.dispatchEvent(new CustomEvent("open-flyout", {
      detail: { type: "sponsor", ...ad }
    }));
  };

  const hasSponsorAds = loaded && sponsorAds.length > 0;

  return (
    <div className="ai-pulse" style={{ height: "100%" }}>
      <div className="pulse-header">
        <div className="pulse-icon" style={{ background: "rgba(52, 152, 219, 0.2)", color: "#3498db" }}>
          <span>★</span>
        </div>
        <h3 className="pulse-title">Sponsored Spotlight</h3>
      </div>

      {hasSponsorAds ? sponsorAds.slice(0, 2).map((ad, i) => (
        <div key={ad.id} className="pulse-metric">
          <div className="metric-label" style={{ color: SPONSOR_COLORS[i] }}>
            {ad.sponsor?.tagline || "Sponsored Content"}
          </div>
          <div className="metric-text" style={{ fontWeight: 600, color: "white", marginBottom: "6px" }}>
            {ad.title}
          </div>
          <div className="metric-text" style={{ fontSize: "0.8rem" }}>
            {(ad.sponsor?.summary || "").slice(0, 100)}{(ad.sponsor?.summary?.length ?? 0) > 100 ? "…" : ""}
          </div>
          <button
            onClick={() => openSponsorFlyout(ad)}
            style={{ display: "block", marginTop: "12px", fontSize: "0.8rem", color: "#3498db", fontWeight: 600, background: "none", border: "none", padding: 0, cursor: "pointer" }}
          >
            {ad.sponsor?.cta_text || "Read Report"} →
          </button>
        </div>
      )) : (
        // Fallback demo sponsor cards that wire to the flyout just like real ads
        <>
          {([
            {
              id: "demo-1",
              title: "Agricultural Intervention Fund Yields Results",
              ad_type: "sponsor" as const,
              sponsor: {
                tagline: "Federal Government Focus",
                summary: "New policy aims to stabilize food prices across the nation by providing direct support to smallholder farmers and cooperatives.",
                full_content: "The Federal Government's Agricultural Intervention Fund has recorded significant milestones, channeling over ₦120bn to food production initiatives targeted at stabilizing commodity prices.",
                cta_text: "Read Report",
              }
            },
            {
              id: "demo-2",
              title: "Future Forward Banking Initiative",
              ad_type: "sponsor" as const,
              sponsor: {
                tagline: "Zenith Bank",
                summary: "Unveiling next-generation digital lending platforms designed to scale SMEs across West Africa.",
                full_content: "Zenith Bank's Future Forward initiative introduces an AI-powered credit scoring system giving SMEs instant access to micro-loans up to ₦5m with no collateral requirement.",
                cta_text: "Learn More",
              }
            }
          ] as SponsorAd[]).map((ad, i) => (
            <div key={ad.id} className="pulse-metric">
              <div className="metric-label" style={{ color: SPONSOR_COLORS[i] }}>
                {ad.sponsor?.tagline}
              </div>
              <div className="metric-text" style={{ fontWeight: 600, color: "white", marginBottom: "6px" }}>
                {ad.title}
              </div>
              <div className="metric-text" style={{ fontSize: "0.8rem" }}>
                {(ad.sponsor?.summary || "").slice(0, 90)}…
              </div>
              <button
                onClick={() => openSponsorFlyout(ad)}
                style={{ display: "inline-flex", alignItems: "center", gap: "4px", marginTop: "12px", fontSize: "0.8rem", color: "#3498db", fontWeight: 600, background: "none", border: "none", padding: 0, cursor: "pointer" }}
              >
                {ad.sponsor?.cta_text} →
              </button>
            </div>
          ))}
        </>
      )}

      {/* Bottom slot: small AdSense */}
      <div className="pulse-metric" style={{ borderBottom: "none", paddingBottom: 0, marginBottom: 0 }}>
        <div className="metric-label" style={{ color: "#888", fontSize: "0.65rem", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "8px" }}>
          Advertisement
        </div>
        <div style={{
          minHeight: "90px",
          background: "rgba(255,255,255,0.03)",
          border: "1px dashed rgba(255,255,255,0.1)",
          borderRadius: "6px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "#444",
          fontSize: "0.72rem",
          letterSpacing: "0.05em"
        }}>
          {/* Paste AdSense snippet here */}
          Ad Slot
        </div>
      </div>
    </div>
  );
}

export default function HeroCarousel({ topics: initialTopics }: { topics: Topic[] }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [topics, setTopics] = useState(initialTopics);

  React.useEffect(() => {
    setTopics(initialTopics);
  }, [initialTopics]);

  React.useEffect(() => {
    const handler = (e: Event) => {
      const { topicId, commentCount } = (e as CustomEvent).detail || {};
      if (!topicId) return;
      setTopics(prev => prev.map(t =>
        String(t.id) === String(topicId) || t.slug === String(topicId)
          ? { ...t, commentCount: commentCount !== undefined ? commentCount : t.commentCount }
          : t
      ));
    };
    window.addEventListener("topic-viewed", handler);
    return () => window.removeEventListener("topic-viewed", handler);
  }, []);

  if (!topics || topics.length === 0) return null;

  const topic = topics[currentIndex];
  const displaySources = topic.sources.slice(0, 3);
  const remainingSources = topic.sources.length - 3;

  return (
    <section className="hero-intelligence">
      <div className="hero-container relative">
        {topics.length > 1 && (
          <div className="hero-carousel-nav">
            <button className="carousel-btn" onClick={() => setCurrentIndex((prev) => (prev - 1 + topics.length) % topics.length)} aria-label="Previous story">
              <svg width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <button className="carousel-btn" onClick={() => setCurrentIndex((prev) => (prev + 1) % topics.length)} aria-label="Next story">
              <svg width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        )}

        <div className="hero-content-wrapper" key={String(topic.id)}>
          <div className="hero-label-container" style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '24px' }}>
            <div className="hero-label" style={{ marginBottom: 0 }}>
              <div className="live-pulse"></div>
              {topic.status.toUpperCase()} STORY
            </div>
            {topic.isPremium && (
              <div className="hero-label premium" style={{ marginBottom: 0, background: "rgba(var(--accent-rgb, 192,57,43), 0.15)", color: "var(--accent)", border: "1px solid var(--accent)", marginLeft: '8px' }}>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" style={{ marginRight: "6px" }}>
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87L18.18 21 12 17.77 5.82 21 7 14.14l-5-4.87 6.91-1.01L12 2z" />
                </svg>
                PREMIUM INTELLIGENCE
              </div>
            )}
            {topics.length > 1 && (
              <div className="carousel-indicators">
                {topics.map((_, idx) => (
                  <div
                    key={idx}
                    className={`carousel-dot ${idx === currentIndex ? "active" : ""}`}
                    onClick={() => setCurrentIndex(idx)}
                  />
                ))}
              </div>
            )}
          </div>

          <h1 className="hero-title">{topic.title}</h1>

          <div className="hero-meta">
            <span>
              <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="10" strokeWidth={2}></circle>
                <path strokeLinecap="round" strokeWidth={2} d="M12 6v6l4 2"></path>
              </svg>
              Updated {topic.updatedAt.replace("Updated ", "")}
            </span>
            <span>•</span>
            <span>{topic.sourceCount} sources • {topic.commentCount} comments</span>
          </div>

          <div className="hero-summary">
            <div className="summary-tag">60-Second Brief</div>
            <div className="summary-content">{topic.summary}</div>

            {topic.wyntk && topic.wyntk.length > 0 && (
              <ul className="summary-bullets">
                {topic.wyntk.map((bullet: string, i: number) => (
                  <li key={i}>{bullet}</li>
                ))}
              </ul>
            )}

            <div className="hero-actions">
              <a href="#" onClick={(e) => {
                e.preventDefault();
                window.dispatchEvent(new CustomEvent("open-flyout", { detail: { id: topic.id, slug: topic.slug } }));
              }} className="btn-read-full open-detail" data-id={topic.id}>
                Read Full Intelligence →
              </a>
              <div className="source-chips">
                {displaySources.map((source, i) => (
                  <div key={i} className="source-chip">{source}</div>
                ))}
                {remainingSources > 0 && <div className="source-chip">+{remainingSources} more</div>}
              </div>
            </div>
          </div>
        </div>

        {/* Sponsored Spotlight sidebar — live DB ads or elegant fallback */}
        <div className="hero-sidebar">
          <SponsoredSpotlight />
        </div>
      </div>
    </section>
  );
}

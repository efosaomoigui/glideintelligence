"use client";

import React, { useEffect, useState } from "react";
import TopicCard from "@/components/TopicCard";
import GenericAd, { AdData } from "@/components/ads/GenericAd";
import { formatDistanceToNow } from "date-fns";

// Helper to format numbers like 2800 -> 2.8K
function formatViews(num: number): string {
  if (!num) return "0";
  if (num >= 1000000) return (num / 1000000).toFixed(1).replace(/\.0$/, "") + "M";
  if (num >= 1000) return (num / 1000).toFixed(1).replace(/\.0$/, "") + "K";
  return num.toString();
}

// Safe relative time using date-fns and fallback
function getSafeRelativeTime(dateStr: string, fallbackStr: string): string {
  if (!dateStr) return fallbackStr || "Recently";
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return fallbackStr || "Recently";
    return formatDistanceToNow(d, { addSuffix: true });
  } catch {
    return fallbackStr || "Recently";
  }
}

export default function DynamicIntelligence({ children }: { children?: React.ReactNode }) {
  const [selectedPeriod, setSelectedPeriod] = useState<string>("today");
  const [page, setPage] = useState<number>(1);
  const [topics, setTopics] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [hasMore, setHasMore] = useState<boolean>(true);

  const fetchTopics = async (period: string, pageNum: number, append = false) => {
    setLoading(true);
    try {
      // Correct endpoint: /api/topics/trending?filter=<period>&page=<n>
      const res = await fetch(`/api/topics/trending?filter=${period}&page=${pageNum}`);

      if (!res.ok) {
        throw new Error(`API returned status: ${res.status}`);
      }

      const text = await res.text();
      let data: any;
      try {
        data = JSON.parse(text);
      } catch {
        throw new Error("API did not return valid JSON");
      }

      // Backend returns PaginatedResponse: { items, total, page, limit, has_more }
      const AVATAR_COLORS = ["#e74c3c", "#9b59b6", "#1abc9c", "#34495e", "#e67e22", "#2980b9", "#c0392b", "#16a085"];

      const transformed = (data.items || []).map((t: any) => ({
        id: String(t.id),
        title: t.title,
        brief: t.ai_brief || t.description || "",
        updatedAt: getSafeRelativeTime(t.updated_at, t.updated_at_str),
        category: t.badge || t.category || "Trending",
        isDeveloping: t.is_trending || t.status === "developing",
        // Perspectives from source_perspectives (sentiment bars)
        perspectives: (t.source_perspectives || []).map((p: any) => ({
          source: p.source_name || p.frame_label || "",
          sentiment: p.sentiment as "positive" | "negative" | "neutral",
          score: parseFloat(String(p.sentiment_percentage).replace("%", "").replace("+", "")) || 0,
        })),
        // Regional impacts
        impacts: (t.regional_impacts || []).map((i: any) => ({
          icon: i.icon || "📊",
          title: i.title,
          value: i.value,
        })),
        // Source avatars: use real publication names from sources[] array
        sourceAvatars: (t.sources || []).slice(0, 4).map((s: any, idx: number) => {
          const name: string = s.name || "Unknown";
          return {
            initials: name.substring(0, 2).toUpperCase(),
            color: AVATAR_COLORS[idx % AVATAR_COLORS.length],
          };
        }),
        sourceCount: t.source_count || (t.sources?.length ?? 0) || 0,
        commentCount: t.engagement?.comments ?? t.comment_count ?? 0,
        // Raw integer so TopicCard fmt() formats it correctly and flyout math stays clean
        viewCount: t.view_count ?? 0,
        isPremium: t.is_premium ?? false,
        intelligenceLevel: t.intelligence_level ?? "Standard",
        analysisStatus: t.analysis_status ?? "stable",
      }));


      // Deduplicate by ID to avoid React duplicate-key warnings on overlapping pages
      setTopics(prev => {
        if (!append) return transformed;
        const existingIds = new Set(prev.map((t: any) => t.id));
        const newItems = transformed.filter((t: any) => !existingIds.has(t.id));
        return [...prev, ...newItems];
      });
      setHasMore(data.has_more ?? false);
    } catch (e) {
      console.error("Failed to fetch topics:", e);
    } finally {
      setLoading(false);
    }
  };

  const [ads, setAds] = useState<AdData[]>([]);

  const fetchAds = async () => {
    try {
      const pool: AdData[] = [];
      for (let i = 0; i < 3; i++) {
        const res = await fetch("/api/ads/placement/homepage_feed");
        if (res.ok && res.headers.get("content-type")?.includes("application/json")) {
          const ad = await res.json();
          if (ad && !pool.find(a => a.id === ad.id)) {
            pool.push(ad);
          }
        } else {
          break; // No ads configured for this placement
        }
      }
      setAds(pool);
    } catch (e) {
      // Silently fail — ads are non-critical
    }
  };

  // Initial load and when period changes
  useEffect(() => {
    setPage(1);
    fetchTopics(selectedPeriod, 1, false);
    fetchAds();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedPeriod]);

  // Load more when page increments
  useEffect(() => {
    if (page > 1) {
      fetchTopics(selectedPeriod, page, true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  const handlePeriodClick = (period: string) => {
    if (period !== selectedPeriod) {
      setSelectedPeriod(period);
    }
  };

  const loadMore = () => {
    if (hasMore && !loading) {
      setPage(prev => prev + 1);
    }
  };

  // Listen for real-time view/comment updates dispatched by DetailFlyout
  useEffect(() => {
    const handler = (e: Event) => {
      const { topicId, viewCount, commentCount } = (e as CustomEvent).detail || {};
      if (!topicId) return;
      setTopics(prev => prev.map(t =>
        t.id === String(topicId)
          ? {
              ...t,
              viewCount: viewCount !== undefined ? viewCount : t.viewCount,
              commentCount: commentCount !== undefined ? commentCount : t.commentCount,
            }
          : t
      ));
    };
    window.addEventListener("topic-viewed", handler);
    return () => window.removeEventListener("topic-viewed", handler);
  }, []);

  return (
    <>
      {/* ── Mobile Filter Tabs (sticky, horizontal scroll) ── */}
      <div className="mobile-filter-tabs" role="tablist" aria-label="Filter intelligence by time">
        <button 
          className={`filter-pill ${selectedPeriod === "today" ? "active" : ""}`} 
          role="tab"
          onClick={() => handlePeriodClick("today")}
        >
          Today
        </button>
        <button 
          className={`filter-pill ${selectedPeriod === "week" ? "active" : ""}`} 
          role="tab"
          onClick={() => handlePeriodClick("week")}
        >
          This Week
        </button>
        <button 
          className={`filter-pill ${selectedPeriod === "month" ? "active" : ""}`} 
          role="tab"
          onClick={() => handlePeriodClick("month")}
        >
          This Month
        </button>
        <button 
          className={`filter-pill ${selectedPeriod === "developing" ? "active" : ""}`} 
          role="tab"
          onClick={() => handlePeriodClick("developing")}
        >
          🔴 Developing
        </button>
      </div>

      <main className="main-content">
        {/* TOPICS FEED */}
        <div className="topics-section">
          <div className="section-header">
            <h2 className="section-title">Today&apos;s Glide</h2>
            {/* Desktop filter (hidden on mobile) */}
            <div className="time-filter">
              <button 
                className={selectedPeriod === "today" ? "active" : ""} 
                onClick={() => handlePeriodClick("today")}
              >
                Today
              </button>
              <button 
                className={selectedPeriod === "week" ? "active" : ""} 
                onClick={() => handlePeriodClick("week")}
              >
                This Week
              </button>
              <button 
                className={selectedPeriod === "month" ? "active" : ""} 
                onClick={() => handlePeriodClick("month")}
              >
                This Month
              </button>
              <button 
                className={selectedPeriod === "developing" ? "active" : ""} 
                onClick={() => handlePeriodClick("developing")}
              >
                Developing
              </button>
            </div>
          </div>

          {topics.map((topic, index) => {
            // Render an ad every 3 topics, starting after the 2nd topic (index 1)
            const showAd = ads.length > 0 && index > 0 && (index + 1) % 3 === 0;
            const adIndex = (Math.floor((index + 1) / 3) - 1) % ads.length;
            const currentAd = ads[adIndex];

            return (
              <React.Fragment key={topic.id}>
                <TopicCard topic={topic} />
                {showAd && currentAd && (
                  <div className="feed-ad-wrapper px-4 md:px-0">
                    <GenericAd ad={currentAd} />
                  </div>
                )}
              </React.Fragment>
            );
          })}

          {loading && <div style={{textAlign: "center", padding: "1rem"}}>Loading...</div>}

          {/* Mobile Load More */}
          {hasMore && (
            <div className="mobile-load-more">
              <button className="mobile-load-more-btn" onClick={loadMore} disabled={loading}
                style={{
                  background: loading ? undefined : "var(--accent)",
                  borderColor: "var(--accent)",
                  color: loading ? undefined : "#fff",
                  fontWeight: 700,
                  boxShadow: loading ? undefined : "0 2px 8px rgba(192,57,43,0.30)"
                }}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="6 9 12 15 18 9" />
                </svg>
                {loading ? "Loading..." : "Load More Intelligence"}
              </button>
            </div>
          )}

          {/* Desktop Load More */}
          {hasMore && (
            <div className="load-more-section">
              <button className="load-more-btn" onClick={loadMore} disabled={loading}
                style={{
                  background: loading ? undefined : "var(--accent)",
                  borderColor: "var(--accent)",
                  color: loading ? undefined : "#fff",
                  fontWeight: 700,
                  boxShadow: loading ? undefined : "0 2px 8px rgba(192,57,43,0.30)",
                  padding: "10px 28px",
                  borderRadius: "8px",
                  border: "2px solid var(--accent)",
                  cursor: loading ? "default" : "pointer",
                  fontSize: "0.9rem",
                  transition: "all 0.2s"
                }}
              >
                {loading ? "Loading..." : "Load More Intelligence"}
              </button>
            </div>
          )}
        </div>
        
        {children}
      </main>
    </>
  );
}

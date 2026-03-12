"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";

interface Perspective {
  source: string;
  sentiment: "positive" | "negative" | "neutral";
  score: number;
}

interface ImpactItem {
  icon: string;
  title: string;
  value: string;
}

interface SourceAvatar {
  initials: string;
  color: string;
}

interface TopicCardProps {
  topic: {
    id: string;
    title: string;
    category: string;
    isDeveloping?: boolean;
    updatedAt: string;
    brief: string;
    perspectives: Perspective[];
    impacts: ImpactItem[];
    sourceAvatars: SourceAvatar[];
    sourceCount: number;
    commentCount: number;
    viewCount: number;  // raw integer from DB (formatted for display by fmt())
    isPremium?: boolean;
    intelligenceLevel?: string;
    analysisStatus?: string;
  };
}

// Format number helper
function fmt(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1).replace(/\.0$/, "") + "M";
  if (n >= 1_000) return (n / 1_000).toFixed(1).replace(/\.0$/, "") + "K";
  return String(n);
}

export default function TopicCard({ topic }: TopicCardProps) {
  const [liveComments, setLiveComments] = useState(topic.commentCount || 0);
  const [liveViews, setLiveViews] = useState(() => fmt(topic.viewCount || 0));
  const [liveViewsRaw, setLiveViewsRaw] = useState(topic.viewCount || 0); // raw int for math

  // Sync if parent re-renders with fresh data
  useEffect(() => { setLiveComments(topic.commentCount || 0); }, [topic.commentCount]);
  useEffect(() => { setLiveViewsRaw(topic.viewCount || 0); setLiveViews(fmt(topic.viewCount || 0)); }, [topic.viewCount]);

  // Listen for real-time updates dispatched by DetailFlyout when a topic is opened
  useEffect(() => {
    const handler = (e: Event) => {
      const { topicId, viewCount, commentCount } = (e as CustomEvent).detail || {};
      if (String(topicId) !== String(topic.id)) return;
      if (viewCount !== undefined) {
        const n = typeof viewCount === 'number' ? viewCount : parseInt(String(viewCount), 10) || 0;
        setLiveViewsRaw(n);
        setLiveViews(fmt(n));
      }
      if (commentCount !== undefined) setLiveComments(commentCount);
    };
    window.addEventListener("topic-viewed", handler);
    return () => window.removeEventListener("topic-viewed", handler);
  }, [topic.id]);

  const handleOpenDetail = (e: React.MouseEvent) => {
    e.preventDefault();
    const slug = topic.title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
    window.dispatchEvent(new CustomEvent("open-flyout", {
      detail: {
        id: topic.id,
        slug,
        viewCount: liveViewsRaw,   // always a raw integer — safe for arithmetic in flyout
        commentCount: liveComments,
      }
    }));
  };

  // Determine status label and class
  const isEnriching = topic.analysisStatus === 'pending' || topic.analysisStatus === 'processing' || topic.analysisStatus === 'pipeline_failed';
  const statusLabel = isEnriching ? "Enriching Intelligence..." : (topic.isDeveloping ? "Developing" : topic.category);

  return (
    <div 
      className="block open-detail" 
      data-id={topic.id} 
      onClick={handleOpenDetail}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          handleOpenDetail(e as any);
        }
      }}
    >
      <article className="topic-card hover:border-accent transition-colors cursor-pointer">
        <div className="topic-header">
          <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
            <div className={`topic-badge${topic.isDeveloping || isEnriching ? " developing" : ""}`}>
              {(topic.isDeveloping || isEnriching) && (
                <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                  <circle cx="12" cy="12" r="10" />
                </svg>
              )}
              {statusLabel}
            </div>
            {topic.isPremium && (
              <div className="topic-badge premium" style={{ background: "rgba(var(--accent-rgb, 192,57,43), 0.15)", color: "var(--accent)", border: "1px solid var(--accent)" }}>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" style={{ marginRight: "4px" }}>
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87L18.18 21 12 17.77 5.82 21 7 14.14l-5-4.87 6.91-1.01L12 2z" />
                </svg>
                Premium Intelligence
              </div>
            )}
          </div>
        <div className="topic-status">
          <div className="update-time">
            <svg
              width="14"
              height="14"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            {topic.updatedAt}
          </div>
        </div>
      </div>

      <h3 className="topic-title">{topic.title}</h3>

      {/* PILLAR 2: AI SUMMARY */}
      <div className="ai-brief">
        <div className="brief-label">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 10V3L4 14h7v7l9-11h-7z"
            />
          </svg>
          Glide Brief
        </div>
        <p className="brief-text">{topic.brief}</p>
      </div>

      {/* PILLAR 3: PERSPECTIVE MAP */}
      <div className="perspective-map desktop-only">
        <div className="perspective-label">
          <svg
            width="14"
            height="14"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            />
          </svg>
          How Different Sources Frame This
        </div>
        <div className="perspective-grid">
          {topic.perspectives.map((p, i) => (
            <div key={i} className="perspective-item">
              <div className="perspective-source">{p.source}</div>
              <div className="perspective-bar">
                <div
                  className={`perspective-fill ${p.sentiment}`}
                  style={{ width: `${Math.abs(p.score)}%` }}
                ></div>
              </div>
              <div className="perspective-score">
                {p.score > 0 ? "+" : ""}
                {p.score}%
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* PILLAR 4: REGIONAL IMPACT */}
      <div className="regional-impact desktop-only">
        <div className="impact-label">
          <svg
            width="14"
            height="14"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
                Impact Analysis
              </div>
        <div className="impact-grid">
          {topic.impacts.map((item, i) => (
            <div key={i} className="impact-item">
              <div className="impact-icon">{item.icon}</div>
              <div className="impact-title">{item.title}</div>
              <div className="impact-value">{item.value}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="topic-footer">
        <div className="source-count">
          <div className="source-avatars">
            {topic.sourceAvatars.slice(0, 3).map((avatar, i) => (
              <div
                key={i}
                className="source-avatar"
                style={{ background: avatar.color }}
              >
                {avatar.initials}
              </div>
            ))}
            {topic.sourceCount > 3 && (
              <div className="source-avatar" style={{ background: "#34495e" }}>
                +{topic.sourceCount - 3}
              </div>
            )}
          </div>
          <span>{topic.sourceCount} {topic.sourceCount === 1 ? 'Source' : 'Sources'}</span>
        </div>
        <div className="engagement-stats">
          <span>
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
              />
            </svg>
            {liveComments}
          </span>
          <span>
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
              />
            </svg>
            {liveViews}
          </span>
        </div>
      </div>
    </article>
    </div>
  );
}

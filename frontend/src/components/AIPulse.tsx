"use client";

import React, { useEffect, useState } from "react";

interface SidebarPulse {
  sentiment_label: string;
  sentiment_score: number;
  sentiment_text: string;
  trending_topic: string;
  trending_id?: number | string;
  trending_text: string;
  regional_focus: string;
  regional_id?: number | string;
  regional_text: string;
}

interface SidebarVoice {
  initials: string;
  name: string;
  role: string;
  quote: string;
  color: string;
}

interface SidebarPoll {
  question: string;
  options: string[];
  responses: number;
  closes_in_hours: number;
}

interface SidebarData {
  pulse: SidebarPulse;
  voices: SidebarVoice[];
  poll: SidebarPoll;
}

// All API calls use relative /api/ paths — proxied by Next.js to localhost:8000

export default function AIPulse({ initialData }: { initialData?: SidebarPulse }) {
  const [data, setData] = useState<SidebarPulse | null>(initialData || null);

  useEffect(() => {
    if (!initialData) {
      fetch(`/api/sidebar`)
        .then((r) => r.json())
        .then((json) => setData(json.pulse))
        .catch(() => {/* silently fail – static fallback below */});
    }
  }, [initialData]);

  // Fallback while loading or on error — preserve exact original layout/classes
  const pulse: SidebarPulse = data ?? {
    sentiment_label: "Cautiously Optimistic",
    sentiment_score: 68,
    sentiment_text: "Economic sentiment improved this week following Naira gains and reserve growth.",
    trending_topic: "Monetary Policy",
    trending_text: "Dominating 82% of economic coverage this week. Key trigger: CBN rate hold + reserve announcement.",
    regional_focus: "ECOWAS Stability",
    regional_text: "West African bloc tensions rise as Mali, Burkina Faso, Niger formalize exit. Nigeria's mediator role questioned.",
  };

  const truncate = (text: string, maxWords: number = 15) => {
    if (!text) return "";
    const words = text.split(/\s+/);
    if (words.length <= maxWords) return text;
    return words.slice(0, maxWords).join(" ") + "...";
  };

  const handleOpenFlyout = (id?: number | string) => {
    if (!id) return;
    window.dispatchEvent(
      new CustomEvent("open-flyout", {
        detail: { id: String(id) },
      })
    );
  };

  return (
    <div className="ai-pulse">
      <div className="pulse-header">
        <div className="pulse-icon">✦</div>
        <div className="pulse-title">Glide Pulse</div>
      </div>

      <div className="pulse-metric">
        <div className="metric-label">Overall Sentiment</div>
        <div className="metric-value">
          {pulse.sentiment_label}
          <span className={`metric-badge ${pulse.sentiment_score >= 50 ? "positive" : "negative"}`}>
            {pulse.sentiment_score >= 50 ? `+${Math.round(pulse.sentiment_score - 50)}%` : `${Math.round(pulse.sentiment_score - 50)}%`}
          </span>
        </div>
        <div className="metric-text">{pulse.sentiment_text}</div>
        <div className="pulse-bar">
          <div className="pulse-bar-fill" style={{ width: `${pulse.sentiment_score}%` }}></div>
        </div>
      </div>

      <div className="pulse-metric">
        <div className="metric-value" style={{ fontSize: "1.1rem" }}>
          {pulse.trending_topic}
        </div>
        <div className="metric-text">
          {truncate(pulse.trending_text)}
          {pulse.trending_id && (
            <button 
              onClick={() => handleOpenFlyout(pulse.trending_id)}
              className="read-more-pulse"
              style={{ padding: 0, background: 'none', border: 'none', color: '#e67e22', cursor: 'pointer', display: 'block', fontSize: '0.8rem', fontWeight: 'bold', marginTop: '4px', textShadow: 'none' }}
            >
              Read more analysis
            </button>
          )}
        </div>
      </div>

      <div className="pulse-metric">
        <div className="metric-label">Regional Focus</div>
        <div className="metric-value" style={{ fontSize: "1.1rem" }}>
          {pulse.regional_focus}
        </div>
        <div className="metric-text">
          {truncate(pulse.regional_text)}
          {pulse.regional_id && (
            <button 
              onClick={() => handleOpenFlyout(pulse.regional_id)}
              className="read-more-pulse"
              style={{ padding: 0, background: 'none', border: 'none', color: '#e67e22', cursor: 'pointer', display: 'block', fontSize: '0.8rem', fontWeight: 'bold', marginTop: '4px', textShadow: 'none' }}
            >
              Read more analysis
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

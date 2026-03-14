"use client";

import React from "react";

interface InsightItem {
  label: string;
  value: string;
  text: string;
  id?: number | string;
}

interface VerticalInsightsProps {
  title: string;
  color: string;
  items: InsightItem[];
}

export default function VerticalInsights({ title, color, items }: VerticalInsightsProps) {
  return (
    <div
      className="sidebar-card vertical-insights"
      style={{
        background: `linear-gradient(135deg, ${color} 0%, ${color}d9 100%)`,
      }}
    >
      <div className="sidebar-title">
        <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        {title}
      </div>

      {items.map((item, i) => {
        const words = item.text.split(/\s+/);
        const isTruncated = words.length > 30;
        const displayText = isTruncated ? words.slice(0, 30).join(" ") + "..." : item.text;

        const handleOpenFlyout = () => {
          if (!item.id) return;
          window.dispatchEvent(
            new CustomEvent("open-flyout", {
              detail: { id: String(item.id) },
            })
          );
        };

        return (
          <div key={i} className="insight-item">
            <div className="insight-label">{item.label}</div>
            <div className="insight-value">{item.value}</div>
            <div className="insight-text">
              {displayText}
              {item.id && (
                <button 
                  onClick={handleOpenFlyout}
                  className="read-more-pulse"
                  style={{ padding: 0, background: 'none', border: 'none', color: '#e67e22', cursor: 'pointer', display: 'block', fontSize: '0.75rem', fontWeight: 'bold', marginTop: '4px', textDecoration: 'underline' }}
                >
                  Read more analysis
                </button>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

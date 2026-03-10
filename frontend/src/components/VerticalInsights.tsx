"use client";

import React from "react";

interface InsightItem {
  label: string;
  value: string;
  text: string;
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

      {items.map((item, i) => (
        <div key={i} className="insight-item">
          <div className="insight-label">{item.label}</div>
          <div className="insight-value">{item.value}</div>
          <div className="insight-text">{item.text}</div>
        </div>
      ))}
    </div>
  );
}

"use client";

import React from "react";
import Link from "next/link";

interface VerticalConfig {
  name: string;
  icon: string;
  description: string;
  color: string;
  stats: { value: string; label: string }[];
}

interface VerticalHeaderProps {
  config: VerticalConfig;
}

export default function VerticalHeader({ config }: VerticalHeaderProps) {
  return (
    <section
      className="vertical-header"
      style={{
        background: `linear-gradient(135deg, ${config.color} 0%, ${config.color}cc 100%)`,
      }}
    >
      <div className="vertical-container">
        <nav className="vertical-breadcrumb">
          <Link href="/">Home</Link>
          <span>/</span>
          <span>{config.name}</span>
        </nav>

        <div className="vertical-title-wrapper" style={{ display: "flex", alignItems: "center", gap: "16px", marginBottom: "16px" }}>
          <div className="vertical-icon" style={{ fontSize: "2.5rem", marginBottom: 0 }}>{config.icon}</div>
          <h1 className="vertical-title" style={{ marginBottom: 0 }}>{config.name} Intelligence</h1>
        </div>
        <p className="vertical-description">{config.description}</p>

        <div className="vertical-stats">
          {config.stats.map((stat, i) => (
            <div key={i} className="vertical-stat">
              <div className="stat-value">{stat.value}</div>
              <div className="stat-label">{stat.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

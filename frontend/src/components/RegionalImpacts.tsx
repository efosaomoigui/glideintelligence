"use client";

import React from "react";

interface ImpactItem {
  impact_category: string;
  icon: string;
  title: string;
  value: string;
  severity: "low" | "medium" | "high" | "critical";
  context: string;
}

interface RegionalImpactsProps {
  impacts: ImpactItem[];
}

export default function RegionalImpacts({ impacts }: RegionalImpactsProps) {
  return (
    <div className="bg-card border border-rule rounded-xl p-8 shadow-sm">
      <div className="flex items-center gap-3 mb-8 pb-4 border-b border-rule">
        <h3 className="font-serif text-[1.25rem] font-black tracking-tight text-ink uppercase">Pillar 4: Regional Impact</h3>
        <span className="text-[0.65rem] font-bold text-ink-muted uppercase tracking-[0.2em] ml-auto">Geopolitical Tracking</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {impacts.map((impact, i) => (
          <div key={i} className="bg-bg/40 border border-rule/60 rounded-lg p-6 hover:border-accent/40 transition-all group">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <span className="text-2xl">{impact.icon}</span>
                <div>
                  <div className="text-[0.65rem] font-bold text-ink-muted uppercase tracking-widest leading-none mb-1">{impact.impact_category}</div>
                  <div className="font-serif text-[1.1rem] font-bold text-ink leading-tight">{impact.title}</div>
                </div>
              </div>
              <span className={`px-2 py-0.5 rounded text-[0.6rem] font-black uppercase tracking-widest shadow-sm ${
                impact.severity === 'critical' ? 'bg-accent text-white' :
                impact.severity === 'high' ? 'bg-accent/10 text-accent' :
                impact.severity === 'medium' ? 'bg-accent-warm text-white' :
                'bg-green/10 text-green'
              }`}>
                {impact.severity}
              </span>
            </div>

            <div className="text-[1.2rem] font-black text-ink mb-3 tracking-tight group-hover:text-accent transition-colors">
              {impact.value}
            </div>

            <p className="text-[0.85rem] leading-relaxed text-ink-mid font-medium">
              {impact.context}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

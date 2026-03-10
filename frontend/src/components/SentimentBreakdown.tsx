"use client";

import React from "react";

interface SentimentPillar {
  dimension_type: string;
  dimension_value: string;
  sentiment: "positive" | "negative" | "neutral" | "mixed";
  sentiment_score: number;
  percentage: number;
  icon: string;
  description: string;
}

interface SentimentBreakdownProps {
  pillars: SentimentPillar[];
}

export default function SentimentBreakdown({ pillars }: SentimentBreakdownProps) {
  return (
    <div className="bg-card border border-rule rounded-xl p-8 shadow-sm">
      <div className="flex items-center gap-3 mb-8 pb-4 border-b border-rule">
        <h3 className="font-serif text-[1.25rem] font-black tracking-tight text-ink uppercase">Pillar 1: Narrative Alignment</h3>
        <span className="text-[0.65rem] font-bold text-ink-muted uppercase tracking-[0.2em] ml-auto">Sentiment Matrix</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {pillars.map((pillar, i) => (
          <div key={i} className="space-y-4">
            <div className="flex justify-between items-end">
              <div>
                <div className="text-[0.65rem] font-bold text-ink-muted uppercase tracking-widest mb-1">{pillar.dimension_type}</div>
                <div className="flex items-center gap-2">
                  <span className="text-xl">{pillar.icon}</span>
                  <span className="font-bold text-ink">{pillar.dimension_value}</span>
                </div>
              </div>
              <div className="text-right">
                <div className={`text-[0.9rem] font-black uppercase tracking-widest ${
                  pillar.sentiment === 'positive' ? 'text-green' : 
                  pillar.sentiment === 'negative' ? 'text-accent' : 
                  'text-blue'
                }`}>
                  {pillar.sentiment}
                </div>
                <div className="text-[0.7rem] font-mono font-bold text-ink-muted">{pillar.percentage}% Coverage</div>
              </div>
            </div>

            <div className="h-2.5 bg-bg rounded-full overflow-hidden relative shadow-inner">
              <div 
                className={`h-full rounded-full transition-all duration-1000 ${
                  pillar.sentiment === 'positive' ? 'bg-linear-to-r from-green to-green/60' : 
                  pillar.sentiment === 'negative' ? 'bg-linear-to-r from-accent to-accent/60' : 
                  'bg-linear-to-r from-blue to-blue/60'
                }`}
                style={{ width: `${pillar.percentage}%` }} 
              />
            </div>

            <p className="text-[0.82rem] leading-relaxed text-ink-mid font-medium italic">
              {pillar.description}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

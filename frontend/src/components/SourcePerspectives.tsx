"use client";

import React from "react";

interface Perspective {
  source_name: string;
  source_type: string;
  frame_label: string;
  sentiment: string;
  sentiment_percentage: string;
  key_narrative: string;
}

interface SourcePerspectivesProps {
  perspectives: Perspective[];
}

export default function SourcePerspectives({ perspectives }: SourcePerspectivesProps) {
  return (
    <div className="bg-card border border-rule rounded-xl p-8 shadow-sm">
      <div className="flex items-center gap-3 mb-8 pb-4 border-b border-rule">
        <h3 className="font-serif text-[1.25rem] font-black tracking-tight text-ink uppercase">Pillar 3: Perspective Map</h3>
        <span className="text-[0.65rem] font-bold text-ink-muted uppercase tracking-[0.2em] ml-auto">Source Diversity</span>
      </div>

      <div className="space-y-8">
        {perspectives.map((p, i) => (
          <div key={i} className="group relative">
            <div className="flex flex-wrap items-end justify-between gap-4 mb-4">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-bg border border-rule rounded flex items-center justify-center font-black text-[0.7rem] uppercase tracking-widest text-ink/30 shadow-sm group-hover:border-accent group-hover:text-accent transition-all">
                  {p.source_name.substring(0, 3)}
                </div>
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-extrabold text-ink text-[0.95rem]">{p.source_name}</span>
                    <span className="text-[0.6rem] font-bold bg-bg px-2 py-0.5 rounded border border-rule uppercase tracking-widest text-ink-muted">{p.source_type}</span>
                  </div>
                  <div className="text-[0.75rem] font-bold text-accent uppercase tracking-[0.1em]">{p.frame_label}</div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-[1.1rem] font-black font-mono tracking-tighter text-ink leading-none">{p.sentiment_percentage}</div>
                <div className="text-[0.6rem] font-bold uppercase tracking-widest text-ink-muted mt-1 leading-none">Framing Delta</div>
              </div>
            </div>

            <p className="text-[0.88rem] leading-relaxed text-ink-mid font-medium border-l-2 border-rule pl-4 group-hover:border-accent/40 transition-colors">
              {p.key_narrative}
            </p>

            {/* Visual indicator of divergence */}
            <div className="mt-4 flex gap-1 h-1.5 opacity-30 group-hover:opacity-100 transition-opacity">
               {[...Array(20)].map((_, j) => {
                 const isHigh = Math.abs(parseInt(p.sentiment_percentage)) > (j * 5);
                 return (
                   <div 
                    key={j} 
                    className={`flex-grow rounded-sm ${isHigh ? 'bg-accent' : 'bg-rule'}`}
                   />
                 );
               })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

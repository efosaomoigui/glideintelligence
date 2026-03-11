"use client";

import React, { useEffect, useState } from "react";

export default function Ticker() {
  const [items, setItems] = useState<{ id: string | number; title: string }[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/topics/trending?filter=today&page=1")
      .then((r) => r.json())
      .then((data) => {
        if (data && Array.isArray(data.items)) {
          setItems(data.items.slice(0, 10).map((t: any) => ({
            id: t.id,
            slug: t.slug || t.title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, ""),
            title: t.title
          })));
        }
      })
      .catch((err) => console.error("Failed to fetch ticker updates:", err))
      .finally(() => setLoading(false));
  }, []);

  const handleTopicClick = (item: { id: string | number; slug: string }) => {
    window.dispatchEvent(
      new CustomEvent("open-flyout", {
        detail: { type: "topic", id: String(item.id), slug: item.slug },
      })
    );
  };

  const displayItems = items.length > 0 
    ? items 
    : [
        { id: "static-1", title: "Synthesizing latest intelligence..." },
        { id: "static-2", title: "Awaiting data pipeline ingestion..." }
      ];

  return (
    <div className="ticker">
      <div className="ticker-label">LIVE UPDATES</div>
      <div className="ticker-track">
        {[...displayItems, ...displayItems].map((item, idx) => (
          <span 
            key={`${item.id}-${idx}`} 
            onClick={() => item.id.toString().startsWith("static") ? null : handleTopicClick(item as any)}
            style={{ cursor: item.id.toString().startsWith("static") ? "default" : "pointer" }}
          >
            {item.title}
          </span>
        ))}
      </div>
    </div>
  );
}

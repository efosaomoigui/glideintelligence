"use client";

import React from "react";
import Link from "next/link";

interface KeyTopicItem {
  title: string;
  slug: string;
  views: string;
  timeAgo: string;
}

interface KeyTopicsProps {
  title: string;
  topics: KeyTopicItem[];
}

export default function KeyTopics({ title, topics: initialTopics }: KeyTopicsProps) {
  const [topics, setTopics] = React.useState(initialTopics);

  React.useEffect(() => {
    setTopics(initialTopics);
  }, [initialTopics]);

  React.useEffect(() => {
    const handler = (e: Event) => {
      const { topicId, viewCount } = (e as CustomEvent).detail || {};
      if (!topicId) return;
      
      setTopics(prev => prev.map(t => {
        if (t.slug === String(topicId) || t.title === String(topicId)) {
          // Attempt to format raw view count or append K/M
          let newViews = t.views;
          if (viewCount !== undefined) {
             const n = typeof viewCount === 'number' ? viewCount : parseInt(String(viewCount), 10) || 0;
             if (n >= 1000000) newViews = (n / 1000000).toFixed(1).replace(/\.0$/, "") + "M";
             else if (n >= 1000) newViews = (n / 1000).toFixed(1).replace(/\.0$/, "") + "K";
             else newViews = String(n);
          }
          return { ...t, views: newViews };
        }
        return t;
      }));
    };
    window.addEventListener("topic-viewed", handler);
    return () => window.removeEventListener("topic-viewed", handler);
  }, []);
  return (
    <div className="sidebar-card">
      <div className="sidebar-title">{title}</div>
      <div className="key-topics-list">
        {topics.map((topic, i) => {
          return (
          <a key={i} href="#" onClick={(e) => {
            e.preventDefault();
            window.dispatchEvent(new CustomEvent("open-flyout", {
              detail: { id: topic.slug, slug: topic.slug } // Backend/Flyout logic will handle matching slug as id
            }));
          }} className="key-topic open-detail" data-id={topic.slug}>
            <div className="key-topic-title">{topic.title}</div>
            <div className="key-topic-meta">
              <span>{topic.views}</span>
              <span>•</span>
              <span>{topic.timeAgo}</span>
            </div>
          </a>
          );
        })}
      </div>
    </div>
  );
}

"use client";

import React from "react";
import Link from "next/link";

const CATEGORIES = [
  "All Topics",
  "Economy",
  "Politics",
  "Business",
  "Security",
  "Technology",
  "Sports",
  "Regional",
  "Global Impact"
];

interface TopicNavbarProps {
  activeCategory?: string;
}

export default function TopicNavbar({ activeCategory = "All Topics" }: TopicNavbarProps) {
  return (
    <nav className="bg-white border-b border-rule sticky top-[80px] z-[90] h-[56px] flex items-center">
      <div className="outer-container flex h-full">
        <ul className="flex gap-10 items-center h-full">
          {CATEGORIES.map((cat) => {
            const isActive = activeCategory.toLowerCase() === cat.toLowerCase();
            return (
              <li key={cat} className="h-full">
                <Link
                  href={cat === "All Topics" ? "/" : cat === "Sports" ? "/sport" : `/${cat.toLowerCase()}`}
                  className={`h-full flex items-center text-[0.88rem] transition-all relative whitespace-nowrap tracking-tight group ${
                    isActive ? "text-ink font-extrabold" : "text-ink-muted/80 hover:text-ink font-bold"
                  }`}
                >
                  {cat}
                  <div className={`absolute bottom-0 left-0 right-0 h-1 transition-all ${
                    isActive ? "bg-accent shadow-[0_-1px_4px_rgba(185,28,28,0.2)]" : "bg-accent/0 group-hover:bg-accent/30"
                  }`} />
                  {isActive && (
                    <div className="absolute top-0 left-0 right-0 h-[2px] bg-white z-[100]" />
                  )}
                </Link>
              </li>
            );
          })}
        </ul>
      </div>
    </nav>
  );
}

"use client";

import React, { useState } from "react";
import Link from "next/link";
import MobileDrawer from "./MobileDrawer";

interface MobileHeaderProps {
  activeCategory?: string;
}

export default function MobileHeader({ activeCategory }: MobileHeaderProps) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);

  return (
    <>
      <header className="mobile-header">
        <div className="mobile-header-inner">
          {/* Left: Hamburger */}
          <button
            className="mobile-icon-btn"
            onClick={() => setDrawerOpen(true)}
            aria-label="Open navigation menu"
          >
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
              <line x1="3" y1="6" x2="21" y2="6" />
              <line x1="3" y1="12" x2="21" y2="12" />
              <line x1="3" y1="18" x2="21" y2="18" />
            </svg>
          </button>

          {/* Center: Logo */}
          <Link href="/" className="mobile-logo" style={{ textDecoration: "none", fontFamily: '"Playfair Display", Georgia, serif', fontStyle: 'italic', fontWeight: 800 }}>
            <span style={{ color: "#000" }}>PA</span><span style={{ color: "#c0392b" }}>PERLY.</span>
          </Link>

          {/* Right: Actions */}
          <div className="mobile-header-actions">
            <button
              className="mobile-icon-btn"
              onClick={() => setSearchOpen(!searchOpen)}
              aria-label="Search"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8" />
                <path d="M21 21l-4.35-4.35" />
              </svg>
            </button>
            <button className="mobile-icon-btn" aria-label="Profile">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                <circle cx="12" cy="7" r="4" />
              </svg>
            </button>
          </div>
        </div>

        {/* Expandable Search Bar */}
        <div className={`mobile-search-bar${searchOpen ? " open" : ""}`}>
          <div className="mobile-search-inner">
            <svg className="mobile-search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8" />
              <path d="M21 21l-4.35-4.35" />
            </svg>
            <input
              type="text"
              placeholder="Search topics, sources, keywords..."
              autoFocus={searchOpen}
            />
          </div>
        </div>
      </header>

      <MobileDrawer
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        activeCategory={activeCategory}
      />
    </>
  );
}

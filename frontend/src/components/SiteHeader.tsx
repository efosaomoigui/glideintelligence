"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

export default function SiteHeader() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <header className="site-header">
      <div className="header-top">
        <div>
          <Link href="/" className="logo" style={{ textDecoration: 'none', fontFamily: '"Playfair Display", Georgia, serif', fontStyle: 'italic', fontWeight: 800 }}>
            <span style={{ color: "#000" }}>PA</span><span style={{ color: "#c0392b" }}>PERLY.</span>
          </Link>
          <div className="tagline">Making Sense of the News</div>
        </div>

        <button className="search-bar" onClick={() => window.dispatchEvent(new CustomEvent("open-flyout", { detail: { type: "search" } }))} style={{ textAlign: "left", cursor: "pointer" }}>
          <svg className="search-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            placeholder="Search topics, sources, or keywords..."
            readOnly
            style={{ cursor: "pointer", pointerEvents: "none" }}
          />
        </button>

        <div className="header-actions">
          {user ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--ink)' }}>
                {user.full_name || user.username}
              </span>
              <button className="btn btn-ghost" onClick={logout}>Logout</button>
            </div>
          ) : (
            <>
              <button className="btn btn-ghost" onClick={() => window.dispatchEvent(new CustomEvent("open-flyout", { detail: { type: "login" } }))}>Sign In</button>
              <button className="btn btn-primary" onClick={() => window.dispatchEvent(new CustomEvent("open-flyout", { detail: { type: "subscribe" } }))}>Subscribe</button>
            </>
          )}
        </div>
      </div>

      <nav className="main-nav">
        <div className="nav-inner">
          <Link href="/" className={`nav-link ${pathname === "/" ? "active" : ""}`}>All Stories</Link>
          <Link href="/economy" className={`nav-link ${pathname === "/economy" ? "active" : ""}`}>Economy</Link>
          <Link href="/politics" className={`nav-link ${pathname === "/politics" ? "active" : ""}`}>Politics</Link>
          <Link href="/business" className={`nav-link ${pathname === "/business" ? "active" : ""}`}>Business</Link>
          <Link href="/security" className={`nav-link ${pathname === "/security" ? "active" : ""}`}>Security</Link>
          <Link href="/technology" className={`nav-link ${pathname === "/technology" ? "active" : ""}`}>Technology</Link>
          <Link href="/sport" className={`nav-link ${pathname === "/sport" ? "active" : ""}`}>Sport</Link>
          <Link href="/regional" className={`nav-link ${pathname === "/regional" ? "active" : ""}`}>Regional</Link>
          <Link href="/global-impact" className={`nav-link ${pathname === "/global-impact" ? "active" : ""}`}>Global Impact</Link>
        </div>
      </nav>
    </header>
  );
}

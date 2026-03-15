"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

interface MobileDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  activeCategory?: string;
}

const NAV_ITEMS = [
  { href: "/", label: "All Topics", icon: "⬡" },
  { href: "/economy", label: "Economy", icon: "📈" },
  { href: "/politics", label: "Politics", icon: "🏛️" },
  { href: "/business", label: "Business", icon: "💼" },
  { href: "/security", label: "Security", icon: "🛡️" },
  { href: "/technology", label: "Technology", icon: "💡" },
  { href: "/regional", label: "Regional", icon: "🌍" },
  { href: "/global-impact", label: "Global Impact", icon: "🌐" },
];

export default function MobileDrawer({ isOpen, onClose, activeCategory }: MobileDrawerProps) {
  const pathname = usePathname();

  // Lock scroll when drawer is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  // Close on Escape
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) onClose();
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [isOpen, onClose]);

  return (
    <>
      {/* Backdrop */}
      <div
        className={`drawer-backdrop${isOpen ? " open" : ""}`}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer Panel */}
      <div className={`mobile-drawer${isOpen ? " open" : ""}`} role="dialog" aria-modal="true" aria-label="Navigation Menu">
        {/* Drawer Header */}
        <div className="drawer-header">
          <span className="drawer-logo" style={{ fontFamily: '"Playfair Display", Georgia, serif', fontStyle: 'italic', fontWeight: 800 }}>
            <span style={{ color: "#000" }}>PA</span><span style={{ color: "#c0392b" }}>PERLY.</span>
          </span>
          <button className="drawer-close-btn" onClick={onClose} aria-label="Close menu">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <div className="drawer-divider" />

        {/* Navigation Label */}
        <div className="drawer-section-label">Intelligence Verticals</div>

        {/* Nav Items */}
        <nav className="drawer-nav">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href || activeCategory === item.label;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`drawer-nav-item${isActive ? " active" : ""}`}
                onClick={onClose}
              >
                <span className="drawer-nav-icon">{item.icon}</span>
                <span className="drawer-nav-label">{item.label}</span>
                {isActive && (
                  <svg className="drawer-nav-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="9 18 15 12 9 6" />
                  </svg>
                )}
              </Link>
            );
          })}
        </nav>

        <div className="drawer-divider" style={{ marginTop: "auto" }} />

        {/* Footer Actions */}
        <div className="drawer-footer">
          <button className="drawer-footer-btn" onClick={() => window.dispatchEvent(new CustomEvent("open-flyout", { detail: { type: "login" } }))}>Sign In</button>
          <button className="drawer-footer-btn primary" onClick={() => window.dispatchEvent(new CustomEvent("open-flyout", { detail: { type: "subscribe" } }))}>Subscribe</button>
        </div>
      </div>
    </>
  );
}

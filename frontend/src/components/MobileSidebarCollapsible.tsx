"use client";

import React, { useState } from "react";

interface MobileSidebarCollapsibleProps {
  title: string;
  icon?: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
  accent?: boolean;
}

export default function MobileSidebarCollapsible({
  title,
  icon,
  defaultOpen = false,
  children,
  accent = false,
}: MobileSidebarCollapsibleProps) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className={`mobile-collapsible${accent ? " accent-bg" : ""}`}>
      <button
        className="mobile-collapsible-trigger"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
      >
        <span className="mobile-collapsible-title">
          {icon && <span className="collapsible-icon">{icon}</span>}
          {title}
        </span>
        <svg
          className={`collapsible-chevron${open ? " rotated" : ""}`}
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>
      <div className={`mobile-collapsible-body${open ? " open" : ""}`}>
        <div className="mobile-collapsible-content">{children}</div>
      </div>
    </div>
  );
}

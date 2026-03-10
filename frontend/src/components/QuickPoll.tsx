"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";

interface QuickPollProps {
  poll?: any;
  userVotedOptionId?: number | null;
  onVoteSuccess?: () => void;
}

export default function QuickPoll({ poll: initialPoll, userVotedOptionId, onVoteSuccess }: QuickPollProps = {}) {
  const { user: currentUser } = useAuth();
  const [poll, setPoll] = useState<any>(initialPoll);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [hasVoted, setHasVoted] = useState(false);

  useEffect(() => {
    // If we're passed an explicit poll (or null for "awaiting" or "none"), 
    // we don't fetch the global fallback poll.
    if (initialPoll !== undefined) {
       setPoll(initialPoll);
       
       if (initialPoll && currentUser) {
          if (userVotedOptionId !== undefined && userVotedOptionId !== null) {
              setSelectedId(userVotedOptionId);
              setHasVoted(true);
          } else if (initialPoll.votes) {
              const vote = initialPoll.votes.find((v:any) => v.user_id === currentUser.id);
              if (vote) {
                  setSelectedId(vote.poll_option_id);
                  setHasVoted(true);
              } else {
                  setSelectedId(null);
                  setHasVoted(false);
              }
          } else {
              setSelectedId(null);
              setHasVoted(false);
          }
       }
       return;
    }

    // Default: Fetch the latest platform-wide poll
    fetch("/api/interactions/polls")
      .then(res => res.json())
      .then(data => {
        if (data && data.length > 0) {
          const current = data[0];
          setPoll(current);
          if (currentUser && current.votes) {
             const vote = current.votes.find((v:any) => v.user_id === currentUser.id);
             if (vote) {
                 setSelectedId(vote.poll_option_id);
                 setHasVoted(true);
             }
          }
        }
      })
      .catch((e) => console.error(e));
  }, [currentUser, initialPoll]);

  const handleVote = async (optionId: number) => {
      if (hasVoted || selectedId !== null) return;
      if (!currentUser) {
          window.dispatchEvent(new CustomEvent("open-flyout", { detail: { type: "login" } }));
          return;
      }
      setSelectedId(optionId);
      setHasVoted(true);

      const update = { ...poll };
      update.total_votes += 1;
      update.options = update.options.map((o: any) => 
          o.id === optionId ? { ...o, vote_count: o.vote_count + 1 } : o
      );
      setPoll(update);

      try {
        await fetch(`/api/interactions/polls/${poll.id}/vote`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ poll_option_id: optionId })
        });
        if (onVoteSuccess) onVoteSuccess();
      } catch (e) {
          setHasVoted(false);
          setSelectedId(null);
      }
  };

  if (poll === null || initialPoll === null) {
      return (
        <div>
          <div className="sidebar-title-flyout" style={{ marginBottom: "12px" }}>Quick Poll</div>
          <div className="poll-title" style={{color: "rgba(255,255,255,0.4)", fontSize: "0.9rem", border: "1px solid rgba(255,255,255,0.05)", padding: "16px", borderRadius: "8px", background: "rgba(255,255,255,0.02)"}}>
            Intelligence synthesis in progress. Community perspectives will be available shortly.
          </div>
        </div>
      );
  }

  if (poll === undefined) {
      return (
        <div>
          <div className="sidebar-title-flyout" style={{ marginBottom: "12px" }}>Quick Poll</div>
          <div className="poll-title" style={{color: "#fff", border: "1px solid rgba(255,255,255,0.1)", padding: "16px", borderRadius: "8px", background: "rgba(255,255,255,0.03)"}}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <div className="animate-pulse w-2 h-2 rounded-full bg-accent" />
              <span>Fetching contextual intelligence...</span>
            </div>
          </div>
        </div>
      );
  }

  return (
    <div>
      <div className="sidebar-title-flyout" style={{ marginBottom: "12px" }}>Quick Poll</div>
      <div className="poll-question-flyout" style={{lineHeight: 1.4, fontSize: "1.08rem", fontWeight: 600, color: "#fff", marginBottom: "20px", fontFamily: "var(--serif)"}}>{poll.question}</div>
      <div className="poll-options" style={{display: "flex", flexDirection: "column", gap: "10px"}}>
        {poll.options.map((option: any) => {
          const votesForOpt = option.vote_count || 0;
          const totalVotes = poll.total_votes || 0;
          const percent = totalVotes > 0 ? Math.round((votesForOpt / totalVotes) * 100) : 0;
          const isVoted = selectedId === option.id;

          return (
              <div 
                key={option.id} 
                className="poll-option-flyout"
                onClick={() => !hasVoted && handleVote(option.id)}
                style={{ 
                    padding: "14px 16px", 
                    background: isVoted ? "#2c3e50cc" : "rgba(255,255,255,0.03)", 
                    border: isVoted ? "1px solid var(--accent)" : "1px solid rgba(255,255,255,0.08)",
                    borderRadius: "8px",
                    cursor: hasVoted ? "default" : "pointer",
                    position: "relative",
                    overflow: "hidden",
                    transition: "all 0.2s ease"
                }}
            >
                {hasVoted && (
                    <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: `${percent}%`, background: isVoted ? "rgba(255,255,255,0.1)" : "rgba(255,255,255,0.05)", zIndex: 0, transition: "width 0.8s cubic-bezier(0.4, 0, 0.2, 1)" }} />
                )}
                
                <div style={{ position: "relative", zIndex: 1, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                    {!hasVoted && (
                    <div style={{ width: "16px", height: "16px", borderRadius: "50%", border: "1px solid rgba(255,255,255,0.2)" }} />
                    )}
                    <span style={{ fontSize: "0.95rem", color: "#fff", fontWeight: 500 }}>{option.option_text}</span>
                </div>
                {hasVoted && <span style={{ fontSize: "0.9rem", fontWeight: 700, color: "#fff" }}>{percent}%</span>}
                </div>
            </div>
          )
        })}
      </div>
      {hasVoted && (
        <div style={{ marginTop: "16px", fontSize: "0.75rem", color: "rgba(255,255,255,0.4)", textAlign: "right", letterSpacing: "0.02em" }}>
          {poll.total_votes?.toLocaleString()} responses collected
        </div>
      )}
    </div>
  );
}

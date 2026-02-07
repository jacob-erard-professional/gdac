import React from "react";

export default function EmptyState({ title, detail }) {
  return (
    <div className="empty-state">
      <div>
        <h4>{title}</h4>
        <p>{detail}</p>
      </div>
    </div>
  );
}

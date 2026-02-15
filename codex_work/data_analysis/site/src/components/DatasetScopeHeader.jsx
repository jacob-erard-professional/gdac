import React from "react";

export default function DatasetScopeHeader({ year }) {
  return (
    <div className="scope-header">
      <div className="scope-pill">regular: outputs/analytics/{year}</div>
      <div className="scope-pill">full: outputs/analytics/{year}_full</div>
    </div>
  );
}

import React from "react";

export default function YearSelector({ years, value, onChange, disabled }) {
  return (
    <label className="year-selector">
      <span>Analysis Year</span>
      <select value={value || ""} onChange={(e) => onChange(e.target.value)} disabled={disabled}>
        {!value && <option value="">Select year</option>}
        {years.map((year) => (
          <option key={year} value={year}>
            {year}
          </option>
        ))}
      </select>
    </label>
  );
}

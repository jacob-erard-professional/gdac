import React from "react";

export default function YearSelector({ year, years, onChange }) {
  return (
    <div className="year-selector">
      <label htmlFor="year-input">Year</label>
      <input
        id="year-input"
        type="text"
        value={year}
        onChange={(event) => onChange(event.target.value)}
        placeholder="2024"
      />
      {years.length > 0 ? (
        <div className="year-buttons">
          {years.map((item) => (
            <button
              key={item}
              type="button"
              className={item === year ? "active" : ""}
              onClick={() => onChange(item)}
            >
              {item}
            </button>
          ))}
        </div>
      ) : (
        <p className="muted">No year index found. Type a year above.</p>
      )}
    </div>
  );
}

import React, { useEffect, useRef } from "react";
import * as echarts from "echarts";
import "echarts-wordcloud";

export default function ChartCard({ title, subtitle, option }) {
  const chartRef = useRef(null);

  useEffect(() => {
    if (!chartRef.current || !option) return undefined;
    const chart = echarts.init(chartRef.current);
    chart.setOption(option);
    const handleResize = () => chart.resize();
    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
      chart.dispose();
    };
  }, [option]);

  const minWidth = 720;

  return (
    <section className="card chart-card">
      <div className="card-header">
        <div>
          <h3>{title}</h3>
          {subtitle ? <p className="muted">{subtitle}</p> : null}
        </div>
      </div>
      <div className="chart-scroll">
        <div className="chart" ref={chartRef} style={{ minWidth }} />
      </div>
    </section>
  );
}

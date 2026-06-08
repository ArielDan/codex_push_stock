import ReactECharts from "echarts-for-react";
import { CalendarRange, Layers3, TrendingDown, TrendingUp } from "lucide-react";
import type { YearlyReview } from "../types/portfolio";
import { buildThemeMatrix, formatCurrency, formatPct, getDominantTheme, getYearlyDelta, signedClass } from "../utils/portfolio";

type YearlyReviewPanelProps = {
  years: YearlyReview[];
};

const riskColor: Record<string, string> = {
  Medium: "#57a8c7",
  High: "#d7aa55",
  "Very High": "#d76767",
};

export function YearlyReviewPanel({ years }: YearlyReviewPanelProps) {
  const sortedYears = [...years].sort((a, b) => a.year - b.year);
  const themeMatrix = buildThemeMatrix(sortedYears);
  const option = {
    color: ["#d7aa55", "#57a8c7", "#4fb783"],
    grid: { left: 16, right: 28, top: 34, bottom: 24, containLabel: true },
    legend: {
      top: 0,
      right: 0,
      textStyle: { color: "#8fa1af" },
      itemWidth: 9,
      itemHeight: 9,
    },
    tooltip: {
      trigger: "axis",
      backgroundColor: "#101820",
      borderColor: "rgba(178,191,204,.18)",
      textStyle: { color: "#e9eef2" },
    },
    xAxis: {
      type: "category",
      data: sortedYears.map((year) => String(year.year)),
      axisLabel: { color: "#8fa1af" },
      axisTick: { show: false },
      axisLine: { lineStyle: { color: "rgba(178,191,204,.18)" } },
    },
    yAxis: [
      {
        type: "value",
        name: "NAV",
        axisLabel: { color: "#8fa1af", formatter: "${value}" },
        splitLine: { lineStyle: { color: "rgba(178,191,204,.1)" } },
      },
      {
        type: "value",
        name: "TWR",
        axisLabel: { color: "#8fa1af", formatter: "{value}%" },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: "期末 NAV",
        type: "line",
        smooth: true,
        symbolSize: 9,
        lineStyle: { width: 3 },
        data: sortedYears.map((year) => Number(year.ending_nav.toFixed(2))),
      },
      {
        name: "净入金",
        type: "bar",
        barWidth: 18,
        itemStyle: { borderRadius: [5, 5, 0, 0], color: "rgba(87,168,199,.72)" },
        data: sortedYears.map((year) => Number(year.net_deposits.toFixed(2))),
      },
      {
        name: "TWR",
        type: "bar",
        yAxisIndex: 1,
        barWidth: 18,
        itemStyle: {
          borderRadius: [5, 5, 0, 0],
          color: ({ value }: { value: number }) => (value >= 0 ? "#4fb783" : "#d76767"),
        },
        data: sortedYears.map((year) => Number(year.twr_pct.toFixed(2))),
      },
    ],
  };

  return (
    <section className="panel lg:col-span-12">
      <div className="mb-5 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="eyebrow">Annual Review</p>
          <h2 className="text-lg font-semibold tracking-wide text-text">年度复盘：2024 → 2025 → 2026</h2>
        </div>
        <div className="rounded border border-line bg-white/[0.03] px-3 py-1.5 text-xs text-muted">
          2026 为 5 月报表局部视图
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.1fr_1.9fr]">
        <div className="rounded-lg border border-line bg-white/[0.02] p-4">
          <p className="mb-3 text-xs uppercase tracking-[0.22em] text-muted">NAV / Deposit / TWR</p>
          <ReactECharts option={option} className="h-[310px]" />
        </div>

        <div className="grid gap-3 lg:grid-cols-3">
          {sortedYears.map((year, index) => {
            const previous = sortedYears[index - 1];
            const delta = getYearlyDelta(year, previous);
            const dominantTheme = getDominantTheme(year);
            const TrendIcon = year.twr_pct >= 0 ? TrendingUp : TrendingDown;
            return (
              <article key={year.year} className="rounded-lg border border-line bg-white/[0.025] p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-mono text-xs text-amber">{year.period}</p>
                    <h3 className="mt-1 text-2xl font-semibold text-text">{year.year}</h3>
                  </div>
                  <TrendIcon className={`h-5 w-5 ${signedClass(year.twr_pct)}`} />
                </div>
                <p className="mt-3 min-h-[40px] text-sm leading-5 text-muted">{year.review_note}</p>

                <div className="mt-4 grid gap-2 text-sm">
                  <Metric label="期末 NAV" value={formatCurrency(year.ending_nav)} />
                  <Metric label="TWR" value={formatPct(year.twr_pct)} valueClass={signedClass(year.twr_pct)} />
                  <Metric label="净入金" value={formatCurrency(year.net_deposits)} />
                  <Metric label="MTM P&L" value={formatCurrency(year.mark_to_market_pnl)} valueClass={signedClass(year.mark_to_market_pnl)} />
                  <Metric label="高风险暴露" value={formatPct(delta.highRiskWeightPct)} valueClass={delta.highRiskWeightPct > 70 ? "text-red" : "text-amber"} />
                  <Metric label="现金估算" value={formatPct(delta.cashWeightPct)} />
                </div>

                <div className="mt-4 rounded border border-line bg-ink/35 p-3">
                  <div className="flex items-center gap-2 text-xs text-muted">
                    <Layers3 className="h-3.5 w-3.5 text-cyan" />
                    主导主题
                  </div>
                  <p className="mt-1 text-sm font-semibold text-text">{dominantTheme?.theme || "N/A"}</p>
                  {dominantTheme ? <p className="mt-1 font-mono text-xs text-muted">{formatPct(dominantTheme.weight_pct)} of NAV</p> : null}
                </div>

                <div className="mt-3 flex items-center gap-2 text-xs text-muted">
                  <CalendarRange className="h-3.5 w-3.5" />
                  {year.coverage}
                </div>
              </article>
            );
          })}
        </div>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-[1.3fr_.7fr]">
        <div className="rounded-lg border border-line bg-white/[0.02] p-4">
          <p className="mb-3 text-xs uppercase tracking-[0.22em] text-muted">Theme Migration</p>
          <div className="overflow-x-auto">
            <div className="min-w-[720px]">
              <div className="grid grid-cols-[220px_repeat(3,1fr)] border-b border-line pb-2 text-xs uppercase tracking-[0.14em] text-muted">
                <span>主题</span>
                {sortedYears.map((year) => (
                  <span key={year.year}>{year.year}</span>
                ))}
              </div>
              {themeMatrix.slice(0, 10).map((row) => (
                <div key={row.theme} className="grid grid-cols-[220px_repeat(3,1fr)] items-center gap-3 border-b border-line/70 py-2 text-sm">
                  <span className="truncate pr-4 text-muted">{row.theme}</span>
                  {row.values.map((value, index) => (
                    <div key={`${row.theme}-${sortedYears[index].year}`} className="flex items-center gap-2">
                      <div className="h-2 flex-1 rounded-full bg-white/10">
                        <div className="h-full rounded-full bg-cyan" style={{ width: `${Math.min(value * 2.4, 100)}%` }} />
                      </div>
                      <span className="w-12 text-right font-mono text-xs text-text">{formatPct(value)}</span>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="rounded-lg border border-line bg-white/[0.02] p-4">
          <p className="mb-3 text-xs uppercase tracking-[0.22em] text-muted">Risk Mix</p>
          <div className="space-y-4">
            {sortedYears.map((year) => (
              <div key={year.year}>
                <div className="mb-2 flex items-center justify-between text-sm">
                  <span className="font-semibold text-text">{year.year}</span>
                  <span className="font-mono text-xs text-muted">{year.position_count} positions</span>
                </div>
                <div className="flex h-3 overflow-hidden rounded-full bg-white/10">
                  {year.risk_exposure.map((risk) => (
                    <div
                      key={`${year.year}-${risk.risk_level}`}
                      title={`${risk.risk_level}: ${formatPct(risk.weight_pct)}`}
                      style={{ width: `${risk.weight_pct}%`, background: riskColor[risk.risk_level] || "#7b8fa0" }}
                    />
                  ))}
                </div>
                <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-muted">
                  {year.risk_exposure.map((risk) => (
                    <span key={`${year.year}-label-${risk.risk_level}`}>
                      {risk.risk_level} {formatPct(risk.weight_pct)}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function Metric({ label, value, valueClass = "text-text" }: { label: string; value: string; valueClass?: string }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-line/70 pb-2">
      <span className="text-muted">{label}</span>
      <span className={`font-mono ${valueClass}`}>{value}</span>
    </div>
  );
}

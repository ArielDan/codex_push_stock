import { ArrowDownRight, ArrowUpRight } from "lucide-react";
import type { Position } from "../types/portfolio";
import { formatCurrency, formatNumber, formatPct, signedClass } from "../utils/portfolio";

type PositionsTableProps = {
  positions: Position[];
};

const riskClass: Record<string, string> = {
  Low: "border-green/25 bg-green/10 text-green",
  Medium: "border-cyan/25 bg-cyan/10 text-cyan",
  High: "border-amber/25 bg-amber/10 text-amber",
  "Very High": "border-red/30 bg-red/10 text-red",
};

export function PositionsTable({ positions }: PositionsTableProps) {
  return (
    <section className="panel lg:col-span-12">
      <div className="mb-5 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="eyebrow">Open Positions</p>
          <h2 className="text-lg font-semibold tracking-wide text-text">持仓明细</h2>
        </div>
        <p className="text-xs text-muted">{positions.length} 个标的，按市值降序排列</p>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-[1080px] w-full border-collapse">
          <thead>
            <tr className="border-y border-line text-left text-[11px] uppercase tracking-[0.16em] text-muted">
              <th className="py-3 pr-4">Symbol</th>
              <th className="px-4">数量</th>
              <th className="px-4">成本价</th>
              <th className="px-4">当前价</th>
              <th className="px-4">市值</th>
              <th className="px-4">仓位</th>
              <th className="px-4">浮盈亏</th>
              <th className="px-4">盈亏率</th>
              <th className="px-4">主题</th>
              <th className="pl-4">风险</th>
            </tr>
          </thead>
          <tbody>
            {positions.map((position) => {
              const isGain = position.unrealized_pnl >= 0;
              const TrendIcon = isGain ? ArrowUpRight : ArrowDownRight;
              return (
                <tr key={`${position.account_id}-${position.symbol}`} className="table-row border-b border-line/80 text-sm">
                  <td className="py-3 pr-4">
                    <div className="font-mono text-base font-semibold text-text">{position.symbol}</div>
                    <div className="text-xs text-muted">
                      {position.asset_class} · {position.currency}
                    </div>
                  </td>
                  <td className="px-4 font-mono text-text">{formatNumber(position.quantity)}</td>
                  <td className="px-4 font-mono text-muted">{formatNumber(position.cost_price)}</td>
                  <td className="px-4 font-mono text-text">{formatNumber(position.current_price)}</td>
                  <td className="px-4 font-mono text-text">{formatCurrency(position.market_value)}</td>
                  <td className="px-4">
                    <div className="flex min-w-[90px] items-center gap-2">
                      <div className="h-1.5 flex-1 rounded-full bg-white/10">
                        <div
                          className="h-full rounded-full bg-amber"
                          style={{ width: `${Math.min(position.weight_pct * 4, 100)}%` }}
                        />
                      </div>
                      <span className="font-mono text-xs text-muted">{formatPct(position.weight_pct)}</span>
                    </div>
                  </td>
                  <td className={`px-4 font-mono ${signedClass(position.unrealized_pnl)}`}>
                    <span className="inline-flex items-center gap-1">
                      <TrendIcon className="h-3.5 w-3.5" />
                      {formatCurrency(position.unrealized_pnl)}
                    </span>
                  </td>
                  <td className={`px-4 font-mono ${signedClass(position.unrealized_pnl_pct)}`}>
                    {formatPct(position.unrealized_pnl_pct)}
                  </td>
                  <td className="max-w-[190px] px-4 text-muted">
                    <span className="line-clamp-2">{position.theme}</span>
                  </td>
                  <td className="pl-4">
                    <span
                      className={`whitespace-nowrap rounded border px-2 py-1 text-xs ${
                        riskClass[position.risk_level] || "border-line bg-white/[0.03] text-muted"
                      }`}
                    >
                      {position.risk_level}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}

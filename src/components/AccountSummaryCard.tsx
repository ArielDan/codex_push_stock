import { Activity, Banknote, CircleDollarSign, Gauge, Landmark, LineChart, WalletCards } from "lucide-react";
import type { AccountSummary, RiskAlert } from "../types/portfolio";
import { formatCurrency, formatPct, getPortfolioPulse, signedClass } from "../utils/portfolio";

type AccountSummaryCardProps = {
  account: AccountSummary;
  alerts: RiskAlert[];
};

export function AccountSummaryCard({ account, alerts }: AccountSummaryCardProps) {
  const pulse = getPortfolioPulse(account, alerts);
  const metrics = [
    { label: "现金", value: formatCurrency(account.cash), icon: Banknote },
    { label: "持仓市值", value: formatCurrency(account.position_market_value), icon: LineChart },
    { label: "可用资金", value: formatCurrency(account.available_funds), icon: WalletCards },
    { label: "保证金占用", value: formatCurrency(account.margin_used), icon: Landmark },
    { label: "现金比例", value: formatPct(pulse.cashWeight), icon: Gauge },
    { label: "保证金 / NAV", value: formatPct(pulse.marginWeight), icon: Activity },
  ];

  return (
    <section className="panel relative overflow-hidden lg:col-span-12">
      <div className="absolute right-0 top-0 h-full w-1/2 bg-[radial-gradient(circle_at_top_right,rgba(215,170,85,0.16),transparent_48%)]" />
      <div className="relative grid gap-7 lg:grid-cols-[1.15fr_1.85fr]">
        <div className="min-w-0">
          <p className="eyebrow">IBKR Portfolio / {account.as_of}</p>
          <div className="mt-3 flex items-end gap-3">
            <CircleDollarSign className="mb-2 h-8 w-8 text-amber" />
            <div>
              <p className="text-sm text-muted">总资产</p>
              <h1 className="font-display text-4xl font-semibold tracking-normal text-text md:text-5xl">
                {formatCurrency(account.total_assets)}
              </h1>
            </div>
          </div>
          <div className="mt-5 flex flex-wrap items-center gap-3 text-sm">
            <span className="rounded border border-line bg-white/[0.03] px-3 py-1.5 text-muted">Base {account.base_currency}</span>
            <span className="rounded border border-amber/25 bg-amber/10 px-3 py-1.5 text-amber">风险状态：{pulse.riskLabel}</span>
            {typeof account.period_twr_pct === "number" ? (
              <span className="rounded border border-green/25 bg-green/10 px-3 py-1.5 text-green">
                5月 TWR 均值 {formatPct(account.period_twr_pct)}
              </span>
            ) : null}
          </div>
          {account.source_note ? <p className="mt-5 max-w-xl text-xs leading-5 text-muted">{account.source_note}</p> : null}
        </div>

        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          <div className="summary-tile sm:col-span-2 xl:col-span-3">
            <div>
              <p className="text-xs uppercase tracking-[0.24em] text-muted">总浮盈亏</p>
              <p className={`mt-2 text-3xl font-semibold ${signedClass(account.total_unrealized_pnl)}`}>
                {formatCurrency(account.total_unrealized_pnl)}
              </p>
            </div>
            <div className="h-12 w-px bg-line" />
            <div>
              <p className="text-xs uppercase tracking-[0.24em] text-muted">风险提醒</p>
              <p className="mt-2 text-3xl font-semibold text-text">{alerts.length}</p>
            </div>
          </div>
          {metrics.map(({ label, value, icon: Icon }) => (
            <div className="summary-tile" key={label}>
              <Icon className="h-4 w-4 text-cyan" />
              <div>
                <p className="text-xs text-muted">{label}</p>
                <p className="mt-1 font-mono text-base text-text">{value}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

import { AlertTriangle, CheckCircle2, ShieldAlert } from "lucide-react";
import type { RiskAlert } from "../types/portfolio";
import { riskRules } from "../utils/portfolio";

type RiskAlertPanelProps = {
  alerts: RiskAlert[];
};

const severityClass = {
  danger: "border-red/25 bg-red/10 text-red",
  warning: "border-amber/25 bg-amber/10 text-amber",
  info: "border-cyan/25 bg-cyan/10 text-cyan",
};

export function RiskAlertPanel({ alerts }: RiskAlertPanelProps) {
  return (
    <section className="panel lg:col-span-12">
      <div className="mb-5 flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p className="eyebrow">Risk Watch</p>
          <h2 className="text-lg font-semibold tracking-wide text-text">风险提醒</h2>
        </div>
        <div className="grid gap-2 text-xs text-muted sm:grid-cols-2 lg:grid-cols-5">
          <span className="rule-chip">单票 &gt; {riskRules.maxSinglePositionWeightPct}%</span>
          <span className="rule-chip">亏损 &lt; {riskRules.maxSinglePositionLossPct}%</span>
          <span className="rule-chip">高风险 &gt; {riskRules.maxHighRiskWeightPct}%</span>
          <span className="rule-chip">现金 &lt; {riskRules.minCashWeightPct}%</span>
          <span className="rule-chip">主题 &gt; {riskRules.maxThemeWeightPct}%</span>
        </div>
      </div>

      {alerts.length === 0 ? (
        <div className="flex items-center gap-3 rounded border border-green/20 bg-green/10 p-4 text-green">
          <CheckCircle2 className="h-5 w-5" />
          <p className="text-sm">当前没有触发配置中的风险规则。</p>
        </div>
      ) : (
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {alerts.map((alert) => (
            <article key={alert.id} className={`rounded border p-4 ${severityClass[alert.severity]}`}>
              <div className="flex items-start gap-3">
                {alert.severity === "danger" ? (
                  <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0" />
                ) : (
                  <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0" />
                )}
                <div>
                  <h3 className="font-semibold text-text">{alert.title}</h3>
                  <p className="mt-1 text-sm leading-5 text-muted">{alert.detail}</p>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

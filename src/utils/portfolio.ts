import type { AccountSummary, Position, RiskAlert, ThemeExposure, YearlyReview } from "../types/portfolio";

export const riskRules = {
  maxSinglePositionWeightPct: 10,
  maxSinglePositionLossPct: -20,
  maxHighRiskWeightPct: 20,
  minCashWeightPct: 10,
  maxThemeWeightPct: 35,
  highRiskLevels: ["High", "Very High"],
};

export const formatCurrency = (value: number, currency = "USD") =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: Math.abs(value) >= 1000 ? 0 : 2,
  }).format(value);

export const formatNumber = (value: number) =>
  new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(value);

export const formatPct = (value: number, digits = 1) =>
  `${value >= 0 ? "" : "-"}${Math.abs(value).toFixed(digits)}%`;

export const signedClass = (value: number) =>
  value > 0 ? "text-green" : value < 0 ? "text-red" : "text-muted";

export function normalizePositions(positions: Position[], totalAssets: number): Position[] {
  return [...positions]
    .map((position) => ({
      ...position,
      weight_pct: position.weight_pct || (totalAssets ? (position.market_value / totalAssets) * 100 : 0),
      unrealized_pnl_pct:
        position.unrealized_pnl_pct ||
        (position.cost_basis ? (position.unrealized_pnl / position.cost_basis) * 100 : 0),
    }))
    .sort((a, b) => b.market_value - a.market_value);
}

export function calculateThemeExposure(positions: Position[], totalAssets: number): ThemeExposure[] {
  const exposure = positions.reduce<Record<string, number>>((acc, position) => {
    acc[position.theme] = (acc[position.theme] || 0) + position.market_value;
    return acc;
  }, {});

  return Object.entries(exposure)
    .map(([theme, market_value]) => ({
      theme,
      market_value,
      weight_pct: totalAssets ? (market_value / totalAssets) * 100 : 0,
    }))
    .sort((a, b) => b.market_value - a.market_value);
}

export function calculateRiskAlerts(
  account: AccountSummary,
  positions: Position[],
  themeExposure: ThemeExposure[],
  rules = riskRules,
): RiskAlert[] {
  const alerts: RiskAlert[] = [];
  const cashWeight = account.total_assets ? (account.cash / account.total_assets) * 100 : 0;
  const highRiskValue = positions
    .filter((position) => rules.highRiskLevels.includes(position.risk_level))
    .reduce((sum, position) => sum + position.market_value, 0);
  const highRiskWeight = account.total_assets ? (highRiskValue / account.total_assets) * 100 : 0;

  positions.forEach((position) => {
    if (position.weight_pct > rules.maxSinglePositionWeightPct) {
      alerts.push({
        id: `single-weight-${position.symbol}`,
        title: `${position.symbol} 单票仓位偏高`,
        detail: `当前占总资产 ${formatPct(position.weight_pct)}，高于 ${rules.maxSinglePositionWeightPct}% 阈值。`,
        severity: "warning",
        metric: position.weight_pct,
      });
    }

    if (position.unrealized_pnl_pct < rules.maxSinglePositionLossPct) {
      alerts.push({
        id: `single-loss-${position.symbol}`,
        title: `${position.symbol} 浮亏超过阈值`,
        detail: `浮亏率 ${formatPct(position.unrealized_pnl_pct)}，低于 ${rules.maxSinglePositionLossPct}% 风控线。`,
        severity: "danger",
        metric: position.unrealized_pnl_pct,
      });
    }
  });

  if (highRiskWeight > rules.maxHighRiskWeightPct) {
    alerts.push({
      id: "high-risk-weight",
      title: "高风险资产仓位过高",
      detail: `High / Very High 合计 ${formatPct(highRiskWeight)}，高于 ${rules.maxHighRiskWeightPct}% 阈值。`,
      severity: "danger",
      metric: highRiskWeight,
    });
  }

  if (cashWeight < rules.minCashWeightPct) {
    alerts.push({
      id: "cash-low",
      title: "现金比例偏低",
      detail: `现金占比 ${formatPct(cashWeight)}，低于 ${rules.minCashWeightPct}% 安全垫。`,
      severity: "warning",
      metric: cashWeight,
    });
  }

  themeExposure.forEach((theme) => {
    if (theme.weight_pct > rules.maxThemeWeightPct) {
      alerts.push({
        id: `theme-${theme.theme}`,
        title: `${theme.theme} 主题拥挤`,
        detail: `主题占总资产 ${formatPct(theme.weight_pct)}，高于 ${rules.maxThemeWeightPct}% 阈值。`,
        severity: "warning",
        metric: theme.weight_pct,
      });
    }
  });

  return alerts.sort((a, b) => {
    const severityScore = { danger: 3, warning: 2, info: 1 };
    return severityScore[b.severity] - severityScore[a.severity] || Math.abs(b.metric) - Math.abs(a.metric);
  });
}

export function getPnlRanking(positions: Position[]) {
  const topGainers = [...positions].sort((a, b) => b.unrealized_pnl - a.unrealized_pnl).slice(0, 7);
  const topLosers = [...positions].sort((a, b) => a.unrealized_pnl - b.unrealized_pnl).slice(0, 7);
  return [...topLosers.reverse(), ...topGainers].filter(
    (position, index, array) => array.findIndex((item) => item.symbol === position.symbol) === index,
  );
}

export function getPortfolioPulse(account: AccountSummary, alerts: RiskAlert[]) {
  const cashWeight = account.total_assets ? (account.cash / account.total_assets) * 100 : 0;
  const marginWeight = account.total_assets ? (account.margin_used / account.total_assets) * 100 : 0;
  const dangerCount = alerts.filter((alert) => alert.severity === "danger").length;

  return {
    cashWeight,
    marginWeight,
    dangerCount,
    riskLabel: dangerCount > 4 ? "紧张" : dangerCount > 0 ? "需复盘" : "平衡",
  };
}

export function getYearlyDelta(current: YearlyReview, previous?: YearlyReview) {
  const navGrowthPct = current.beginning_nav
    ? ((current.ending_nav - current.beginning_nav - current.net_deposits) / current.beginning_nav) * 100
    : current.twr_pct;
  const navChangeFromPreviousPct = previous?.ending_nav
    ? ((current.ending_nav - previous.ending_nav) / previous.ending_nav) * 100
    : undefined;
  const cashWeightPct = current.ending_nav ? (current.cash_estimate / current.ending_nav) * 100 : 0;
  const investedWeightPct = current.ending_nav ? (current.position_market_value / current.ending_nav) * 100 : 0;
  const highRiskWeightPct = current.risk_exposure
    .filter((risk) => risk.risk_level === "High" || risk.risk_level === "Very High")
    .reduce((sum, risk) => sum + risk.weight_pct, 0);

  return {
    navGrowthPct,
    navChangeFromPreviousPct,
    cashWeightPct,
    investedWeightPct,
    highRiskWeightPct,
  };
}

export function getDominantTheme(year: YearlyReview) {
  return [...year.top_themes].sort((a, b) => b.market_value - a.market_value)[0];
}

export function buildThemeMatrix(years: YearlyReview[]) {
  const themes = Array.from(new Set(years.flatMap((year) => year.top_themes.slice(0, 4).map((theme) => theme.theme))));

  return themes.map((theme) => ({
    theme,
    values: years.map((year) => year.top_themes.find((item) => item.theme === theme)?.weight_pct || 0),
  }));
}

export type RiskLevel = "Low" | "Medium" | "High" | "Very High" | string;

export type AccountSummary = {
  as_of: string;
  base_currency: string;
  total_assets: number;
  cash: number;
  position_market_value: number;
  available_funds: number;
  margin_used: number;
  maintenance_margin: number;
  buying_power: number;
  total_unrealized_pnl: number;
  period_twr_pct?: number;
  source_note?: string;
};

export type Position = {
  symbol: string;
  account_id?: string;
  asset_class: string;
  currency: string;
  quantity: number;
  cost_price: number;
  current_price: number;
  cost_basis: number;
  market_value: number;
  weight_pct: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
  theme: string;
  risk_level: RiskLevel;
};

export type ThemeExposure = {
  theme: string;
  market_value: number;
  weight_pct: number;
};

export type YearlyReview = {
  year: number;
  period: string;
  coverage: string;
  beginning_nav: number;
  ending_nav: number;
  net_deposits: number;
  mark_to_market_pnl: number;
  dividends: number;
  interest: number;
  commissions: number;
  twr_pct: number;
  position_market_value: number;
  cash_estimate: number;
  position_count: number;
  top_themes: ThemeExposure[];
  risk_exposure: Array<{ risk_level: string; market_value: number; weight_pct: number }>;
  review_note: string;
};

export type RiskAlert = {
  id: string;
  title: string;
  detail: string;
  severity: "info" | "warning" | "danger";
  metric: number;
};

export type PortfolioData = {
  account_summary: AccountSummary;
  positions: Position[];
  theme_exposure: ThemeExposure[];
  risk_alerts: RiskAlert[];
  risk_exposure?: Array<{ risk_level: string; market_value: number; weight_pct: number }>;
  yearly_analysis?: YearlyReview[];
};

import rawData from "../data/positions.json";
import { AccountSummaryCard } from "./components/AccountSummaryCard";
import { AllocationChart } from "./components/AllocationChart";
import { PnlRankingChart } from "./components/PnlRankingChart";
import { PositionsTable } from "./components/PositionsTable";
import { RiskAlertPanel } from "./components/RiskAlertPanel";
import { ThemeExposureChart } from "./components/ThemeExposureChart";
import { YearlyReviewPanel } from "./components/YearlyReviewPanel";
import type { PortfolioData } from "./types/portfolio";
import { calculateRiskAlerts, calculateThemeExposure, normalizePositions } from "./utils/portfolio";

const portfolioData = rawData as PortfolioData;

function App() {
  const positions = normalizePositions(portfolioData.positions, portfolioData.account_summary.total_assets);
  const themeExposure = calculateThemeExposure(positions, portfolioData.account_summary.total_assets);
  const alerts = calculateRiskAlerts(portfolioData.account_summary, positions, themeExposure);

  return (
    <main className="min-h-screen bg-ink text-text">
      <div className="market-grid" />
      <div className="relative mx-auto max-w-[1500px] px-4 py-5 sm:px-6 lg:px-8">
        <header className="mb-5 flex flex-col gap-3 border-b border-line pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="eyebrow">Personal Investment Review</p>
            <h1 className="font-display text-2xl font-semibold tracking-normal text-text md:text-4xl">
              IBKR 持仓复盘 Dashboard
            </h1>
          </div>
          <div className="flex flex-wrap gap-2 text-xs text-muted">
            <span className="rounded border border-line bg-white/[0.03] px-3 py-1.5">Static JSON</span>
            <span className="rounded border border-line bg-white/[0.03] px-3 py-1.5">React + ECharts</span>
            <span className="rounded border border-line bg-white/[0.03] px-3 py-1.5">Risk Rules Configurable</span>
          </div>
        </header>

        <div className="grid gap-4 lg:grid-cols-12">
          <AccountSummaryCard account={portfolioData.account_summary} alerts={alerts} />
          {portfolioData.yearly_analysis ? <YearlyReviewPanel years={portfolioData.yearly_analysis} /> : null}
          <div className="grid gap-4 lg:col-span-12 xl:grid-cols-3">
            <AllocationChart positions={positions} />
            <ThemeExposureChart exposure={themeExposure} />
            <PnlRankingChart positions={positions} />
          </div>
          <RiskAlertPanel alerts={alerts} />
          <PositionsTable positions={positions} />
        </div>
      </div>
    </main>
  );
}

export default App;

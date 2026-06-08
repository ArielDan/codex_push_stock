import ReactECharts from "echarts-for-react";
import type { Position } from "../types/portfolio";
import { getPnlRanking } from "../utils/portfolio";
import { ChartFrame } from "./ChartFrame";

type PnlRankingChartProps = {
  positions: Position[];
};

export function PnlRankingChart({ positions }: PnlRankingChartProps) {
  const data = getPnlRanking(positions);
  const option = {
    grid: { left: 12, right: 20, top: 12, bottom: 14, containLabel: true },
    xAxis: {
      type: "category",
      data: data.map((position) => position.symbol),
      axisLabel: { color: "#8fa1af", interval: 0, rotate: 35 },
      axisTick: { show: false },
      axisLine: { lineStyle: { color: "rgba(178,191,204,.18)" } },
    },
    yAxis: {
      type: "value",
      axisLabel: { color: "#8fa1af", formatter: "${value}" },
      splitLine: { lineStyle: { color: "rgba(178,191,204,.1)" } },
    },
    tooltip: {
      trigger: "axis",
      backgroundColor: "#101820",
      borderColor: "rgba(178,191,204,.18)",
      textStyle: { color: "#e9eef2" },
    },
    series: [
      {
        type: "bar",
        data: data.map((position) => Number(position.unrealized_pnl.toFixed(2))),
        barWidth: 16,
        itemStyle: {
          borderRadius: [5, 5, 0, 0],
          color: ({ value }: { value: number }) => (value >= 0 ? "#4fb783" : "#d76767"),
        },
      },
    ],
  };

  return (
    <ChartFrame title="浮盈亏贡献排行" kicker="P&L Ranking">
      <ReactECharts option={option} className="h-[290px]" />
    </ChartFrame>
  );
}

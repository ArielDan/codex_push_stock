import ReactECharts from "echarts-for-react";
import type { Position } from "../types/portfolio";
import { ChartFrame } from "./ChartFrame";

type AllocationChartProps = {
  positions: Position[];
};

export function AllocationChart({ positions }: AllocationChartProps) {
  const top = positions.slice(0, 12);
  const option = {
    color: ["#d7aa55", "#57a8c7", "#4fb783", "#d76767", "#9fb4c7", "#d19a7a", "#86a376", "#c8c1ad"],
    tooltip: {
      trigger: "item",
      backgroundColor: "#101820",
      borderColor: "rgba(178,191,204,.18)",
      textStyle: { color: "#e9eef2" },
      formatter: "{b}<br/>${c} ({d}%)",
    },
    legend: {
      bottom: 0,
      left: "center",
      type: "scroll",
      itemWidth: 8,
      itemHeight: 8,
      textStyle: { color: "#8fa1af", fontSize: 10 },
      pageIconColor: "#d7aa55",
      pageTextStyle: { color: "#8fa1af" },
    },
    series: [
      {
        type: "pie",
        radius: ["45%", "68%"],
        center: ["50%", "47%"],
        avoidLabelOverlap: true,
        itemStyle: { borderColor: "#0b1116", borderWidth: 2 },
        label: { show: false },
        emphasis: {
          label: { show: true, color: "#e9eef2", formatter: "{b} {d}%", fontSize: 12 },
        },
        data: top.map((position) => ({
          name: position.symbol,
          value: Number(position.market_value.toFixed(2)),
        })),
      },
    ],
  };

  return (
    <ChartFrame title="标的仓位占比" kicker="Allocation by Symbol">
      <ReactECharts option={option} className="h-[290px]" />
    </ChartFrame>
  );
}

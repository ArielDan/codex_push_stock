import ReactECharts from "echarts-for-react";
import type { ThemeExposure } from "../types/portfolio";
import { ChartFrame } from "./ChartFrame";

type ThemeExposureChartProps = {
  exposure: ThemeExposure[];
};

export function ThemeExposureChart({ exposure }: ThemeExposureChartProps) {
  const data = exposure.slice(0, 10).reverse();
  const option = {
    grid: { left: 8, right: 24, top: 8, bottom: 8, containLabel: true },
    xAxis: {
      type: "value",
      axisLabel: { color: "#8fa1af", formatter: "{value}%" },
      splitLine: { lineStyle: { color: "rgba(178,191,204,.1)" } },
    },
    yAxis: {
      type: "category",
      data: data.map((item) => item.theme),
      axisLabel: { color: "#b6c2cc", width: 130, overflow: "truncate" },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    tooltip: {
      trigger: "axis",
      backgroundColor: "#101820",
      borderColor: "rgba(178,191,204,.18)",
      textStyle: { color: "#e9eef2" },
      valueFormatter: (value: number) => `${value.toFixed(1)}%`,
    },
    series: [
      {
        type: "bar",
        data: data.map((item) => Number(item.weight_pct.toFixed(2))),
        barWidth: 12,
        itemStyle: {
          color: "#57a8c7",
          borderRadius: [0, 6, 6, 0],
        },
        markLine: {
          symbol: "none",
          lineStyle: { color: "#d7aa55", type: "dashed" },
          label: { color: "#d7aa55", formatter: "35%" },
          data: [{ xAxis: 35 }],
        },
      },
    ],
  };

  return (
    <ChartFrame title="主题暴露" kicker="Theme Exposure">
      <ReactECharts option={option} className="h-[290px]" />
    </ChartFrame>
  );
}

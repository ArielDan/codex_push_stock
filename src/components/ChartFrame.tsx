import type { ReactNode } from "react";

type ChartFrameProps = {
  title: string;
  kicker: string;
  children: ReactNode;
  className?: string;
};

export function ChartFrame({ title, kicker, children, className = "" }: ChartFrameProps) {
  return (
    <section className={`panel min-h-[360px] ${className}`}>
      <div className="mb-5 flex items-start justify-between gap-4">
        <div>
          <p className="eyebrow">{kicker}</p>
          <h2 className="text-lg font-semibold tracking-wide text-text">{title}</h2>
        </div>
      </div>
      {children}
    </section>
  );
}

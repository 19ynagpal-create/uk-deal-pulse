import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const axis = {
  stroke: "var(--color-border-strong)",
  tick: { fill: "var(--color-muted-foreground)", fontSize: 11 },
  tickLine: false,
};

const tooltipStyle = {
  contentStyle: {
    background: "var(--color-card)",
    border: "1px solid var(--color-border-strong)",
    borderRadius: 2,
    fontSize: 12,
  },
  labelStyle: { color: "var(--color-foreground)", fontWeight: 600 },
  cursor: { fill: "var(--color-muted)" },
};

export function monthLabel(month: string) {
  const [y, m] = month.split("-");
  return new Date(Date.UTC(Number(y), Number(m) - 1, 1)).toLocaleDateString("en-GB", {
    month: "short",
    year: "2-digit",
    timeZone: "UTC",
  });
}

export function ChartFrame({
  height = 260,
  children,
}: {
  height?: number;
  children: React.ReactElement;
}) {
  return (
    <div style={{ height }} className="w-full">
      <ResponsiveContainer width="100%" height="100%">
        {children}
      </ResponsiveContainer>
    </div>
  );
}

export function MonthlyBars({
  data,
  dataKey,
  name,
  formatter,
}: {
  data: { month: string; deals: number; value: number }[];
  dataKey: "deals" | "value";
  name: string;
  formatter?: (v: number) => string;
}) {
  return (
    <ChartFrame>
      <BarChart data={data} margin={{ top: 4, right: 8, left: -12, bottom: 0 }}>
        <CartesianGrid vertical={false} stroke="var(--color-border)" />
        <XAxis dataKey="month" tickFormatter={monthLabel} {...axis} />
        <YAxis
          {...axis}
          width={56}
          allowDecimals={false}
          tickFormatter={(v) => (formatter ? formatter(v) : String(v))}
        />
        <Tooltip
          {...tooltipStyle}
          labelFormatter={(l) => monthLabel(String(l))}
          formatter={(v: number) => [formatter ? formatter(v) : v, name]}
        />
        <Bar dataKey={dataKey} fill="var(--color-chart-1)" maxBarSize={26} />
      </BarChart>
    </ChartFrame>
  );
}

export function MonthlyLine({
  data,
  formatter,
}: {
  data: { month: string; value: number }[];
  formatter?: (v: number) => string;
}) {
  return (
    <ChartFrame>
      <LineChart data={data} margin={{ top: 4, right: 8, left: -12, bottom: 0 }}>
        <CartesianGrid vertical={false} stroke="var(--color-border)" />
        <XAxis dataKey="month" tickFormatter={monthLabel} {...axis} />
        <YAxis {...axis} width={56} tickFormatter={(v) => (formatter ? formatter(v) : String(v))} />
        <Tooltip
          {...tooltipStyle}
          cursor={{ stroke: "var(--color-border-strong)" }}
          labelFormatter={(l) => monthLabel(String(l))}
          formatter={(v: number) => [formatter ? formatter(v) : v, "Announced value"]}
        />
        <Line
          type="monotone"
          dataKey="value"
          stroke="var(--color-chart-2)"
          strokeWidth={2}
          dot={{ r: 2.5, fill: "var(--color-chart-2)" }}
        />
      </LineChart>
    </ChartFrame>
  );
}

export function CategoryBars({
  data,
  categoryKey,
  valueKey,
  name,
  formatter,
  height = 280,
  colorful = false,
}: {
  data: Record<string, unknown>[];
  categoryKey: string;
  valueKey: string;
  name: string;
  formatter?: (v: number) => string;
  height?: number;
  colorful?: boolean;
}) {
  const palette = [
    "var(--color-chart-1)",
    "var(--color-chart-2)",
    "var(--color-chart-3)",
    "var(--color-chart-4)",
    "var(--color-chart-5)",
  ];
  return (
    <ChartFrame height={height}>
      <BarChart data={data} layout="vertical" margin={{ top: 4, right: 16, left: 8, bottom: 0 }}>
        <CartesianGrid horizontal={false} stroke="var(--color-border)" />
        <XAxis type="number" allowDecimals={false} {...axis} tickFormatter={(v) => (formatter ? formatter(v) : String(v))} />
        <YAxis type="category" dataKey={categoryKey} {...axis} width={120} />
        <Tooltip {...tooltipStyle} formatter={(v: number) => [formatter ? formatter(v) : v, name]} />
        <Bar dataKey={valueKey} maxBarSize={20}>
          {data.map((_, i) => (
            <Cell key={i} fill={colorful ? palette[i % palette.length] : "var(--color-chart-1)"} />
          ))}
        </Bar>
      </BarChart>
    </ChartFrame>
  );
}

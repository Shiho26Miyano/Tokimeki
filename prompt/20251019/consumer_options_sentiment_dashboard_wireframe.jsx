import React, { useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Download, Filter, TrendingUp, TrendingDown } from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
  BarChart,
  Bar,
  AreaChart,
  Area,
  Legend,
  ComposedChart,
} from "recharts";

/**
 * Consumer Options Sentiment Dashboard — UI Wireframe (static demo)
 * ---------------------------------------------------------------
 * Purpose: show the layout/flow. All data is mocked; swap in live data later.
 * Styling: Tailwind + shadcn/ui components
 * Charts: recharts (preinstalled in this environment)
 */

const SAMPLE_TICKERS = ["COST", "WMT", "TGT", "AMZN", "AAPL"];

// --- Mocked data builders ---
const mockIvTermStructure = (ticker) => {
  const expiries = ["2025-11-01", "2025-11-08", "2025-11-15", "2025-11-22", "2025-12-06", "2025-12-20", "2026-01-17", "2026-03-21"];
  return expiries.map((d, i) => ({ expiry: d, iv_median: 0.25 + 0.02 * Math.sin(i + ticker.length) }));
};

const mockUnderlyingDaily = () =>
  Array.from({ length: 60 }).map((_, i) => ({
    date: new Date(Date.now() - (60 - i) * 24 * 3600 * 1000).toISOString().slice(0, 10),
    open: 700 + Math.sin(i / 6) * 8 + i * 0.3,
    high: 705 + Math.sin(i / 6) * 8 + i * 0.3 + 3,
    low: 695 + Math.sin(i / 6) * 8 + i * 0.3 - 3,
    close: 702 + Math.sin(i / 6) * 8 + i * 0.3,
    volume: 800000 + Math.round(Math.abs(Math.cos(i / 7) * 120000)),
  }));

const mockChainRows = (ticker) => {
  const types = ["call", "put"]; const rows = [];
  for (let i = 0; i < 24; i++) {
    const t = types[i % 2];
    rows.push({
      contract: `${ticker}251122${t === "call" ? "C" : "P"}${(700 + i * 5).toString().padStart(7, "0")}`,
      expiry: "2025-11-22",
      type: t,
      strike: 700 + i * 5,
      iv: 0.22 + (i % 5) * 0.01,
      delta: t === "call" ? 0.6 - i * 0.01 : -0.4 + i * 0.01,
      gamma: 0.02 + (i % 4) * 0.002,
      theta: -0.04 + (i % 3) * -0.002,
      vega: 0.11 + (i % 6) * 0.01,
      last: 10 + (i % 7) * 0.7,
      day_volume: 100 + (i % 10) * 25,
      day_oi: 1000 + (i % 12) * 75,
    });
  }
  return rows;
};

const formatPct = (x) => (x == null ? "—" : `${(x * 100).toFixed(1)}%`);

export default function ConsumerOptionsDashboard() {
  const [tickers, setTickers] = useState(["COST", "AMZN"]);
  const [focusTicker, setFocusTicker] = useState("COST");
  const [onlyUnusual, setOnlyUnusual] = useState(false);

  const chain = useMemo(() => mockChainRows(focusTicker), [focusTicker]);
  const ivTerm = useMemo(() => mockIvTermStructure(focusTicker), [focusTicker]);
  const underlying = useMemo(() => mockUnderlyingDaily(), []);

  const callPut = useMemo(() => {
    const calls = chain.filter((r) => r.type === "call");
    const puts = chain.filter((r) => r.type === "put");
    const volC = calls.reduce((s, r) => s + (r.day_volume || 0), 0);
    const volP = puts.reduce((s, r) => s + (r.day_volume || 0), 0);
    const oiC = calls.reduce((s, r) => s + (r.day_oi || 0), 0);
    const oiP = puts.reduce((s, r) => s + (r.day_oi || 0), 0);
    return {
      volRatio: volP ? volC / volP : null,
      oiRatio: oiP ? oiC / oiP : null,
      totalOI: oiC + oiP,
      medianIV: chain.length ? chain.reduce((s, r) => s + (r.iv || 0), 0) / chain.length : null,
    };
  }, [chain]);

  const unusual = useMemo(() => {
    // Mock unusual: mark rows with volume > 300 or iv > 0.28
    return chain.filter((r) => r.day_volume > 300 || r.iv > 0.28);
  }, [chain]);

  const displayRows = onlyUnusual ? unusual : chain;

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight">Consumer Options Sentiment</h1>
            <p className="text-sm text-muted-foreground">Polygon Options Starter • 15‑min delayed • 2y history</p>
          </div>
          <div className="flex items-center gap-2">
            <Select value={focusTicker} onValueChange={setFocusTicker}>
              <SelectTrigger className="w-40"><SelectValue placeholder="Ticker" /></SelectTrigger>
              <SelectContent>
                {SAMPLE_TICKERS.map((t) => (
                  <SelectItem key={t} value={t}>{t}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button variant="outline" className="gap-2"><Filter className="h-4 w-4"/> Filters</Button>
            <Button className="gap-2"><Download className="h-4 w-4"/> Export CSV</Button>
          </div>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
          <Card className="rounded-2xl shadow-sm">
            <CardHeader className="pb-2"><CardTitle className="text-sm">Call/Put Volume</CardTitle></CardHeader>
            <CardContent>
              <div className="text-2xl font-semibold">{callPut.volRatio ? callPut.volRatio.toFixed(2) : "—"}</div>
              <Badge variant={callPut.volRatio > 1 ? "default" : "secondary"} className="mt-2">
                {callPut.volRatio > 1 ? <span className="flex items-center gap-1"><TrendingUp className="h-3 w-3"/> Bullish</span> : <span className="flex items-center gap-1"><TrendingDown className="h-3 w-3"/> Bearish/Neutral</span>}
              </Badge>
            </CardContent>
          </Card>
          <Card className="rounded-2xl shadow-sm">
            <CardHeader className="pb-2"><CardTitle className="text-sm">Call/Put OI</CardTitle></CardHeader>
            <CardContent>
              <div className="text-2xl font-semibold">{callPut.oiRatio ? callPut.oiRatio.toFixed(2) : "—"}</div>
              <p className="mt-1 text-xs text-muted-foreground">Total OI: {callPut.totalOI.toLocaleString()}</p>
            </CardContent>
          </Card>
          <Card className="rounded-2xl shadow-sm">
            <CardHeader className="pb-2"><CardTitle className="text-sm">Median IV (chain)</CardTitle></CardHeader>
            <CardContent>
              <div className="text-2xl font-semibold">{formatPct(callPut.medianIV)}</div>
              <p className="mt-1 text-xs text-muted-foreground">Across {chain.length} contracts</p>
            </CardContent>
          </Card>
          <Card className="rounded-2xl shadow-sm">
            <CardHeader className="pb-2"><CardTitle className="text-sm">Unusual Flags</CardTitle></CardHeader>
            <CardContent>
              <div className="text-2xl font-semibold">{unusual.length}</div>
              <div className="mt-2 flex items-center gap-2 text-xs">
                <Checkbox id="unusual" checked={onlyUnusual} onCheckedChange={(v) => setOnlyUnusual(Boolean(v))} />
                <label htmlFor="unusual" className="text-muted-foreground">Show only unusual</label>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Left: Chain + Unusual */}
          <div className="lg:col-span-2 space-y-6">
            <Card className="rounded-2xl shadow-sm">
              <CardHeader className="pb-2"><CardTitle>Option Chain Overview</CardTitle></CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="sticky top-0 bg-white">
                      <tr className="text-left">
                        <th className="py-2 pr-4">Contract</th>
                        <th className="py-2 pr-4">Expiry</th>
                        <th className="py-2 pr-4">Type</th>
                        <th className="py-2 pr-4">Strike</th>
                        <th className="py-2 pr-4">IV</th>
                        <th className="py-2 pr-4">Δ</th>
                        <th className="py-2 pr-4">Γ</th>
                        <th className="py-2 pr-4">Θ</th>
                        <th className="py-2 pr-4">Vega</th>
                        <th className="py-2 pr-4">Last</th>
                        <th className="py-2 pr-4">Vol</th>
                        <th className="py-2">OI</th>
                      </tr>
                    </thead>
                    <tbody>
                      {displayRows.map((r) => (
                        <tr key={r.contract} className="border-b last:border-none">
                          <td className="py-2 pr-4 font-mono text-[11px]">{r.contract}</td>
                          <td className="py-2 pr-4">{r.expiry}</td>
                          <td className="py-2 pr-4 capitalize">{r.type}</td>
                          <td className="py-2 pr-4">{r.strike}</td>
                          <td className="py-2 pr-4">{formatPct(r.iv)}</td>
                          <td className="py-2 pr-4">{r.delta?.toFixed(2)}</td>
                          <td className="py-2 pr-4">{r.gamma?.toFixed(3)}</td>
                          <td className="py-2 pr-4">{r.theta?.toFixed(3)}</td>
                          <td className="py-2 pr-4">{r.vega?.toFixed(3)}</td>
                          <td className="py-2 pr-4">{r.last?.toFixed?.(2) ?? r.last}</td>
                          <td className="py-2 pr-4">{r.day_volume}</td>
                          <td className="py-2">{r.day_oi}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>

            <Card className="rounded-2xl shadow-sm">
              <CardHeader className="pb-2"><CardTitle>Contract Drilldown (Price vs Volume)</CardTitle></CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={280}>
                  <ComposedChart data={underlying.slice(-60)}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" hide />
                    <YAxis yAxisId="left" />
                    <YAxis yAxisId="right" orientation="right" />
                    <Tooltip />
                    <Area yAxisId="left" type="monotone" dataKey="close" fillOpacity={0.2} />
                    <Bar yAxisId="right" dataKey="volume" fillOpacity={0.6} />
                    <Legend />
                  </ComposedChart>
                </ResponsiveContainer>
                <p className="mt-2 text-xs text-muted-foreground">Replace with selected option's 1‑minute series + volume.</p>
              </CardContent>
            </Card>
          </div>

          {/* Right: IV Term & Underlying */}
          <div className="space-y-6">
            <Card className="rounded-2xl shadow-sm">
              <CardHeader className="pb-2"><CardTitle>IV Term Structure</CardTitle></CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={220}>
                  <LineChart data={ivTerm}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="expiry" tick={{ fontSize: 10 }} />
                    <YAxis domain={[0, 0.6]} tickFormatter={(v) => `${Math.round(v * 100)}%`} />
                    <Tooltip formatter={(v) => formatPct(v)} />
                    <Line type="monotone" dataKey="iv_median" dot />
                  </LineChart>
                </ResponsiveContainer>
                <p className="mt-2 text-xs text-muted-foreground">Median IV per expiry for next 8 expirations.</p>
              </CardContent>
            </Card>

            <Card className="rounded-2xl shadow-sm">
              <CardHeader className="pb-2"><CardTitle>Underlying (Daily)</CardTitle></CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={220}>
                  <AreaChart data={underlying}>
                    <defs>
                      <linearGradient id="uv" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopOpacity={0.4}/>
                        <stop offset="95%" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" hide />
                    <YAxis />
                    <Tooltip />
                    <Area type="monotone" dataKey="close" strokeOpacity={0.9} fill="url(#uv)" />
                  </AreaChart>
                </ResponsiveContainer>
                <p className="mt-2 text-xs text-muted-foreground">Candles/RSI can replace this area chart.</p>
              </CardContent>
            </Card>
          </div>
        </div>

        <Separator />
        <div className="text-xs text-muted-foreground">
          <p>Wireframe only • Replace mocked selectors/data with Polygon API calls. Cache snapshots ~60s, aggregates ~10m.</p>
        </div>
      </div>
    </div>
  );
}

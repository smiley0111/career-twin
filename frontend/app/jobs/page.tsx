"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import type { Job, JobCategory } from "../types";
import { JOB_CATEGORY_LABELS } from "../types";

interface Stats {
  total: number;
  by_category: Record<string, number>;
  by_city: Record<string, number>;
}

const CATEGORY_COLORS: Record<JobCategory, string> = {
  developer: "bg-blue-50 text-blue-700 ring-blue-200",
  test: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  ai: "bg-purple-50 text-purple-700 ring-purple-200",
  pm: "bg-amber-50 text-amber-700 ring-amber-200",
  manager: "bg-rose-50 text-rose-700 ring-rose-200",
  other: "bg-neutral-100 text-neutral-700 ring-neutral-200",
};

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [cityFilter, setCityFilter] = useState<string>("");
  const [catFilter, setCatFilter] = useState<JobCategory | "">("");

  useEffect(() => {
    Promise.all([
      fetch("/api/jobs").then((r) => r.json()),
      fetch("/api/jobs/stats").then((r) => r.json()),
    ])
      .then(([js, st]) => {
        setJobs(js);
        setStats(st);
      })
      .finally(() => setLoading(false));
  }, []);

  const cities = useMemo(() => {
    if (!stats) return [];
    return Object.keys(stats.by_city).sort();
  }, [stats]);

  const filtered = useMemo(() => {
    return jobs.filter((j) => {
      if (cityFilter && j.city !== cityFilter) return false;
      if (catFilter && j.category !== catFilter) return false;
      return true;
    });
  }, [jobs, cityFilter, catFilter]);

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <header className="mb-8 flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">岗位库</h1>
          <p className="mt-2 text-neutral-600">
            Agent 2 在为你做市场情报时, 真正读的就是这些岗位
          </p>
        </div>
        <Link
          href="/"
          className="text-sm text-neutral-600 underline-offset-4 hover:underline"
        >
          ← 回到职业分身
        </Link>
      </header>

      {stats && (
        <section className="mb-6 rounded-xl border border-neutral-200 bg-white p-6 shadow-sm">
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <Stat label="总岗位数" value={stats.total.toString()} />
            <Stat
              label="覆盖城市"
              value={Object.keys(stats.by_city).length.toString()}
            />
            <Stat
              label="主导类别"
              value={
                Object.entries(stats.by_category).sort(
                  (a, b) => b[1] - a[1]
                )[0]?.[0] ?? "-"
              }
            />
            <Stat
              label="数据源"
              value={
                Array.from(new Set(jobs.map((j) => j.source))).join(", ") || "-"
              }
            />
          </div>
          <div className="mt-4 flex flex-wrap gap-2 text-xs">
            {Object.entries(stats.by_category).map(([cat, n]) => (
              <span
                key={cat}
                className={`rounded-full px-3 py-1 ring-1 ${
                  CATEGORY_COLORS[cat as JobCategory] ?? CATEGORY_COLORS.other
                }`}
              >
                {JOB_CATEGORY_LABELS[cat as JobCategory] ?? cat}: {n}
              </span>
            ))}
          </div>
        </section>
      )}

      <section className="mb-4 rounded-xl border border-neutral-200 bg-white p-4 shadow-sm">
        <div className="flex flex-wrap items-center gap-3">
          <span className="text-sm font-medium text-neutral-700">过滤:</span>
          <select
            className="rounded-lg border border-neutral-300 bg-white px-3 py-1.5 text-sm"
            value={cityFilter}
            onChange={(e) => setCityFilter(e.target.value)}
          >
            <option value="">全部城市</option>
            {cities.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
          <select
            className="rounded-lg border border-neutral-300 bg-white px-3 py-1.5 text-sm"
            value={catFilter}
            onChange={(e) => setCatFilter(e.target.value as JobCategory | "")}
          >
            <option value="">全部类别</option>
            {(Object.keys(JOB_CATEGORY_LABELS) as JobCategory[]).map((k) => (
              <option key={k} value={k}>
                {JOB_CATEGORY_LABELS[k]}
              </option>
            ))}
          </select>
          <span className="ml-auto text-xs text-neutral-500">
            显示 {filtered.length} / {jobs.length}
          </span>
        </div>
      </section>

      {loading ? (
        <p className="py-10 text-center text-sm text-neutral-500">加载中...</p>
      ) : (
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          {filtered.map((j) => (
            <JobCard key={j.id} job={j} />
          ))}
        </div>
      )}
    </main>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-sm font-medium text-neutral-500">{label}</p>
      <p className="mt-0.5 text-xl font-semibold">{value}</p>
    </div>
  );
}

function JobCard({ job }: { job: Job }) {
  return (
    <div className="rounded-lg border border-neutral-200 bg-white p-4 shadow-sm transition hover:shadow-md">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h3 className="text-base font-semibold leading-tight">{job.title}</h3>
          <p className="mt-0.5 text-sm text-neutral-600">
            {job.company} · {job.city} · {job.experience}
          </p>
        </div>
        <span className="whitespace-nowrap text-sm font-semibold text-neutral-900">
          {job.salary_text}
        </span>
      </div>

      <div className="mt-2">
        <span
          className={`rounded px-2 py-0.5 text-xs ring-1 ${
            CATEGORY_COLORS[job.category]
          }`}
        >
          {JOB_CATEGORY_LABELS[job.category]}
        </span>
      </div>

      <p className="mt-2 text-sm text-neutral-700">{job.description}</p>

      {job.skills.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1">
          {job.skills.map((s) => (
            <span
              key={s}
              className="rounded bg-neutral-100 px-2 py-0.5 text-xs text-neutral-600"
            >
              {s}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import type {
  UserProfile,
  CareerReport,
  TestCase,
  JobCategory,
} from "./types";
import { JOB_CATEGORY_LABELS } from "./types";

const DEFAULT_PROFILE: UserProfile = {
  age: 47,
  role: "测试经理",
  role_category: "manager",
  industry: "互联网电视",
  city: "青岛",
  family: "两个孩子",
  mortgage_wan: 60,
  current_monthly_salary_k: 30,
  expectation: "尽量保持收入",
};

export default function HomePage() {
  const [profile, setProfile] = useState<UserProfile>(DEFAULT_PROFILE);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<CareerReport | null>(null);
  const [testCases, setTestCases] = useState<TestCase[]>([]);
  const [activeProbe, setActiveProbe] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/test-cases")
      .then((r) => (r.ok ? r.json() : []))
      .then((data: TestCase[]) => setTestCases(data))
      .catch(() => {});
  }, []);

  const update = <K extends keyof UserProfile>(key: K, value: UserProfile[K]) => {
    setProfile((p) => ({ ...p, [key]: value }));
  };

  const loadTestCase = (tc: TestCase) => {
    setProfile(tc.profile);
    setActiveProbe(`${tc.name} · ${tc.probe}`);
    setReport(null);
    setError(null);
  };

  const submit = async () => {
    setLoading(true);
    setError(null);
    setReport(null);
    try {
      const res = await fetch("/api/career-twin", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(profile),
      });
      if (!res.ok) {
        const detail = await res.text();
        throw new Error(`HTTP ${res.status}: ${detail}`);
      }
      const data: CareerReport = await res.json();
      setReport(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <header className="mb-8 flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            Career Twin · 职业分身
          </h1>
          <p className="mt-2 text-neutral-600">
            AI 不替你做决定, 只帮你看清未来有哪几条路
          </p>
        </div>
        <Link
          href="/jobs"
          className="rounded-lg border border-neutral-300 bg-white px-3 py-1.5 text-sm text-neutral-700 transition hover:border-neutral-900 hover:bg-neutral-900 hover:text-white"
        >
          查看岗位库 →
        </Link>
      </header>

      <section className="rounded-xl border border-neutral-200 bg-white p-6 shadow-sm">
        <h2 className="mb-2 text-lg font-semibold">输入你的画像</h2>

        {testCases.length > 0 && (
          <div className="mb-5">
            <p className="mb-2 text-xs font-medium text-neutral-500">
              快速加载预设画像 (压力测试用)
            </p>
            <div className="flex flex-wrap gap-2">
              {testCases.map((tc) => (
                <button
                  key={tc.id}
                  onClick={() => loadTestCase(tc)}
                  className="rounded-full border border-neutral-300 bg-white px-3 py-1 text-xs text-neutral-700 transition hover:border-neutral-900 hover:bg-neutral-900 hover:text-white"
                  title={tc.description}
                >
                  {tc.name}
                </button>
              ))}
            </div>
            {activeProbe && (
              <p className="mt-2 rounded bg-amber-50 px-3 py-2 text-xs text-amber-800">
                <span className="font-medium">探测目标</span>: {activeProbe}
              </p>
            )}
          </div>
        )}

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Field label="年龄">
            <input
              type="number"
              className="input"
              value={profile.age}
              onChange={(e) => update("age", Number(e.target.value))}
            />
          </Field>
          <Field label="当前岗位">
            <input
              className="input"
              value={profile.role}
              onChange={(e) => update("role", e.target.value)}
            />
          </Field>
          <Field label="岗位大类 (决定 Agent 检索哪些岗位)">
            <select
              className="input"
              value={profile.role_category}
              onChange={(e) =>
                update("role_category", e.target.value as JobCategory)
              }
            >
              {(Object.keys(JOB_CATEGORY_LABELS) as JobCategory[]).map((k) => (
                <option key={k} value={k}>
                  {JOB_CATEGORY_LABELS[k]}
                </option>
              ))}
            </select>
          </Field>
          <Field label="所在行业">
            <input
              className="input"
              value={profile.industry}
              onChange={(e) => update("industry", e.target.value)}
            />
          </Field>
          <Field label="所在城市">
            <input
              className="input"
              value={profile.city}
              onChange={(e) => update("city", e.target.value)}
            />
          </Field>
          <Field label="家庭状况">
            <input
              className="input"
              value={profile.family}
              onChange={(e) => update("family", e.target.value)}
            />
          </Field>
          <Field label="房贷余额 (万元)">
            <input
              type="number"
              className="input"
              value={profile.mortgage_wan}
              onChange={(e) => update("mortgage_wan", Number(e.target.value))}
            />
          </Field>
          <Field label="当前税前月薪 (K)">
            <input
              type="number"
              className="input"
              value={profile.current_monthly_salary_k}
              onChange={(e) =>
                update("current_monthly_salary_k", Number(e.target.value))
              }
            />
          </Field>
          <Field label="个人期望" className="md:col-span-2">
            <textarea
              className="input min-h-[80px]"
              value={profile.expectation}
              onChange={(e) => update("expectation", e.target.value)}
            />
          </Field>
        </div>

        <button
          onClick={submit}
          disabled={loading}
          className="mt-6 rounded-lg bg-neutral-900 px-6 py-2.5 text-white transition hover:bg-neutral-700 disabled:opacity-50"
        >
          {loading ? "Agent 工作中... (大约 30 秒)" : "生成职业分身"}
        </button>

        {error && (
          <p className="mt-4 rounded bg-red-50 p-3 text-sm text-red-700">
            出错: {error}
          </p>
        )}
      </section>

      {report && <Report report={report} />}
    </main>
  );
}

function Field({
  label,
  children,
  className = "",
}: {
  label: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <label className={`flex flex-col gap-1.5 ${className}`}>
      <span className="text-sm font-medium text-neutral-700">{label}</span>
      {children}
    </label>
  );
}

function Report({ report }: { report: CareerReport }) {
  const { persona, market, simulation } = report;
  return (
    <section className="mt-8 space-y-6">
      {/* 画像总结 */}
      <Card title="画像分析">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <Stat label="职业阶段" value={persona.career_stage} />
          <Stat label="核心诉求" value={persona.primary_need} />
          <Stat
            label="风险评分"
            value={`${persona.risk_score} / 10`}
            valueClass={persona.risk_score >= 7 ? "text-red-600" : "text-amber-600"}
          />
        </div>
        <div className="mt-4">
          <p className="text-sm font-medium text-neutral-500">主要约束</p>
          <ul className="mt-1 list-disc pl-5 text-sm">
            {persona.main_constraints.map((c, i) => (
              <li key={i}>{c}</li>
            ))}
          </ul>
        </div>
      </Card>

      {/* 市场情报 */}
      <Card title="市场情报">
        <p className="text-sm text-neutral-700">{market.summary}</p>
        <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2">
          {market.positions.map((p, i) => (
            <div
              key={i}
              className="rounded-lg border border-neutral-200 bg-neutral-50 p-4"
            >
              <div className="flex items-baseline justify-between">
                <h4 className="font-semibold">{p.name}</h4>
                <span className="text-sm text-neutral-600">{p.salary_range}</span>
              </div>
              <p className="mt-1 text-xs text-neutral-500">
                {p.job_count_desc} · {p.note}
              </p>
              <div className="mt-2 flex flex-wrap gap-1">
                {p.hot_skills.map((s, j) => (
                  <span
                    key={j}
                    className="rounded bg-white px-2 py-0.5 text-xs text-neutral-700 ring-1 ring-neutral-200"
                  >
                    {s}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* 路线推演 */}
      <Card title="未来路线">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {simulation.paths.map((path, i) => (
            <div
              key={i}
              className="flex flex-col rounded-lg border-2 border-neutral-200 p-4 transition hover:border-neutral-900"
            >
              <h4 className="text-base font-semibold">{path.name}</h4>
              <p className="mt-1 text-sm text-neutral-600">{path.one_liner}</p>

              <div className="mt-3 grid grid-cols-3 gap-2 text-center text-xs">
                <Mini
                  label="成功率"
                  value={"★".repeat(path.success_probability) + "☆".repeat(5 - path.success_probability)}
                />
                <Mini label="周期" value={`${path.expected_months}月`} />
                <Mini label="预期薪资" value={path.expected_salary_band} />
              </div>

              <div className="mt-3">
                <p className="text-xs font-medium text-neutral-500">对标岗位</p>
                <div className="mt-1 flex flex-wrap gap-1">
                  {path.target_positions.map((t, j) => (
                    <span
                      key={j}
                      className="rounded bg-neutral-100 px-2 py-0.5 text-xs text-neutral-700"
                    >
                      {t}
                    </span>
                  ))}
                </div>
              </div>

              <div className="mt-3">
                <p className="text-xs font-medium text-neutral-500">主要风险</p>
                <ul className="mt-1 list-disc pl-4 text-xs">
                  {path.main_risks.map((r, j) => (
                    <li key={j}>{r}</li>
                  ))}
                </ul>
              </div>

              <div className="mt-3">
                <p className="text-xs font-medium text-neutral-500">行动清单</p>
                <ul className="mt-1 list-decimal pl-4 text-xs">
                  {path.required_actions.map((a, j) => (
                    <li key={j}>{a}</li>
                  ))}
                </ul>
              </div>

              <details className="mt-3 text-xs text-neutral-500">
                <summary className="cursor-pointer font-medium hover:text-neutral-700">
                  推断依据
                </summary>
                <p className="mt-1 leading-relaxed">{path.evidence}</p>
              </details>
            </div>
          ))}
        </div>

        <div className="mt-6 rounded-lg bg-neutral-900 p-4 text-sm text-neutral-100">
          <p className="mb-1 font-medium text-neutral-300">权衡建议</p>
          <p>{simulation.recommendation}</p>
        </div>
      </Card>
    </section>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-neutral-200 bg-white p-6 shadow-sm">
      <h3 className="mb-4 text-lg font-semibold">{title}</h3>
      {children}
    </div>
  );
}

function Stat({
  label,
  value,
  valueClass = "",
}: {
  label: string;
  value: string;
  valueClass?: string;
}) {
  return (
    <div>
      <p className="text-sm font-medium text-neutral-500">{label}</p>
      <p className={`mt-0.5 text-base font-semibold ${valueClass}`}>{value}</p>
    </div>
  );
}

function Mini({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded bg-neutral-50 py-1.5">
      <div className="text-[10px] text-neutral-500">{label}</div>
      <div className="font-semibold text-neutral-900">{value}</div>
    </div>
  );
}

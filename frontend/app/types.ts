// 与后端 Pydantic 模型一一对应. 后端字段变了, 这里也要同步.
// (后续阶段可以用 openapi 自动生成, 现在手写够用.)

export type JobCategory =
  | "developer"
  | "test"
  | "ai"
  | "pm"
  | "manager"
  | "other";

export const JOB_CATEGORY_LABELS: Record<JobCategory, string> = {
  developer: "Developer (研发)",
  test: "Test (测试/QA)",
  ai: "AI / 算法",
  pm: "Product (产品)",
  manager: "Manager (管理)",
  other: "Other (架构/运维/数据)",
};

export interface UserProfile {
  age: number;
  role: string;
  role_category: JobCategory;
  industry: string;
  city: string;
  family: string;
  mortgage_wan: number;
  current_monthly_salary_k: number;
  expectation: string;
}

export interface Job {
  id: number;
  title: string;
  company: string;
  city: string;
  category: JobCategory;
  salary_min_k: number;
  salary_max_k: number;
  salary_text: string;
  experience: string;
  skills: string[];
  description: string;
  source: string;
  source_url: string | null;
  posted_at: string | null;
}

export interface PersonaAnalysis {
  career_stage: "早期" | "中期" | "中后期" | "晚期";
  primary_need: string;
  main_constraints: string[];
  risk_score: number;
  risk_reasons: string[];
}

export interface PositionIntel {
  name: string;
  job_count_desc: string;
  salary_range: string;
  hot_skills: string[];
  note: string;
}

export interface MarketIntel {
  summary: string;
  positions: PositionIntel[];
}

export interface CareerPath {
  name: string;
  one_liner: string;
  success_probability: number;
  expected_months: number;
  expected_salary_band: string;
  target_positions: string[];
  main_risks: string[];
  required_actions: string[];
  evidence: string;
}

export interface CareerSimulation {
  paths: CareerPath[];
  recommendation: string;
}

export interface CareerReport {
  profile: UserProfile;
  persona: PersonaAnalysis;
  market: MarketIntel;
  simulation: CareerSimulation;
}

export interface TestCase {
  id: string;
  name: string;
  description: string;
  probe: string;
  profile: UserProfile;
}

"use client";

// 把一份 CareerReport 可视化成一棵职业路线树:
//
//   [现在的你]  ──►  [路线 A]  ──►  [对标岗位 1]
//                ├─►  [路线 B]  ──►  [对标岗位 2]
//                └─►  [路线 C]  ──►  [对标岗位 3]
//
// 设计取舍:
// - 数据直接从已有的 CareerReport 派生, 不需要新后端 endpoint (省一次往返).
// - 布局用最朴素的三列手工排布 (根 / 路线 / 岗位), 不引 dagre 之类的自动布局库,
//   因为节点数很小 (1 + 3 + N), 手写反而可控、可读、零额外依赖.
// - 边的颜色按成功率分档 (绿/琥珀/红), 让"哪条路更稳"一眼可见.

import { useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  Handle,
  Position,
  MarkerType,
  type Node,
  type Edge,
  type NodeProps,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import type { CareerReport, CareerPath } from "./types";

// ---------- 布局常量 ----------
const COL_ROOT = 0;
const COL_PATH = 340;
const COL_POS = 720;
const ROW_H = 150;
const POS_ROW_H = 90;

// ---------- 成功率 -> 颜色 ----------
function probColor(prob: number): string {
  if (prob >= 4) return "#16a34a"; // green-600
  if (prob === 3) return "#d97706"; // amber-600
  return "#dc2626"; // red-600
}

function stars(prob: number): string {
  return "★".repeat(prob) + "☆".repeat(5 - prob);
}

// ---------- 自定义节点: 现在的你 ----------
type RootData = { role: string; age: number; salaryK: number; city: string };

function RootNode({ data }: NodeProps<Node<RootData>>) {
  return (
    <div className="w-52 rounded-xl border-2 border-neutral-900 bg-neutral-900 px-4 py-3 text-white shadow-lg">
      <div className="text-[11px] uppercase tracking-wide text-neutral-400">
        现在的你
      </div>
      <div className="mt-1 text-base font-bold">{data.role}</div>
      <div className="mt-1 text-xs text-neutral-300">
        {data.age} 岁 · {data.city} · {data.salaryK}K/月
      </div>
      <Handle type="source" position={Position.Right} className="!bg-neutral-500" />
    </div>
  );
}

// ---------- 自定义节点: 一条路线 ----------
type PathData = {
  name: string;
  oneLiner: string;
  prob: number;
  months: number;
  salaryBand: string;
};

function PathNode({ data }: NodeProps<Node<PathData>>) {
  const color = probColor(data.prob);
  return (
    <div
      className="w-64 rounded-xl border-2 bg-white px-4 py-3 shadow-sm"
      style={{ borderColor: color }}
    >
      <Handle type="target" position={Position.Left} className="!bg-neutral-400" />
      <div className="flex items-baseline justify-between">
        <div className="text-sm font-bold text-neutral-900">{data.name}</div>
        <div className="text-xs font-semibold" style={{ color }}>
          {stars(data.prob)}
        </div>
      </div>
      <p className="mt-1 text-xs leading-snug text-neutral-600">{data.oneLiner}</p>
      <div className="mt-2 flex gap-3 text-[11px] text-neutral-500">
        <span>⏱ {data.months} 个月</span>
        <span>💰 {data.salaryBand}</span>
      </div>
      <Handle type="source" position={Position.Right} className="!bg-neutral-400" />
    </div>
  );
}

// ---------- 自定义节点: 对标岗位 ----------
type PosData = { name: string };

function PositionNode({ data }: NodeProps<Node<PosData>>) {
  return (
    <div className="w-44 rounded-lg border border-neutral-300 bg-neutral-50 px-3 py-2 text-xs font-medium text-neutral-700 shadow-sm">
      <Handle type="target" position={Position.Left} className="!bg-neutral-300" />
      🎯 {data.name}
    </div>
  );
}

const nodeTypes = {
  root: RootNode,
  path: PathNode,
  position: PositionNode,
};

// ---------- 把 report 转成 nodes + edges ----------
function buildGraph(report: CareerReport): { nodes: Node[]; edges: Edge[] } {
  const { profile, simulation } = report;
  const paths = simulation.paths;

  const nodes: Node[] = [];
  const edges: Edge[] = [];

  // 根节点: 垂直居中于 3 条路线
  const rootY = ((paths.length - 1) * ROW_H) / 2;
  nodes.push({
    id: "root",
    type: "root",
    position: { x: COL_ROOT, y: rootY },
    data: {
      role: profile.role,
      age: profile.age,
      salaryK: profile.current_monthly_salary_k,
      city: profile.city,
    } satisfies RootData,
  });

  // 去重的岗位叶子: 收集所有 target_positions 的并集, 保持首次出现顺序
  const posOrder: string[] = [];
  const posSeen = new Set<string>();
  paths.forEach((p) => {
    p.target_positions.forEach((t) => {
      if (!posSeen.has(t)) {
        posSeen.add(t);
        posOrder.push(t);
      }
    });
  });
  const posY0 = -((posOrder.length - 1) * POS_ROW_H) / 2 + rootY;
  const posIdOf = (name: string) => `pos-${posOrder.indexOf(name)}`;
  posOrder.forEach((name, i) => {
    nodes.push({
      id: posIdOf(name),
      type: "position",
      position: { x: COL_POS, y: posY0 + i * POS_ROW_H },
      data: { name } satisfies PosData,
    });
  });

  // 路线节点 + 边
  paths.forEach((p: CareerPath, i: number) => {
    const pathId = `path-${i}`;
    const color = probColor(p.success_probability);
    nodes.push({
      id: pathId,
      type: "path",
      position: { x: COL_PATH, y: i * ROW_H },
      data: {
        name: p.name,
        oneLiner: p.one_liner,
        prob: p.success_probability,
        months: p.expected_months,
        salaryBand: p.expected_salary_band,
      } satisfies PathData,
    });

    // 根 -> 路线
    edges.push({
      id: `e-root-${pathId}`,
      source: "root",
      target: pathId,
      animated: true,
      style: { stroke: color, strokeWidth: 2 },
      markerEnd: { type: MarkerType.ArrowClosed, color },
    });

    // 路线 -> 对标岗位
    p.target_positions.forEach((t) => {
      edges.push({
        id: `e-${pathId}-${posIdOf(t)}`,
        source: pathId,
        target: posIdOf(t),
        style: { stroke: "#a3a3a3", strokeWidth: 1.5 },
        markerEnd: { type: MarkerType.ArrowClosed, color: "#a3a3a3" },
      });
    });
  });

  return { nodes, edges };
}

export default function CareerGraph({ report }: { report: CareerReport }) {
  const { nodes, edges } = useMemo(() => buildGraph(report), [report]);

  return (
    <div className="h-[560px] w-full overflow-hidden rounded-lg border border-neutral-200 bg-white">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.15 }}
        proOptions={{ hideAttribution: true }}
        nodesDraggable
        nodesConnectable={false}
        elementsSelectable={false}
      >
        <Background color="#e5e5e5" gap={20} />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}

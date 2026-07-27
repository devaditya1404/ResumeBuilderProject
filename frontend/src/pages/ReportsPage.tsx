import React from 'react';
import { BarChart3, PieChart, Users, Award, Briefcase, TrendingUp } from 'lucide-react';
import { AppReportStats } from '../types';

interface ReportsPageProps {
  stats: AppReportStats;
}

export const ReportsPage: React.FC<ReportsPageProps> = ({ stats }) => {
  return (
    <div className="space-y-6 pb-12">
      {/* Header Banner */}
      <div className="bg-white rounded-xl border border-slate-200/90 p-6 shadow-2xs space-y-1">
        <h2 className="text-xl font-extrabold text-slate-900 flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-indigo-600" />
          Talent Pool Analytics & Recruitment Reports
        </h2>
        <p className="text-xs text-slate-500">
          Local database reporting on candidate distributions, top skill clusters, and matching performance.
        </p>
      </div>

      {/* Top Key Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-2xs space-y-1">
          <span className="text-[10px] uppercase font-bold text-slate-400">Total Talent Pool</span>
          <p className="text-2xl font-black text-slate-900">{stats.totalCandidates} Candidates</p>
          <span className="text-[10px] font-semibold text-emerald-600 flex items-center gap-1">
            <TrendingUp className="w-3 h-3" /> +24 new this week
          </span>
        </div>

        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-2xs space-y-1">
          <span className="text-[10px] uppercase font-bold text-slate-400">Active Openings</span>
          <p className="text-2xl font-black text-indigo-600">{stats.activeRequirements} Job Criteria</p>
          <span className="text-[10px] text-slate-500 font-medium">Mapped to requirements</span>
        </div>

        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-2xs space-y-1">
          <span className="text-[10px] uppercase font-bold text-slate-400">Avg Candidate Score</span>
          <p className="text-2xl font-black text-purple-600">{stats.avgMatchScore}%</p>
          <span className="text-[10px] text-slate-500 font-medium">Deterministic score avg</span>
        </div>

        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-2xs space-y-1">
          <span className="text-[10px] uppercase font-bold text-slate-400">Outreach Conversion</span>
          <p className="text-2xl font-black text-emerald-600">{stats.candidatesContacted} Contacted</p>
          <span className="text-[10px] text-slate-500 font-medium">Logged in timeline</span>
        </div>
      </div>

      {/* Visual Distribution Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Skills Distribution Breakdown */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-2xs space-y-4">
          <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2 border-b border-slate-100 pb-3">
            <PieChart className="w-4 h-4 text-indigo-600" />
            Top Skill Clusters in Database
          </h3>

          <div className="space-y-3">
            {stats.skillsDistribution.map((item, idx) => {
              const pct = Math.round((item.count / stats.totalCandidates) * 100);
              return (
                <div key={idx} className="space-y-1 text-xs">
                  <div className="flex justify-between font-semibold">
                    <span className="text-slate-800">{item.name}</span>
                    <span className="text-indigo-600">{item.count} Candidates ({pct}%)</span>
                  </div>
                  <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                    <div
                      className="bg-indigo-600 h-full rounded-full"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Experience Distribution Breakdown */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-2xs space-y-4">
          <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2 border-b border-slate-100 pb-3">
            <Award className="w-4 h-4 text-purple-600" />
            Experience Tenure Distribution
          </h3>

          <div className="space-y-3">
            {stats.experienceDistribution.map((item, idx) => {
              const pct = Math.round((item.count / stats.totalCandidates) * 100);
              return (
                <div key={idx} className="space-y-1 text-xs">
                  <div className="flex justify-between font-semibold">
                    <span className="text-slate-800">{item.range}</span>
                    <span className="text-purple-600">{item.count} Candidates ({pct}%)</span>
                  </div>
                  <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                    <div
                      className="bg-purple-600 h-full rounded-full"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

      </div>

      {/* Weekly Upload Activity Chart */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-2xs space-y-4">
        <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2 border-b border-slate-100 pb-3">
          <TrendingUp className="w-4 h-4 text-emerald-600" />
          Weekly Resume Upload Volume
        </h3>

        <div className="grid grid-cols-7 gap-2 text-center items-end h-36 pt-4">
          {stats.uploadActivity.map((day, idx) => (
            <div key={idx} className="flex flex-col items-center gap-2 h-full justify-end">
              <span className="text-[10px] font-bold text-indigo-600">{day.uploads}</span>
              <div
                className="w-full max-w-[32px] bg-gradient-to-t from-indigo-600 to-purple-500 rounded-t-lg transition-all"
                style={{ height: `${day.uploads * 10}px` }}
              />
              <span className="text-[10px] font-bold text-slate-400 uppercase">{day.date}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

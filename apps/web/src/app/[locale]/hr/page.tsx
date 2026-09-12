"use client";

import { useState, useEffect } from "react";
import AppLayout from "@/components/AppLayout";
import { getEmployees, Employee } from "@/lib/api";

export default function HRWorkspace() {
  const [employees, setEmployees] = useState<Employee[]>([]);

  useEffect(() => {
    getEmployees().then(setEmployees).catch(console.error);
  }, []);

  return (
    <AppLayout title="Workforce Management" subtitle="Manage employees and timesheets.">
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        <div className="p-6 border-b border-slate-800 flex justify-between items-center bg-slate-900/50">
          <h2 className="text-lg font-bold text-white">Employee Directory</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-400">
            <thead className="bg-slate-950/50 text-xs uppercase font-semibold text-slate-500 border-b border-slate-800">
              <tr>
                <th className="px-6 py-4">Name</th>
                <th className="px-6 py-4">Email</th>
                <th className="px-6 py-4">Base Rate</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {employees.map((emp) => (
                <tr key={emp.id} className="hover:bg-slate-800/50 transition-colors group">
                  <td className="px-6 py-4 text-white font-medium">{emp.first_name} {emp.last_name}</td>
                  <td className="px-6 py-4">{emp.email}</td>
                  <td className="px-6 py-4">${emp.base_hourly_rate}/hr</td>
                </tr>
              ))}
              {employees.length === 0 && (
                <tr>
                  <td colSpan={3} className="px-6 py-8 text-center text-slate-500">No employees found</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </AppLayout>
  );
}

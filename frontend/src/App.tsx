import { Route, Routes } from "react-router-dom";

function InvestigationShell() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <aside className="fixed inset-y-0 left-0 flex w-60 flex-col bg-slate-900 px-6 py-8 text-white">
        <div>
          <p className="text-xl font-bold tracking-wide">ANVESHAK</p>
          <span className="mt-2 inline-block rounded bg-slate-800 px-2 py-1 text-xs text-slate-300">
            SIH26183
          </span>
        </div>
        <p className="mt-auto text-xs text-slate-400">v1.0.0-mvp · TRON Mainnet</p>
      </aside>
      <main className="ml-60 p-6">
        <header className="rounded-lg border border-slate-200 bg-white p-8 shadow-sm">
          <p className="text-sm font-medium uppercase tracking-widest text-blue-700">
            Team PHANTOMS
          </p>
          <h1 className="mt-3 text-3xl font-bold">Investigation Dashboard</h1>
          <p className="mt-3 max-w-2xl text-slate-600">
            Complaint-to-Action Crypto Investigation Workflow for Indian Law
            Enforcement.
          </p>
        </header>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<InvestigationShell />} />
    </Routes>
  );
}

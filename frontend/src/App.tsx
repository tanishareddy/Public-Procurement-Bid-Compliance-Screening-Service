import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, FileSearch, Activity, Database, AlertTriangle, 
  CheckCircle, XCircle, HelpCircle, ArrowRight, RefreshCw, Send, ThumbsUp, ThumbsDown
} from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'new_screening' | 'result' | 'trace' | 'corpus'>('dashboard');
  const [dashboardSummary, setDashboardSummary] = useState<any>(null);
  const [currentRunId, setCurrentRunId] = useState<string | null>(null);
  const [currentResult, setCurrentResult] = useState<any>(null);
  const [currentTrace, setCurrentTrace] = useState<any>(null);
  const [corpusData, setCorpusData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState<boolean>(false);

  // Form state for New Screening
  const [formData, setFormData] = useState({
    tender_id: "NICSI/PROC/2023/IT-INFRA-8921",
    bidder_name: "TechNova Autonomous Systems Pvt Ltd",
    bidder_category: "startup",
    annual_turnover_inr: 12000000,
    prior_experience_years: 1,
    emd_amount_inr: 0,
    emd_paid: false,
    emd_exemption_claimed: true,
    dpiit_recognition_number: "DPIIT-ST-2023-9988",
    udyam_registration_number: "",
    is_consortium: false,
    additional_remarks: "Claiming startup relaxation under DoE OM 2016 and GFR 173(i)."
  });

  const fetchDashboard = async () => {
    try {
      const res = await fetch('/api/v1/dashboard/summary');
      if (res.ok) {
        const data = await res.json();
        setDashboardSummary(data);
      }
    } catch (e) {
      console.error("Dashboard fetch error:", e);
    }
  };

  const fetchCorpus = async () => {
    try {
      const res = await fetch('/api/v1/corpus');
      if (res.ok) {
        const data = await res.json();
        setCorpusData(data);
      }
    } catch (e) {
      console.error("Corpus fetch error:", e);
    }
  };

  useEffect(() => {
    fetchDashboard();
    fetchCorpus();
  }, []);

  const handleScreeningSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setFeedbackSubmitted(false);

    const payload = {
      ...formData,
      annual_turnover_inr: Number(formData.annual_turnover_inr),
      prior_experience_years: Number(formData.prior_experience_years),
      emd_amount_inr: Number(formData.emd_amount_inr),
      supporting_documents: formData.bidder_category === 'startup' ? [
        {
          document_name: "DPIIT Recognition Certificate",
          document_type: "startup",
          reference_number: formData.dpiit_recognition_number
        }
      ] : []
    };

    try {
      const res = await fetch('/api/v1/bids', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (res.ok) {
        setCurrentRunId(data.run_id);
        pollResult(data.run_id);
      } else {
        alert(`Validation Rejected: ${JSON.stringify(data.detail)}`);
        setLoading(false);
      }
    } catch (err) {
      alert("Submission error: " + err);
      setLoading(false);
    }
  };

  const pollResult = async (runId: string) => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/api/v1/runs/${runId}`);
        if (res.status === 200) {
          clearInterval(interval);
          const data = await res.json();
          setCurrentResult(data);
          
          // Fetch trace
          const traceRes = await fetch(`/api/v1/runs/${runId}/trace`);
          if (traceRes.ok) {
            const traceData = await traceRes.json();
            setCurrentTrace(traceData);
          }
          
          setLoading(false);
          setActiveTab('result');
          fetchDashboard();
        }
      } catch (e) {
        console.error("Polling error:", e);
      }
    }, 600);
  };

  const submitFeedback = async (satisfactory: boolean, rating: number) => {
    if (!currentRunId) return;
    try {
      await fetch('/api/v1/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          run_id: currentRunId,
          satisfactory,
          rating,
          reason: satisfactory ? "Correct identification of policy conflict" : "Review needed"
        })
      });
      setFeedbackSubmitted(true);
    } catch (e) {
      console.error("Feedback submit error:", e);
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-slate-900 border-b border-slate-800 text-white px-6 py-4 flex items-center justify-between shadow-md">
        <div className="flex items-center space-x-3">
          <ShieldCheck className="h-8 w-8 text-blue-400" />
          <div>
            <h1 className="text-xl font-bold tracking-tight">BidShield Procurement Screening</h1>
            <p className="text-xs text-slate-400">Government Bid Mandatory Compliance & Statutory Override Verification Service</p>
          </div>
        </div>
        <div className="flex items-center space-x-2 text-xs">
          <span className="px-2.5 py-1 rounded bg-blue-950 text-blue-300 border border-blue-800 font-mono">NICSI/PROC/2023</span>
          <span className="px-2.5 py-1 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 font-mono">DoE OM 2016 Verified</span>
        </div>
      </header>

      {/* Navigation Bar */}
      <nav className="bg-white border-b border-slate-200 px-6 flex space-x-8 text-sm font-medium">
        <button 
          onClick={() => setActiveTab('dashboard')}
          className={`py-3.5 border-b-2 flex items-center space-x-2 ${activeTab === 'dashboard' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-600 hover:text-slate-900'}`}
        >
          <Activity className="h-4 w-4" />
          <span>Screening Dashboard</span>
        </button>
        <button 
          onClick={() => setActiveTab('new_screening')}
          className={`py-3.5 border-b-2 flex items-center space-x-2 ${activeTab === 'new_screening' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-600 hover:text-slate-900'}`}
        >
          <Send className="h-4 w-4" />
          <span>New Bid Screening</span>
        </button>
        {currentResult && (
          <button 
            onClick={() => setActiveTab('result')}
            className={`py-3.5 border-b-2 flex items-center space-x-2 ${activeTab === 'result' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-600 hover:text-slate-900'}`}
          >
            <FileSearch className="h-4 w-4" />
            <span>Screening Findings</span>
          </button>
        )}
        {currentTrace && (
          <button 
            onClick={() => setActiveTab('trace')}
            className={`py-3.5 border-b-2 flex items-center space-x-2 ${activeTab === 'trace' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-600 hover:text-slate-900'}`}
          >
            <Activity className="h-4 w-4" />
            <span>Multi-Agent Trace</span>
          </button>
        )}
        <button 
          onClick={() => setActiveTab('corpus')}
          className={`py-3.5 border-b-2 flex items-center space-x-2 ${activeTab === 'corpus' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-600 hover:text-slate-900'}`}
        >
          <Database className="h-4 w-4" />
          <span>Corpus & Knowledge Base</span>
        </button>
      </nav>

      {/* Main Container */}
      <main className="flex-1 p-6 max-w-7xl mx-auto w-full">
        {/* DASHBOARD TAB */}
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Screenings</span>
                <p className="text-3xl font-extrabold text-slate-900 mt-2">{dashboardSummary?.total_runs || 0}</p>
                <span className="text-xs text-slate-400 mt-1 block">Indexed tenders & bids</span>
              </div>
              <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm">
                <span className="text-xs font-semibold text-amber-600 uppercase tracking-wider">Committee Escalations</span>
                <p className="text-3xl font-extrabold text-amber-600 mt-2">{dashboardSummary?.escalated_runs || 0}</p>
                <span className="text-xs text-amber-600/80 mt-1 block">Statutory policy conflicts</span>
              </div>
              <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm">
                <span className="text-xs font-semibold text-emerald-600 uppercase tracking-wider">Recommended to Pass</span>
                <p className="text-3xl font-extrabold text-emerald-600 mt-2">{dashboardSummary?.passed_runs || 0}</p>
                <span className="text-xs text-slate-400 mt-1 block">Compliant mandatory criteria</span>
              </div>
              <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm">
                <span className="text-xs font-semibold text-rose-600 uppercase tracking-wider">Disqualification Cites</span>
                <p className="text-3xl font-extrabold text-rose-600 mt-2">{dashboardSummary?.rejected_runs || 0}</p>
                <span className="text-xs text-slate-400 mt-1 block">Unmet mandatory criteria</span>
              </div>
            </div>

            {/* Quick action hero */}
            <div className="bg-gradient-to-r from-slate-900 to-blue-950 rounded-xl p-6 text-white shadow-md flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold">Section 4.1 Difficult Case Demonstration</h2>
                <p className="text-slate-300 text-sm mt-1 max-w-2xl">
                  Test the critical startup relaxation conflict: A DPIIT-recognized startup bids with turnover below the tender threshold.
                  BidShield detects the policy conflict and mandates Tender Committee escalation with dual citations.
                </p>
              </div>
              <button 
                onClick={() => {
                  setFormData({
                    tender_id: "NICSI/PROC/2023/IT-INFRA-8921",
                    bidder_name: "Novatech Innovations Pvt Ltd",
                    bidder_category: "startup",
                    annual_turnover_inr: 12000000,
                    prior_experience_years: 1,
                    emd_amount_inr: 0,
                    emd_paid: false,
                    emd_exemption_claimed: true,
                    dpiit_recognition_number: "DPIIT-ST-2023-7766",
                    udyam_registration_number: "",
                    is_consortium: false,
                    additional_remarks: "DPIIT Startup applying under DoE OM 2016"
                  });
                  setActiveTab('new_screening');
                }}
                className="bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold px-4 py-2.5 rounded-lg transition-colors flex items-center space-x-2"
              >
                <span>Load Startup Test</span>
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>

            {/* Recent Screening Activity */}
            <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
                <h3 className="font-semibold text-slate-800 text-sm">Recent Screening Operations</h3>
                <button onClick={fetchDashboard} className="text-slate-500 hover:text-slate-800 text-xs flex items-center space-x-1">
                  <RefreshCw className="h-3 w-3" />
                  <span>Refresh</span>
                </button>
              </div>
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase tracking-wider font-semibold">
                  <tr>
                    <th className="px-6 py-3">Bidder Name</th>
                    <th className="px-6 py-3">Established Category</th>
                    <th className="px-6 py-3">Routing Recommendation</th>
                    <th className="px-6 py-3">Duration</th>
                    <th className="px-6 py-3">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {dashboardSummary?.recent_activity?.map((r: any) => (
                    <tr key={r.run_id} className="hover:bg-slate-50">
                      <td className="px-6 py-3.5 font-medium text-slate-900">{r.bidder_name}</td>
                      <td className="px-6 py-3.5 uppercase">{r.category}</td>
                      <td className="px-6 py-3.5">
                        <span className={`px-2 py-0.5 rounded font-mono text-[11px] ${
                          r.routing === 'escalate-to-committee' ? 'bg-amber-100 text-amber-800 font-semibold' :
                          r.routing === 'pass-to-technical-evaluation' ? 'bg-emerald-100 text-emerald-800' :
                          'bg-rose-100 text-rose-800'
                        }`}>
                          {r.routing}
                        </span>
                      </td>
                      <td className="px-6 py-3.5 text-slate-500">{r.duration}s</td>
                      <td className="px-6 py-3.5">
                        <button 
                          onClick={() => {
                            setCurrentRunId(r.run_id);
                            pollResult(r.run_id);
                          }}
                          className="text-blue-600 hover:underline"
                        >
                          View Details
                        </button>
                      </td>
                    </tr>
                  ))}
                  {(!dashboardSummary?.recent_activity || dashboardSummary?.recent_activity.length === 0) && (
                    <tr>
                      <td colSpan={5} className="px-6 py-8 text-center text-slate-400">
                        No screening runs yet. Launch a new bid screening to see live telemetry.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* NEW BID SCREENING FORM */}
        {activeTab === 'new_screening' && (
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-8 max-w-3xl mx-auto">
            <h2 className="text-xl font-bold text-slate-900">Submit Bid Summary for Mandatory Screening</h2>
            <p className="text-xs text-slate-500 mt-1 mb-6">
              Ingestion boundary validation will enforce categorical, numeric range, and cross-field constraints before dispatching to agents.
            </p>

            <form onSubmit={handleScreeningSubmit} className="space-y-5">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Tender Identifier</label>
                  <input 
                    type="text" 
                    value={formData.tender_id}
                    onChange={(e) => setFormData({...formData, tender_id: e.target.value})}
                    className="w-full text-xs border border-slate-300 rounded px-3 py-2 bg-slate-50 font-mono"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Bidder Legal Name</label>
                  <input 
                    type="text" 
                    value={formData.bidder_name}
                    onChange={(e) => setFormData({...formData, bidder_name: e.target.value})}
                    className="w-full text-xs border border-slate-300 rounded px-3 py-2"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Claimed Category</label>
                  <select 
                    value={formData.bidder_category}
                    onChange={(e) => setFormData({...formData, bidder_category: e.target.value})}
                    className="w-full text-xs border border-slate-300 rounded px-3 py-2"
                  >
                    <option value="startup">Recognized Startup</option>
                    <option value="mse">Micro or Small Enterprise (MSE)</option>
                    <option value="large_enterprise">Large Enterprise</option>
                    <option value="consortium">Consortium / Joint Venture</option>
                    <option value="foreign">Foreign Bidder</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Average Annual Turnover (INR)</label>
                  <input 
                    type="number" 
                    value={formData.annual_turnover_inr}
                    onChange={(e) => setFormData({...formData, annual_turnover_inr: Number(e.target.value)})}
                    className="w-full text-xs border border-slate-300 rounded px-3 py-2"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Prior Experience (Years)</label>
                  <input 
                    type="number" 
                    value={formData.prior_experience_years}
                    onChange={(e) => setFormData({...formData, prior_experience_years: Number(e.target.value)})}
                    className="w-full text-xs border border-slate-300 rounded px-3 py-2"
                    required
                  />
                </div>
              </div>

              {formData.bidder_category === 'startup' && (
                <div className="bg-amber-50 border border-amber-200 rounded p-4 text-xs">
                  <label className="block font-semibold text-amber-900 mb-1">DPIIT Recognition Number</label>
                  <input 
                    type="text" 
                    value={formData.dpiit_recognition_number}
                    onChange={(e) => setFormData({...formData, dpiit_recognition_number: e.target.value})}
                    placeholder="e.g. DPIIT-ST-12345"
                    className="w-full border border-amber-300 rounded px-3 py-2 bg-white font-mono"
                    required
                  />
                  <p className="text-[11px] text-amber-700 mt-1">Rule F3: Startup recognition certificates are verified strictly and never inferred from free-text claims.</p>
                </div>
              )}

              <div className="border-t border-slate-200 pt-4 grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">EMD Deposit (INR)</label>
                  <input 
                    type="number" 
                    value={formData.emd_amount_inr}
                    onChange={(e) => setFormData({...formData, emd_amount_inr: Number(e.target.value)})}
                    className="w-full text-xs border border-slate-300 rounded px-3 py-2"
                  />
                </div>
                <div className="flex items-center space-x-2 pt-6">
                  <input 
                    type="checkbox" 
                    id="emd_paid"
                    checked={formData.emd_paid}
                    onChange={(e) => setFormData({...formData, emd_paid: e.target.checked})}
                    className="rounded text-blue-600"
                  />
                  <label htmlFor="emd_paid" className="text-xs text-slate-700 font-medium">EMD Paid</label>
                </div>
                <div className="flex items-center space-x-2 pt-6">
                  <input 
                    type="checkbox" 
                    id="emd_exempt"
                    checked={formData.emd_exemption_claimed}
                    onChange={(e) => setFormData({...formData, emd_exemption_claimed: e.target.checked})}
                    className="rounded text-blue-600"
                  />
                  <label htmlFor="emd_exempt" className="text-xs text-slate-700 font-medium">EMD Exemption Claimed</label>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Additional Bidder Remarks & Claims</label>
                <textarea 
                  rows={2}
                  value={formData.additional_remarks}
                  onChange={(e) => setFormData({...formData, additional_remarks: e.target.value})}
                  className="w-full text-xs border border-slate-300 rounded px-3 py-2"
                />
              </div>

              <div className="flex justify-end pt-4">
                <button 
                  type="submit" 
                  disabled={loading}
                  className="bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs px-6 py-2.5 rounded-lg transition-colors flex items-center space-x-2 shadow-sm disabled:opacity-50"
                >
                  {loading && <RefreshCw className="h-4 w-4 animate-spin" />}
                  <span>{loading ? "Screening in Progress..." : "Dispatch Multi-Agent Screening"}</span>
                </button>
              </div>
            </form>
          </div>
        )}

        {/* SCREENING RESULT TAB */}
        {activeTab === 'result' && currentResult && (
          <div className="space-y-6">
            {/* Header Outcome Banner */}
            <div className={`p-6 rounded-xl border shadow-sm ${
              currentResult.routing_recommendation === 'escalate-to-committee' 
                ? 'bg-amber-50 border-amber-300 text-amber-950'
                : currentResult.routing_recommendation === 'pass-to-technical-evaluation'
                ? 'bg-emerald-50 border-emerald-300 text-emerald-950'
                : 'bg-rose-50 border-rose-300 text-rose-950'
            }`}>
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-xs uppercase font-extrabold tracking-wider opacity-75">Screening Recommendation</span>
                  <h2 className="text-2xl font-black mt-1 uppercase font-mono">{currentResult.routing_recommendation}</h2>
                  <p className="text-xs mt-2 font-medium leading-relaxed max-w-4xl">{currentResult.screening_summary}</p>
                </div>
                <div className="text-right text-xs">
                  <span className="font-mono bg-white/70 px-2.5 py-1 rounded border">Run: {currentResult.run_id.slice(0, 8)}</span>
                  <p className="mt-1 opacity-70">Duration: {currentResult.execution_time_seconds}s</p>
                </div>
              </div>
            </div>

            {/* Condition Findings Table */}
            <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-200">
                <h3 className="font-semibold text-slate-800 text-sm">Mandatory Eligibility Criteria Findings</h3>
              </div>
              <div className="divide-y divide-slate-100">
                {currentResult.condition_findings?.map((f: any, idx: number) => (
                  <div key={idx} className="p-6 flex items-start space-x-4">
                    {f.status === 'compliant' && <CheckCircle className="h-5 w-5 text-emerald-600 mt-0.5 flex-shrink-0" />}
                    {f.status === 'conflict_requires_committee' && <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5 flex-shrink-0" />}
                    {f.status === 'exempted_by_policy' && <CheckCircle className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />}
                    {f.status === 'non_compliant' && <XCircle className="h-5 w-5 text-rose-600 mt-0.5 flex-shrink-0" />}
                    
                    <div className="flex-1">
                      <div className="flex items-center space-x-3">
                        <h4 className="font-bold text-slate-900 text-sm">{f.condition_name}</h4>
                        <span className="text-[11px] font-mono px-2 py-0.5 bg-slate-100 text-slate-600 rounded">
                          {f.tender_clause || "Tender Clause"}
                        </span>
                        <span className={`text-[11px] font-mono px-2 py-0.5 rounded uppercase font-semibold ${
                          f.status === 'compliant' ? 'bg-emerald-100 text-emerald-800' :
                          f.status === 'conflict_requires_committee' ? 'bg-amber-100 text-amber-800' :
                          f.status === 'exempted_by_policy' ? 'bg-blue-100 text-blue-800' :
                          'bg-rose-100 text-rose-800'
                        }`}>
                          {f.status.replace(/_/g, ' ')}
                        </span>
                      </div>
                      <p className="text-xs text-slate-600 mt-2 leading-relaxed">{f.details}</p>

                      {/* Supporting Dual Citations */}
                      <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                        {f.tender_citation && (
                          <div className="bg-slate-50 border border-slate-200 rounded p-3">
                            <span className="font-semibold text-slate-700 block text-[11px]">Tender Clause Reference:</span>
                            <p className="font-mono text-slate-800 font-bold mt-0.5">{f.tender_citation.clause_number}</p>
                            <p className="italic text-slate-600 mt-1">"{f.tender_citation.quoted_text}"</p>
                          </div>
                        )}
                        {f.policy_citation && (
                          <div className="bg-amber-50/70 border border-amber-200 rounded p-3">
                            <span className="font-semibold text-amber-900 block text-[11px]">Statutory Policy Override:</span>
                            <p className="font-mono text-amber-900 font-bold mt-0.5">{f.policy_citation.clause_number}</p>
                            <p className="italic text-amber-800 mt-1">"{f.policy_citation.quoted_text}"</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* User Feedback Widget */}
            <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-5 flex items-center justify-between">
              <div>
                <h4 className="text-xs font-semibold text-slate-800">Tender Committee Feedback</h4>
                <p className="text-[11px] text-slate-500">Rate the accuracy and grounding of this automated screening recommendation.</p>
              </div>
              {feedbackSubmitted ? (
                <span className="text-xs text-emerald-600 font-semibold">Thank you! Feedback recorded.</span>
              ) : (
                <div className="flex items-center space-x-2">
                  <button 
                    onClick={() => submitFeedback(true, 5)}
                    className="px-3 py-1.5 border border-slate-200 hover:bg-emerald-50 text-slate-700 hover:text-emerald-700 rounded text-xs flex items-center space-x-1"
                  >
                    <ThumbsUp className="h-3 w-3" />
                    <span>Satisfactory</span>
                  </button>
                  <button 
                    onClick={() => submitFeedback(false, 2)}
                    className="px-3 py-1.5 border border-slate-200 hover:bg-rose-50 text-slate-700 hover:text-rose-700 rounded text-xs flex items-center space-x-1"
                  >
                    <ThumbsDown className="h-3 w-3" />
                    <span>Unsatisfactory</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* MULTI-AGENT TRACE TAB */}
        {activeTab === 'trace' && currentTrace && (
          <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-6 space-y-4">
            <div className="flex items-center justify-between border-b pb-4">
              <div>
                <h3 className="font-bold text-slate-900 text-sm">Execution Reconstructibility & Trace Log</h3>
                <p className="text-xs text-slate-500">Correlation ID: {currentTrace.run_id}</p>
              </div>
              <div className="text-xs text-slate-500 font-mono">
                Tokens: {currentTrace.total_tokens} | Cost: ${currentTrace.total_cost_usd}
              </div>
            </div>

            <div className="space-y-4">
              {currentTrace.steps?.map((s: any, idx: number) => (
                <div key={idx} className="border-l-2 border-blue-500 pl-4 py-1">
                  <div className="flex items-center space-x-2 text-xs">
                    <span className="font-bold text-blue-700 font-mono">Step {s.step_number}</span>
                    <span className="px-2 py-0.5 rounded bg-slate-100 font-semibold">{s.agent_name}</span>
                    <span className="text-slate-400 font-mono">({s.latency_ms} ms)</span>
                  </div>
                  <p className="text-xs font-mono text-slate-700 mt-1">Action: {s.action}</p>
                  <pre className="bg-slate-50 p-2.5 rounded mt-2 text-[11px] font-mono text-slate-600 overflow-x-auto border border-slate-200">
                    {JSON.stringify(s.action_output, null, 2)}
                  </pre>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* CORPUS MANAGEMENT TAB */}
        {activeTab === 'corpus' && (
          <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-6 space-y-6">
            <div className="flex items-center justify-between border-b pb-4">
              <div>
                <h3 className="font-bold text-slate-900 text-sm">Authoritative Legal & Tender Corpus</h3>
                <p className="text-xs text-slate-500">Real, published procurement regulations and closed tender specifications.</p>
              </div>
              <span className="text-xs bg-emerald-100 text-emerald-800 px-2.5 py-1 rounded font-semibold">
                ChromaDB Vector Store Synced
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {corpusData?.documents?.map((d: any, idx: number) => (
                <div key={idx} className="border border-slate-200 rounded-lg p-4 bg-slate-50/50">
                  <h4 className="font-bold text-slate-900 text-xs">{d.document}</h4>
                  <p className="text-[11px] text-slate-500 mt-0.5">Authority: {d.authority}</p>
                  <div className="mt-3 text-[11px] font-mono space-y-1 text-slate-600">
                    <p>Filename: {d.filename}</p>
                    <p>Indexed Chunks: {d.chunks}</p>
                    <p className="truncate">SHA-256: {d.checksum}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

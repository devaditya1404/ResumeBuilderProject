import React from 'react';
import { Mail, Phone, Globe, MapPin, FileText, Calendar, Send, ShieldCheck } from 'lucide-react';
import type { Candidate } from '../../../types';

interface OverviewTabProps {
  candidate: Candidate;
  onAddContactEvent?: (type: string, note: string) => void;
}

export const OverviewTab: React.FC<OverviewTabProps> = ({ candidate, onAddContactEvent }) => {
  const [contactType, setContactType] = React.useState('Phone Call');
  const [contactNote, setContactNote] = React.useState('');

  const handleContactSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!contactNote.trim()) return;
    if (onAddContactEvent) {
      onAddContactEvent(contactType, contactNote);
      setContactNote('');
    }
  };

  return (
    <div className="space-y-6">
      {/* Contact Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center shrink-0">
            <Mail className="w-4 h-4" />
          </div>
          <div className="min-w-0">
            <p className="text-[10px] uppercase font-bold text-slate-400">Email Address</p>
            <p className="text-xs font-semibold text-slate-900 truncate">
              {candidate.email || <span className="text-slate-400 italic">Unspecified in resume</span>}
            </p>
          </div>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center shrink-0">
            <Phone className="w-4 h-4" />
          </div>
          <div className="min-w-0">
            <p className="text-[10px] uppercase font-bold text-slate-400">Phone Number</p>
            <p className="text-xs font-semibold text-slate-900 truncate">
              {candidate.phone || <span className="text-slate-400 italic">Unspecified in resume</span>}
            </p>
          </div>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center shrink-0">
            <Globe className="w-4 h-4" />
          </div>
          <div className="min-w-0">
            <p className="text-[10px] uppercase font-bold text-slate-400">LinkedIn Profile</p>
            {candidate.linkedinUrl ? (
              <a
                href={candidate.linkedinUrl}
                target="_blank"
                rel="noreferrer"
                className="text-xs font-semibold text-indigo-600 hover:underline truncate block"
              >
                {candidate.linkedinUrl.replace('https://', '')}
              </a>
            ) : (
              <p className="text-xs text-slate-400 italic">Unspecified in resume</p>
            )}
          </div>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center shrink-0">
            <MapPin className="w-4 h-4" />
          </div>
          <div className="min-w-0">
            <p className="text-[10px] uppercase font-bold text-slate-400">Location</p>
            <p className="text-xs font-semibold text-slate-900 truncate">
              {candidate.location || <span className="text-slate-400 italic">Unspecified in resume</span>}
            </p>
          </div>
        </div>
      </div>

      {/* AI Professional Summary */}
      <div className="p-4 rounded-xl bg-gradient-to-br from-indigo-900 to-purple-900 text-white shadow-md">
        <div className="flex items-center gap-2 mb-2">
          <ShieldCheck className="w-4 h-4 text-indigo-300" />
          <h4 className="text-xs font-bold uppercase tracking-wider text-indigo-200">Grounded AI Executive Summary</h4>
        </div>
        <p className="text-xs text-indigo-100 leading-relaxed font-normal">
          {candidate.professionalSummary}
        </p>
      </div>

      {/* Resume History */}
      <div className="p-4 rounded-xl bg-white border border-slate-200/80 space-y-3">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
          <FileText className="w-4 h-4 text-indigo-600" />
          Resume Document Version History
        </h4>
        <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs">
          <div className="flex items-center gap-2.5">
            <FileText className="w-4 h-4 text-slate-400" />
            <div>
              <p className="font-semibold text-slate-900">{candidate.name.replace(/\s+/g, '_')}_Resume_v1.pdf</p>
              <p className="text-[10px] text-slate-500">Uploaded {candidate.uploadedAt} • PyMuPDF Parsed</p>
            </div>
          </div>
          <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-emerald-100 text-emerald-700">
            Active Version
          </span>
        </div>
      </div>

      {/* Contact Event Section */}
      <div className="p-4 rounded-xl bg-white border border-slate-200/80 space-y-3">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
          <Calendar className="w-4 h-4 text-indigo-600" />
          Log Recruiter Outreach Event
        </h4>
        
        <form onSubmit={handleContactSubmit} className="space-y-3">
          <div className="grid grid-cols-3 gap-2">
            {['Phone Call', 'Email Sent', 'Interview Scheduled'].map((type) => (
              <button
                type="button"
                key={type}
                onClick={() => setContactType(type)}
                className={`py-1.5 px-2 text-xs font-medium rounded-lg border text-center transition-colors ${
                  contactType === type
                    ? 'bg-indigo-600 text-white border-indigo-600 font-semibold'
                    : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                }`}
              >
                {type}
              </button>
            ))}
          </div>

          <textarea
            rows={2}
            value={contactNote}
            onChange={(e) => setContactNote(e.target.value)}
            placeholder="Log recruiter note or response details..."
            className="w-full text-xs p-3 rounded-lg border border-slate-200 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
          />

          <div className="flex justify-end">
            <button
              type="submit"
              className="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg shadow-xs transition-colors"
            >
              <Send className="w-3.5 h-3.5" />
              Save Outreach Event
            </button>
          </div>
        </form>

        {/* Existing Contact Events */}
        {candidate.contactHistory.length > 0 && (
          <div className="mt-3 pt-3 border-t border-slate-100 space-y-2">
            <p className="text-[10px] uppercase font-bold text-slate-400">Recorded Outreach Log</p>
            {candidate.contactHistory.map((item, idx) => (
              <div key={idx} className="p-2.5 rounded-lg bg-slate-50 border border-slate-100 text-xs flex flex-col gap-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-indigo-700">{item.type}</span>
                  <span className="text-[10px] text-slate-400">{item.date}</span>
                </div>
                <p className="text-slate-700">{item.note}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

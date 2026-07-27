import React from 'react';
import { Upload, RefreshCw, PhoneCall, StickyNote, Sparkles, CheckCircle } from 'lucide-react';
import { TimelineEvent } from '../../../types';

interface TimelineTabProps {
  events: TimelineEvent[];
}

const EVENT_ICONS: Record<TimelineEvent['type'], React.ElementType> = {
  UPLOAD: Upload,
  UPDATE: RefreshCw,
  CONTACTED: PhoneCall,
  NOTE: StickyNote,
  MATCHED: Sparkles
};

export const TimelineTab: React.FC<TimelineTabProps> = ({ events }) => {
  return (
    <div className="space-y-6">
      <div className="p-3.5 rounded-xl bg-white border border-slate-200/80 shadow-2xs">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
          Candidate Audit & Activity Timeline
        </h4>
        <p className="text-[11px] text-slate-400">All local lifecycle events recorded for this candidate profile.</p>
      </div>

      <div className="relative pl-6 space-y-4 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
        {events.map((evt) => {
          const Icon = EVENT_ICONS[evt.type] || CheckCircle;
          return (
            <div key={evt.id} className="relative group">
              <div className="absolute -left-[23px] top-1.5 w-4 h-4 rounded-full bg-indigo-600 text-white flex items-center justify-center shadow-2xs">
                <Icon className="w-2.5 h-2.5" />
              </div>

              <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-2xs space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <h5 className="font-bold text-slate-900">{evt.title}</h5>
                  <span className="text-[10px] text-slate-400 font-medium">{evt.timestamp}</span>
                </div>
                <p className="text-xs text-slate-600">{evt.description}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

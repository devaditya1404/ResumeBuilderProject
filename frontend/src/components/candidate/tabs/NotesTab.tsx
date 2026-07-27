import React, { useState } from 'react';
import { StickyNote, Plus, Clock, User } from 'lucide-react';
import { RecruiterNote } from '../../../types';

interface NotesTabProps {
  candidateId: string;
  notes: RecruiterNote[];
  onAddNote: (content: string) => void;
}

export const NotesTab: React.FC<NotesTabProps> = ({ notes, onAddNote }) => {
  const [newNoteContent, setNewNoteContent] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newNoteContent.trim()) return;
    onAddNote(newNoteContent.trim());
    setNewNoteContent('');
  };

  return (
    <div className="space-y-6">
      {/* Create Note Input */}
      <form onSubmit={handleSubmit} className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-2xs space-y-3">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
          <StickyNote className="w-4 h-4 text-indigo-600" />
          Add Recruiter Private Note
        </h4>

        <textarea
          rows={3}
          value={newNoteContent}
          onChange={(e) => setNewNoteContent(e.target.value)}
          placeholder="e.g. Candidate contacted for PMO opening. Good communication skills, open to relocation..."
          className="w-full text-xs p-3 rounded-lg border border-slate-200 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
        />

        <div className="flex justify-end">
          <button
            type="submit"
            className="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg shadow-xs transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            Save Note Locally
          </button>
        </div>
      </form>

      {/* Recruiter Notes List */}
      <div className="space-y-3">
        <h5 className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
          Saved Notes ({notes.length})
        </h5>

        {notes.length === 0 ? (
          <div className="p-8 text-center bg-slate-50 rounded-xl border border-dashed border-slate-200">
            <StickyNote className="w-8 h-8 text-slate-300 mx-auto mb-2" />
            <p className="text-xs font-semibold text-slate-500">No recruiter notes saved yet.</p>
            <p className="text-[11px] text-slate-400 mt-1">Add notes above to persist local feedback.</p>
          </div>
        ) : (
          notes.map((note) => (
            <div key={note.id} className="p-4 rounded-xl bg-amber-50/70 border border-amber-200/80 shadow-2xs space-y-2">
              <div className="flex items-center justify-between text-[11px] text-amber-800">
                <span className="font-bold flex items-center gap-1">
                  <User className="w-3 h-3 text-amber-700" />
                  {note.author}
                </span>
                <span className="flex items-center gap-1 font-medium text-amber-700">
                  <Clock className="w-3 h-3" />
                  {note.createdAt}
                </span>
              </div>
              <p className="text-xs text-slate-800 leading-relaxed font-normal whitespace-pre-wrap">
                {note.content}
              </p>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

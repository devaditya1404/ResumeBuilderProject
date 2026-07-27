import React, { useState } from 'react';
import { MessageSquareText, Send, Sparkles, User, Bot, Briefcase, ChevronRight } from 'lucide-react';
import { Candidate, ChatMessage } from '../types';

interface AiChatPageProps {
  candidates: Candidate[];
  onSelectCandidate: (cand: Candidate) => void;
}

export const AiChatPage: React.FC<AiChatPageProps> = ({ candidates, onSelectCandidate }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'msg-1',
      sender: 'assistant',
      text: 'Hello Recruiter! I am your local AI Talent Assistant connected directly to your SQLite database & Ollama Qwen model. Ask me anything about candidates, skills, or job matches.',
      timestamp: '10:00 AM'
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  const samplePrompts = [
    'Find Java developers with 5+ years experience.',
    'Show candidates with Power BI and SQL.',
    'Who is best suited for this PMO requirement?',
    'Find candidates who worked in banking.'
  ];

  const handleSend = (textToSend?: string) => {
    const query = textToSend || inputText;
    if (!query.trim()) return;

    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInputText('');
    setIsTyping(true);

    // Simulate local DB + Ollama query response
    setTimeout(() => {
      let matched: Candidate[] = [];
      let responseText = '';

      const q = query.toLowerCase();
      if (q.includes('java') || q.includes('5+')) {
        matched = candidates.filter((c) => c.topSkills.includes('Java') || (c.experienceYears || 0) >= 5);
        responseText = `Found ${matched.length} candidate(s) with Java backend expertise or 5+ years experience in SQLite database:`;
      } else if (q.includes('power bi') || q.includes('pmo')) {
        matched = candidates.filter((c) => c.topSkills.includes('PMO') || c.topSkills.includes('Power BI'));
        responseText = `Here are candidates matching PMO & Power BI analytical reporting:`;
      } else if (q.includes('banking')) {
        matched = candidates.filter((c) => c.professionalSummary.toLowerCase().includes('banking') || c.topSkills.includes('Java'));
        responseText = `Found candidate(s) with confirmed banking domain client history:`;
      } else {
        matched = candidates.slice(0, 2);
        responseText = `Here are the top matching candidate profiles for your query:`;
      }

      const botMsg: ChatMessage = {
        id: `msg-${Date.now() + 1}`,
        sender: 'assistant',
        text: responseText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        matchedCandidates: matched
      };

      setMessages((prev) => [...prev, botMsg]);
      setIsTyping(false);
    }, 1000);
  };

  return (
    <div className="h-[calc(100vh-140px)] flex flex-col bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
      {/* Chat Header */}
      <div className="p-4 bg-slate-900 text-white border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center shadow-xs">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-bold text-sm text-white flex items-center gap-2">
              AI Recruiter Assistant
              <span className="text-[10px] bg-indigo-500/20 text-indigo-300 px-2 py-0.5 rounded border border-indigo-500/30">
                Ollama Qwen • Local DB
              </span>
            </h3>
            <p className="text-[11px] text-slate-400">Natural language search over local candidate profiles</p>
          </div>
        </div>
      </div>

      {/* Suggested Prompts Pill Row */}
      <div className="p-3 bg-slate-50 border-b border-slate-200/80 flex items-center gap-2 overflow-x-auto scrollbar-none">
        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 shrink-0">Try asking:</span>
        {samplePrompts.map((p, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(p)}
            className="px-3 py-1 bg-white hover:bg-indigo-50 text-slate-700 hover:text-indigo-700 font-semibold text-xs rounded-full border border-slate-200 shrink-0 transition-colors shadow-2xs"
          >
            {p}
          </button>
        ))}
      </div>

      {/* Chat Log Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-slate-50/40">
        {messages.map((msg) => {
          const isUser = msg.sender === 'user';
          return (
            <div
              key={msg.id}
              className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : ''}`}
            >
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
                  isUser
                    ? 'bg-indigo-600 text-white'
                    : 'bg-slate-900 text-indigo-400 border border-slate-800'
                }`}
              >
                {isUser ? <User className="w-4 h-4" /> : <Sparkles className="w-4 h-4" />}
              </div>

              <div className={`max-w-xl space-y-2 ${isUser ? 'text-right' : ''}`}>
                <div
                  className={`inline-block p-4 rounded-2xl text-xs leading-relaxed text-left shadow-2xs ${
                    isUser
                      ? 'bg-indigo-600 text-white font-medium rounded-tr-none'
                      : 'bg-white text-slate-800 border border-slate-200 rounded-tl-none'
                  }`}
                >
                  <p>{msg.text}</p>
                </div>

                {/* Inline matched candidate cards if returned by AI */}
                {msg.matchedCandidates && msg.matchedCandidates.length > 0 && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 text-left">
                    {msg.matchedCandidates.map((c) => (
                      <div
                        key={c.id}
                        onClick={() => onSelectCandidate(c)}
                        className="p-3 rounded-xl bg-white border border-slate-200 hover:border-indigo-400 cursor-pointer shadow-2xs hover:shadow-md transition-all group"
                      >
                        <div className="flex items-center justify-between">
                          <h5 className="font-bold text-slate-900 text-xs group-hover:text-indigo-600">{c.name}</h5>
                          <ChevronRight className="w-3.5 h-3.5 text-slate-400 group-hover:translate-x-0.5 transition-transform" />
                        </div>
                        <p className="text-[11px] text-indigo-600 font-semibold mt-0.5">{c.designation}</p>
                        <p className="text-[10px] text-slate-500 mt-1">{c.experienceDisplay} • {c.location}</p>
                      </div>
                    ))}
                  </div>
                )}

                <span className="text-[10px] text-slate-400 block px-1">{msg.timestamp}</span>
              </div>
            </div>
          );
        })}

        {isTyping && (
          <div className="flex items-center gap-2 text-xs text-slate-500 italic">
            <Sparkles className="w-4 h-4 text-indigo-500 animate-spin" />
            Ollama AI querying SQLite talent vault...
          </div>
        )}
      </div>

      {/* Input Box Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="p-4 bg-white border-t border-slate-200 flex items-center gap-3"
      >
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Ask recruiter query (e.g. Find candidates with Power BI and SQL experience)..."
          className="flex-1 text-xs p-3.5 rounded-xl border border-slate-200 focus:ring-2 focus:ring-indigo-500 focus:outline-none font-medium"
        />
        <button
          type="submit"
          disabled={!inputText.trim()}
          className="p-3.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold shadow-md transition-colors disabled:opacity-50"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};

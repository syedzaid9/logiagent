import React, { useState, useEffect } from 'react';
import { api } from '../../api/services';
import { 
  BookOpen, 
  Search, 
  FileText, 
  ShieldCheck, 
  Sparkles, 
  ChevronRight,
  Database,
  RefreshCw
} from 'lucide-react';

export const PolicyExplorer: React.FC = () => {
  const [documents, setDocuments] = useState<any[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState<any | null>(null);

  const loadDocuments = async () => {
    try {
      const docs = await api.getRAGDocuments();
      setDocuments(docs);
      if (docs.length > 0) {
        setSelectedDoc(docs[0]);
      }
    } catch (err) {
      console.error('Error fetching RAG docs:', err);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    try {
      setSearching(true);
      const res = await api.queryRAG(searchQuery);
      setSearchResults(res.chunks || []);
    } catch (err) {
      console.error('Error querying RAG:', err);
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Header */}
      <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-card flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-indigo-600" />
            <span>Logistics Standard Operating Procedures (RAG Knowledge Base)</span>
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Indexed supply chain compliance SOPs, exception handling protocols, and safety regulations.
          </p>
        </div>

        {/* Semantic Vector Search Input */}
        <form onSubmit={handleSearch} className="flex items-center gap-2 w-full md:w-96">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search policy (e.g. failed delivery grace period)..."
              className="w-full pl-9 pr-3 py-2 rounded-xl bg-white border border-slate-300 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 text-xs text-slate-900 placeholder-slate-400 outline-none"
            />
          </div>
          <button
            type="submit"
            disabled={searching}
            className="px-3.5 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-2xs transition-all flex items-center gap-1.5 shrink-0 cursor-pointer disabled:opacity-50"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Search</span>
          </button>
        </form>
      </div>

      {/* Semantic Search Results (if searched) */}
      {searchResults.length > 0 && (
        <div className="p-5 rounded-2xl bg-indigo-50/60 border border-indigo-200 shadow-card space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-indigo-900 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-indigo-600" />
              <span>Semantic Vector Search Results for: "{searchQuery}"</span>
            </h3>
            <button
              onClick={() => setSearchResults([])}
              className="text-[11px] font-semibold text-slate-500 hover:text-slate-800 cursor-pointer"
            >
              Clear Results
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {searchResults.map((chunk, i) => (
              <div key={i} className="p-3.5 rounded-xl bg-white border border-indigo-100 shadow-2xs space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-indigo-800">
                    [{chunk.document_code}] {chunk.title}
                  </span>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 font-mono font-semibold border border-indigo-200">
                    Sim Score: {(chunk.score * 100).toFixed(1)}%
                  </span>
                </div>
                <p className="text-xs text-slate-700 leading-relaxed line-clamp-4 font-mono bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                  {chunk.content}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Document Library Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {documents.map((doc, idx) => (
          <div
            key={idx}
            className="p-5 rounded-2xl bg-white border border-slate-200 hover:border-blue-300 hover:shadow-card-hover transition-all shadow-card space-y-3"
          >
            <div className="flex items-start justify-between">
              <div className="p-2.5 rounded-xl bg-blue-50 border border-blue-100 text-blue-600">
                <FileText className="w-5 h-5" />
              </div>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 font-mono border border-slate-200">
                {doc.category}
              </span>
            </div>

            <div>
              <span className="text-xs font-mono font-bold text-blue-600">{doc.document_code}</span>
              <h4 className="text-sm font-bold text-slate-900 mt-0.5">{doc.title}</h4>
            </div>

            <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
              <span>{doc.total_chunks} Indexed Chunks</span>
              <span className="font-mono text-[11px] text-slate-400">{doc.document_name}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

